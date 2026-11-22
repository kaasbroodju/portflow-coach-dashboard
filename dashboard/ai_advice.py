"""AI-advies bij een evaluatie (spec 040): collect the material of one review request, replace the
names, ask the local model (Ollama) for an advice per skill, check the answer and keep the last one.

Everything stays on the laptop: Portflow is only asked for the evidence (as on the evaluation page),
and the model runs in Ollama on the laptop itself (ollama.py). Labels are Dutch.
"""

import base64
import json
import re
import sqlite3
import threading
from datetime import date, datetime, timezone

from . import claude_ai, db, evaluation_page, evidence, evidence_files, file_text, lef, ollama
from .evidence import plain_text
from .hide_names import anonymize, numbers
from .overview import semester_period
from .portflow_connection import S_USER_NAME
from .progress import name_key
from .skills import NAMES, SKILLS

NUM_CTX = 32768             # tokens the model may use (prompt and answer)
BUDGET_CHARS = 80000        # F8: about 3.5 characters per token, with room for the answer
MAX_IMAGES = 6
MAX_IMAGE_BYTES = 4 * 1024 * 1024

SYSTEM = (
    "Je helpt een coach of gildemeester van de HBO-ICT-opleiding Open-ICT bij het voorbereiden van een beoordeling. "
    "Geef per gevraagde vaardigheid een advies over het niveau: 0 is startniveau, daarna 1 tot en met 4. "
    "De LEF-teksten zijn de maatstaf: een niveau past als het materiaal laat zien wat de LEF-tekst van dat niveau beschrijft. "
    "Baseer je alleen op het aangeleverde materiaal. Verzin niets: noem alleen bewijsstukken, feedback en handelingen die in "
    "het materiaal staan, en noem bewijsstukken bij hun naam. Ontbreekt er bewijs, zeg dat dan. "
    "Schrijf in het Nederlands, kort, ontwikkelingsgericht en niet beoordelend, gericht aan de coach. "
    "Geef bij 'ontbreekt' wat er nog ontbreekt voor het gevraagde niveau of wat de student kan doen om verder te komen. "
    "Het is een advies: de coach of gildemeester beslist."
)


S_PROMPT = "ai_prompt"                  # F18: the general instruction, if the user changed it
SKILL_PROMPT = "ai_prompt_{}"           # F19: an addition per skill
PROMPT_SETTINGS = (S_PROMPT, *(SKILL_PROMPT.format(code) for code in SKILLS))


def system_prompt(database: str) -> str:
    """F18: the user's own general instruction, or the standard one."""
    return (db.get_setting(database, S_PROMPT) or "").strip() or SYSTEM


def skill_prompts(database: str) -> dict[str, str]:
    """F19: per skill the user's addition (only the ones filled in)."""
    result = {}
    for code in SKILLS:
        text = (db.get_setting(database, SKILL_PROMPT.format(code)) or "").strip()
        if text:
            result[code] = text
    return result


def schema(codes: list[str]) -> dict:
    """F5: the fixed answer of the model."""
    return {"type": "object", "required": ["vaardigheden"], "properties": {"vaardigheden": {
        "type": "array", "items": {"type": "object", "required": ["code", "niveau", "onderbouwing", "ontbreekt"],
                                   "additionalProperties": False,
                                  "properties": {"code": {"type": "string", "enum": codes},
                                                  "niveau": {"type": "integer", "enum": [0, 1, 2, 3, 4]},
                                                  "onderbouwing": {"type": "string"},
                                                  "ontbreekt": {"type": "string"}}}}},
            "additionalProperties": False}


SERVICES = {"lokaal": "Lokaal model (Ollama)", "claude": "Claude (Anthropic, via internet)"}


def available(database: str, user_name: str | None = None) -> list[dict]:
    """F14: the services that are set up, for the choice on the evaluation page. Claude only for the
    allowed Portflow user (F22)."""
    result = []
    url, model = settings(database)
    try:
        if ollama.has_model(url, model):
            result.append({"key": "lokaal", "label": f"Lokaal model · {model}", "external": False})
    except ollama.OllamaError:
        pass
    if claude_ai.ready(database) and claude_ai.allowed(user_name):
        result.append({"key": "claude", "label": f"Claude · {claude_ai.MODEL} (via internet)", "external": True})
    return result


def settings(database: str) -> tuple[str, str]:
    """F11: the address of Ollama and the chosen model."""
    return (db.get_setting(database, ollama.S_URL) or ollama.DEFAULT_URL,
            db.get_setting(database, ollama.S_MODEL) or ollama.DEFAULT_MODEL)


# Names (F3) ----------------------------------------------------------------------------------------

def replacements(conn: sqlite3.Connection, student_name: str) -> dict[str, str]:
    """The student -> "Student"; coaches and guild masters -> "Coach 1", "Gildemeester 1"; the user ->
    "de beoordelaar"; other known names (fellow students, authors of feedback) -> "Medestudent N"."""
    names: dict[str, str] = {}
    me = next((r[0] for r in conn.execute("SELECT value FROM settings WHERE key = ?", (S_USER_NAME,)) if r[0]), None)
    if me:
        names[me] = "de beoordelaar"
    if student_name:
        names[student_name] = "Student"
        first = student_name.split()[0]
        if len(first) >= 3:
            names.setdefault(first, "Student")
    counters = {"Coach": 0, "Gildemeester": 0}
    for row in conn.execute("SELECT name, is_coach, is_guild_master FROM staff ORDER BY id"):
        if row["name"] and row["name"] not in names and name_key(row["name"]) != name_key(me):
            label = "Gildemeester" if row["is_guild_master"] and not row["is_coach"] else "Coach"
            counters[label] += 1
            names[row["name"]] = f"{label} {counters[label]}"
    others = 0
    for name in numbers(conn):
        if name not in names:
            others += 1
            names[name] = f"Medestudent {others}"
    return names


# Collecting the material (F2, F7, F8) ------------------------------------------------------------------

def _plain(html_text: str | None) -> str:
    return plain_text(html_text or "")


def _lef_plain(code: str) -> str:
    parts = []
    for level in (1, 2, 3, 4):
        text = lef.level_text(code, level)
        if text:
            parts.append(f"Niveau {level} – {text['title']}:\n" + re.sub(r"\n{2,}", "\n", plain_text(
                text["html"].replace("</li>", "</li>\n").replace("<li>", "- "))))
    return "\n\n".join(parts)


def overview(data: dict) -> dict:
    """F2: what goes to the model, as counts (before asking; the files are read while asking)."""
    skills = data["skills"]
    evidence_ids = {e["id"] for s in skills for e in s["evidence"]}
    files = {e["id"] for s in skills for e in s["evidence"] if e["raw_kind"] == "file"}
    return {"skills": len(skills), "evidence": len(evidence_ids), "files": len(files),
            "earlier": sum(len(s["earlier"]) for s in skills),
            "feedback": sum(1 + t["replies"] for s in skills for t in s["threads"])}


def collect(conn: sqlite3.Connection, database: str, token: str | None, request_id: int, today: date,
            progress=None, *, vision: bool = True, detail=evidence.detail, files=evidence_files) -> dict:
    """Everything about the request as text, names not yet replaced. Returns
    {'codes', 'student', 'sections', 'evidence': [...], 'images': [...], 'counts', 'names_only': [...]}."""
    start, end, _ = semester_period(conn, today)
    data = evaluation_page.build(conn, request_id, today, start, end)
    if data is None or not data["skills"]:
        raise ollama.OllamaError("Van dit verzoek zijn geen vaardigheden bekend; klik eerst op Verversen.")
    r, student_id = data["request"], data["request"]["student_id"]
    note = conn.execute("SELECT note FROM received_requests WHERE review_request_id = ?", (request_id,)).fetchone()
    feedback_text = _feedback_texts(conn, student_id, start, end)
    extra = skill_prompts(database)   # F19

    head = [f'Evaluatieverzoek "{r["title"]}" van {r["student"]}, ingediend {r["submitted"]}.']
    if note and _plain(note["note"]):
        head.append("Toelichting van de student:\n" + _plain(note["note"]))
    sections, contents, images, names_only = [], [], [], []
    all_evidence = {}
    for s in data["skills"]:
        lines = [f"## Vaardigheid {s['code']} ({s['name']})",
                 f"Beoordeeld door: {s['assessor']}. Hoogste behaalde niveau tot nu toe: "
                 f"{s['current'] if s['current'] is not None else 'nog geen'}. De student vraagt niveau: "
                 f"{s['claimed'] if s['claimed'] is not None else 'niet aangegeven'}.",
                 "Zelfevaluatie van de student:\n" + (_plain(s["self_text"]) or "(geen tekst)"),
                 "LEF-teksten (de maatstaf):\n" + _lef_plain(s["code"])]
        if s["code"] in extra:
            lines.append(f"Waar de beoordelaar bij {s['code']} in het bijzonder op wil letten:\n{extra[s['code']]}")
        if s["earlier"]:
            lines.append("Eerdere beoordelingen:\n" + "\n".join(
                f"- niveau {e['level']} op {e['date']} door {e['author']} ({e['role']}): {_plain(e['text']) or '(geen tekst)'}"
                for e in s["earlier"]))
        else:
            lines.append("Eerdere beoordelingen: geen.")
        if s["evidence"]:
            lines.append("Bewijsstukken bij deze vaardigheid (nieuwste eerst; de inhoud staat verderop):\n" + "\n".join(
                f"- {e['name']} ({e['kind']}, toegevoegd {e['created']})" for e in s["evidence"]))
        else:
            lines.append("Bewijsstukken bij deze vaardigheid: geen.")
        threads = [feedback_text[t["id"]] for t in s["threads"] if t["id"] in feedback_text]
        if threads:
            lines.append("Feedbackvragen en reacties op deze bewijsstukken:\n" + "\n".join(threads))
        sections.append("\n\n".join(lines))
        for e in s["evidence"]:
            all_evidence.setdefault(e["id"], dict(e, skills=[]))["skills"].append(s["code"])

    # F7: the contents of the evidence, newest first per skill (F8 trims them later).
    total = len(all_evidence)
    for number, (evidence_id, e) in enumerate(all_evidence.items(), start=1):
        if progress:
            progress(f"Bewijsstukken lezen ({number} van {total})")
        details, _ = detail(conn, student_id, evidence_id, token)
        if not details:
            names_only.append(e["name"])
            continue
        if details.get("text"):
            contents.append({"name": e["name"], "skills": e["skills"], "text": _plain(details["text"])})
            continue
        texts = []
        for f in details.get("files") or []:
            kind = f["display"]
            try:
                if kind == "image" and vision and len(images) < MAX_IMAGES:
                    path, mime = files.shown_file(database, conn, token, student_id, details["portfolio_id"], f["id"])
                    data_bytes = path.read_bytes()
                    if len(data_bytes) <= MAX_IMAGE_BYTES and mime in ("image/png", "image/jpeg", "image/gif", "image/webp"):
                        images.append({"name": f"{e['name']} – {f['name']}", "mime": mime,
                                       "data": base64.b64encode(data_bytes).decode()})
                        texts.append(f"[afbeelding {f['name']}: meegestuurd als afbeelding {len(images)}]")
                        continue
                elif file_text.readable(f["mime"]):
                    raw = files.original_bytes(conn, token, student_id, details["portfolio_id"], f["id"])
                    text = file_text.text_of(raw, f["mime"])
                    if text:
                        texts.append(f"[bestand {f['name']}]\n{text}")
                        continue
            except evidence_files.FileError:
                pass
            texts.append(f"[bestand {f['name']}: inhoud niet gelezen]")
            names_only.append(f"{e['name']} – {f['name']}")
        if details.get("url"):
            texts.append(f"[link naar {details['url']}]")
        contents.append({"name": e["name"], "skills": e["skills"], "text": "\n".join(texts) or "(geen inhoud)"})

    counts = overview(data)
    return {"codes": data["codes"], "student": r["student"], "head": "\n".join(head), "sections": sections,
            "contents": contents, "images": images, "names_only": names_only, "counts": counts}


def _feedback_texts(conn, student_id: int, start: date, end: date) -> dict[int, str]:
    from .feedback import _requests
    result = {}
    names = {r["evidence_id"]: r["name"] for r in conn.execute(
        "SELECT evidence_id, name FROM evidence_items WHERE student_id = ?", (student_id,))}
    for request in _requests(conn, student_id, start, end):
        lines = [f"- Feedbackvraag bij {names.get(request['evidence_id'], 'een bewijsstuk')} van {request['author_name']}: "
                 f"{plain_text(request['text'])}"]
        lines += [f"  - Reactie van {reply['author_name']} ({reply['role']}): {plain_text(reply['text'])}"
                  for reply in request["replies"]]
        result[request["comment_id"]] = "\n".join(lines)
    return result


def prompt(material: dict, names: dict[str, str]) -> tuple[str, list[dict], dict]:
    """F3, F8: the question for the model with the names replaced, within the budget. Returns
    (text, images as {'data', 'mime'}, counts)."""
    fixed = anonymize(material["head"] + "\n\n" + "\n\n".join(material["sections"]), names)
    room = max(0, BUDGET_CHARS - len(fixed) - 2000)
    contents = [dict(c, text=anonymize(c["text"], names), name=anonymize(c["name"], names)) for c in material["contents"]]
    # F8: per skill the same room, newest first; what does not fit goes with its name only.
    per_item = room // max(1, len(contents))
    shown, cut = [], []
    used = 0
    for c in contents:
        text = c["text"]
        if used >= room:
            cut.append(c["name"])
            continue
        if len(text) > per_item and len(contents) > 1:
            text = text[:max(per_item, 2000)] + " […ingekort]"
        text = text[:room - used]
        used += len(text)
        shown.append(f"### {c['name']} (bij {', '.join(c['skills'])})\n{text}")
    parts = [fixed]
    if shown:
        parts.append("# Inhoud van de bewijsstukken\n\n" + "\n\n".join(shown))
    if cut:
        parts.append("Van deze bewijsstukken past de inhoud niet; alleen de naam: " + ", ".join(cut))
    parts.append("Geef nu per vaardigheid (" + ", ".join(material["codes"]) + ") het advies.")
    counts = dict(material["counts"], cut=len(cut), names_only=[anonymize(n, names) for n in material["names_only"]],
                  images=len(material["images"]))
    return "\n\n".join(parts), [{"data": i["data"], "mime": i["mime"]} for i in material["images"]], counts


def check(answer: dict, codes: list[str]) -> list[dict]:
    """F5: only well-formed advice for the requested skills, in the order OC ... RE."""
    if not isinstance(answer, dict) or not isinstance(answer.get("vaardigheden"), list):
        raise ollama.OllamaError("Het model gaf geen bruikbaar advies. Probeer het opnieuw.")
    found = {}
    for item in answer["vaardigheden"]:
        if not isinstance(item, dict) or item.get("code") not in codes or item["code"] in found:
            continue
        level = item.get("niveau")
        if isinstance(level, str) and level.isdigit():
            level = int(level)
        if not isinstance(level, int) or isinstance(level, bool) or not 0 <= level <= 4:
            continue
        found[item["code"]] = {"code": item["code"], "name": NAMES[item["code"]], "level": level,
                               "reasoning": str(item.get("onderbouwing") or "").strip(),
                               "missing": str(item.get("ontbreekt") or "").strip()}
    if not found:
        raise ollama.OllamaError("Het model gaf geen bruikbaar advies. Probeer het opnieuw.")
    return [found[c] for c in SKILLS if c in found]


# Keeping the advice (F9) -------------------------------------------------------------------------

def duration(seconds: int | None) -> str:
    """F20: '45 s', '1 min 12 s'."""
    if seconds is None:
        return ""
    minutes, rest = divmod(int(seconds), 60)
    return f"{minutes} min {rest} s" if minutes else f"{rest} s"


def saved(conn: sqlite3.Connection, request_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM ai_advice WHERE review_request_id = ?", (request_id,)).fetchone()
    if row is None:
        return None
    moment = datetime.fromisoformat(row["created_at"]).astimezone()
    return {"model": row["model"], "service": row["service"], "service_label": SERVICES.get(row["service"], row["service"]),
            "date": f"{moment.day}-{moment.month}-{moment.year} {moment:%H:%M}",
            "duration": duration(row["seconds"]), "can_ask": bool(row["prompt"]),
            "conversation": [dict(turn, duration=duration(turn.get("seconds"))) for turn in json.loads(row["conversation"] or "[]")],
            "skills": json.loads(row["advice"]), "counts": json.loads(row["counts"])}


def save(database: str, request_id: int, model: str, skills: list[dict], counts: dict, service: str = "lokaal",
         seconds: int | None = None, prompt_text: str | None = None) -> None:
    """F9: a new advice replaces the old one and its conversation (F21)."""
    conn = db.connect(database)
    try:
        with conn:
            conn.execute("INSERT OR REPLACE INTO ai_advice (review_request_id, model, created_at, advice, counts, service, "
                         "seconds, prompt, conversation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '[]')",
                         (request_id, model, datetime.now(timezone.utc).isoformat(), json.dumps(skills), json.dumps(counts),
                          service, seconds, prompt_text))
    finally:
        conn.close()


def add_turn(database: str, request_id: int, question: str, answer: str, seconds: int) -> None:
    """F21: keep a follow-up question with its answer."""
    conn = db.connect(database)
    try:
        with conn:
            row = conn.execute("SELECT conversation FROM ai_advice WHERE review_request_id = ?", (request_id,)).fetchone()
            turns = json.loads(row["conversation"] or "[]") if row else []
            moment = datetime.now(timezone.utc).astimezone()
            turns.append({"question": question, "answer": answer, "seconds": seconds,
                          "date": f"{moment.day}-{moment.month}-{moment.year} {moment:%H:%M}"})
            conn.execute("UPDATE ai_advice SET conversation = ? WHERE review_request_id = ?", (json.dumps(turns), request_id))
    finally:
        conn.close()


FOLLOW_UP = ("Hieronder volgen vervolgvragen van de coach over jouw advies. Antwoord in het Nederlands, kort en "
             "concreet, op basis van hetzelfde materiaal. Verzin niets; zeg het als het materiaal geen antwoord geeft. "
             "Antwoord in gewone tekst, zonder JSON.")


def _history(row, question: str) -> list[dict]:
    """F21: the advice and the conversation so far as messages, then the new question."""
    advice = json.loads(row["advice"])
    messages = [{"role": "assistant", "content": json.dumps({"vaardigheden": [
        {"code": a["code"], "niveau": a["level"], "onderbouwing": a["reasoning"], "ontbreekt": a["missing"]} for a in advice]},
        ensure_ascii=False)}]
    turns = json.loads(row["conversation"] or "[]")
    for i, turn in enumerate(turns):
        prefix = FOLLOW_UP + "\n\n" if i == 0 else ""
        messages += [{"role": "user", "content": prefix + turn["question"]}, {"role": "assistant", "content": turn["answer"]}]
    messages.append({"role": "user", "content": (FOLLOW_UP + "\n\n" if not turns else "") + question})
    return messages


# Running in the background (F4) ------------------------------------------------------------------------

class Jobs:
    """One advice at a time per request; the page polls the status."""

    def __init__(self, database: str, token_source):
        self.database = database
        self.token_source = token_source     # () -> Portflow token or None
        self.lock = threading.Lock()
        self.jobs: dict[int, dict] = {}

    def status(self, request_id: int) -> dict | None:
        with self.lock:
            job = self.jobs.get(request_id)
            return {k: v for k, v in job.items() if k != "cancel"} if job else None

    def ask(self, request_id: int, question: str) -> bool:
        """F21: a follow-up question to the AI that made the advice."""
        question = question.strip()
        if not question:
            return False
        with self.lock:
            job = self.jobs.get(request_id)
            if job and job["state"] == "running":
                return False
            self.jobs[request_id] = {"state": "running", "kind": "question", "step": "Antwoord wordt gemaakt…", "error": "",
                                     "question": question, "cancel": threading.Event()}
        threading.Thread(target=self._ask, args=(request_id, question), daemon=True).start()
        return True

    def _ask(self, request_id: int, question: str) -> None:
        import time
        cancel = self.jobs[request_id]["cancel"]
        conn = db.connect(self.database)
        try:
            row = conn.execute("SELECT * FROM ai_advice WHERE review_request_id = ?", (request_id,)).fetchone()
            if row is None or not row["prompt"]:
                raise ollama.OllamaError("Vraag eerst opnieuw een advies; bij dit advies is het materiaal niet bewaard.")
            student = conn.execute("SELECT s.name FROM evaluations e JOIN students s ON s.id = e.student_id "
                                   "WHERE e.review_request_id = ? LIMIT 1", (request_id,)).fetchone()
            names = replacements(conn, student["name"] if student else "")
            history = _history(row, anonymize(question, names))
            started = time.monotonic()

            def written(*_):
                self._set(request_id, step=f"Antwoord wordt gemaakt… ({int(time.monotonic() - started)} s)")

            if row["service"] == "claude":
                if not claude_ai.ready(self.database):
                    raise ollama.OllamaError("Claude is niet meer ingesteld. Open AI-advies instellen.")
                answer = claude_ai.chat(claude_ai.key(self.database), system_prompt(self.database), row["prompt"], None,
                                        history=history, cancel=cancel, progress=written)
            else:
                url, _model = settings(self.database)
                answer = ollama.chat(url, row["model"], system_prompt(self.database), row["prompt"], None, history=history,
                                     num_ctx=NUM_CTX, cancel=cancel, progress=written)
            if not answer:
                raise ollama.OllamaError("Het model gaf geen antwoord. Probeer het opnieuw.")
            add_turn(self.database, request_id, question, answer, round(time.monotonic() - started))
            self._set(request_id, state="done", step="Klaar")
        except ollama.OllamaError as error:
            self._set(request_id, state="stopped" if cancel.is_set() else "error", error=error.message)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("AI follow-up failed")
            self._set(request_id, state="error", error="Er ging iets mis bij het beantwoorden van de vraag.")
        finally:
            conn.close()

    def start(self, request_id: int, service: str = "lokaal") -> bool:
        if service not in SERVICES:
            return False
        with self.lock:
            job = self.jobs.get(request_id)
            if job and job["state"] == "running":
                return False
            self.jobs[request_id] = {"state": "running", "kind": "advice", "step": "Materiaal verzamelen…", "error": "", "service": service,
                                     "service_label": SERVICES[service], "cancel": threading.Event()}
        threading.Thread(target=self._run, args=(request_id, service), daemon=True).start()
        return True

    def stop(self, request_id: int) -> None:
        with self.lock:
            job = self.jobs.get(request_id)
            if job and job["state"] == "running":
                job["cancel"].set()
                job["step"] = "Stoppen…"

    def _set(self, request_id: int, **values) -> None:
        with self.lock:
            self.jobs[request_id].update(values)

    def _run(self, request_id: int, service: str) -> None:
        cancel = self.jobs[request_id]["cancel"]
        url, model = settings(self.database)
        conn = db.connect(self.database)
        try:
            if service == "claude":
                api_key, model, vision = claude_ai.key(self.database), claude_ai.MODEL, True
                if not claude_ai.ready(self.database):
                    raise ollama.OllamaError("Claude is nog niet ingesteld. Open AI-advies instellen.")
            else:
                if not ollama.has_model(url, model):
                    raise ollama.OllamaError(f"Het model {model} staat niet in Ollama. Open de wizard AI-advies instellen.")
                vision = "vision" in ollama.capabilities(url, model)

            def step(text):
                if cancel.is_set():
                    raise ollama.OllamaError("Gestopt.")
                self._set(request_id, step=text)

            material = collect(conn, self.database, self.token_source(), request_id, date.today(), step, vision=vision)
            text, images, counts = prompt(material, replacements(conn, material["student"]))
            step("Advies schrijven…")
            import time
            started = time.monotonic()

            def written(*_):
                self._set(request_id, step=f"Advies schrijven… ({int(time.monotonic() - started)} s)")

            if service == "claude":
                answer = claude_ai.chat(api_key, system_prompt(self.database), text, schema(material["codes"]), images=images,
                                        cancel=cancel, progress=written)
            else:
                answer = ollama.chat(url, model, system_prompt(self.database), text, schema(material["codes"]), images=[i["data"] for i in images],
                                     num_ctx=NUM_CTX, cancel=cancel, progress=written)
            save(self.database, request_id, model, check(answer, material["codes"]), counts, service,
                 round(time.monotonic() - started), text)
            self._set(request_id, state="done", step="Klaar")
        except ollama.OllamaError as error:
            self._set(request_id, state="stopped" if cancel.is_set() else "error", error=error.message)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("AI advice failed")
            self._set(request_id, state="error", error="Er ging iets mis bij het maken van het advies.")
        finally:
            conn.close()


# The trial question of the wizard (F12, step 4) ------------------------------------------------------------

TRIAL = ("Vaardigheid PL (Plannen). De student vraagt niveau 1.\nZelfevaluatie: Ik heb voor mijn eigen taken in sprint 2 "
         "een planning gemaakt en die bijgehouden.\nLEF niveau 1 – Plannen van eigen werk: je maakt een planning voor je "
         "eigen werk en houdt die bij.\nBewijsstukken: Planning sprint 2 (bestand).\nGeef het advies.")


def trial(url: str, model: str, system: str = SYSTEM) -> dict:
    """A small invented evaluation; returns {'seconds', 'level'} or raises OllamaError."""
    import time
    started = time.monotonic()
    answer = ollama.chat(url, model, system, TRIAL, schema(["PL"]), num_ctx=4096, timeout=600)
    advice = check(answer, ["PL"])
    return {"seconds": round(time.monotonic() - started), "level": advice[0]["level"]}
