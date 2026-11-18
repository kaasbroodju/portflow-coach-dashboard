"""Tijdlijn van bewijsstukken (spec 034): the evidence of one student, fetched from Portflow when
his page is opened, and arranged as dots per skill over the semester period.

Read only: GET /portfolios/{id}/collections and /portfolios/{id}/collections/{id}/evidence (see
docs/portflow-API-reverse-engineer.md). The contents of evidence are never fetched.
"""

import sqlite3
from datetime import date, datetime, timedelta, timezone

from . import portflow_api
from .skills import NAMES, SKILLS, skill_for_goal_name

OTHER = "Overig"   # F4: a row for evidence linked to none of the ten skills
KINDS = {"file": "bestand", "free_text": "tekst", "url": "link"}


def _local_day(value: str) -> date | None:
    try:
        moment = datetime.fromisoformat((value or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment.astimezone().date() if moment.tzinfo else moment.date()


def fetch_for_student(conn: sqlite3.Connection, student_id: int, token: str | None, *, api=portflow_api,
                      now=lambda: datetime.now(timezone.utc)) -> str | None:
    """F1: fetch and store the evidence of one student. Returns a message (Dutch) when it did not
    work; the stored evidence then stays as it was."""
    if not token:
        return "Niet verbonden met Portflow: de bewijsstukken zijn niet opgehaald."
    portfolios = [r[0] for r in conn.execute("SELECT portfolio_id FROM student_portfolios WHERE student_id = ?",
                                             (student_id,))]
    if not portfolios:
        return "Deze student is niet gekoppeld aan een Portflow-portfolio."
    found: dict[int, dict] = {}
    collection_count = 0
    for portfolio_id in portfolios:
        status, items = api.collections(token, portfolio_id)
        if status == 401:
            return "Portflow accepteert de verbinding niet meer; verbind opnieuw en probeer het nog eens."
        if status == 404 or status == 403:
            continue   # not shared (any more)
        if status != 200:
            return "De bewijsstukken konden niet worden opgehaald. Probeer het later opnieuw."
        for collection in items or []:
            collection_count += 1
            status, entries = api.collection_evidence(token, portfolio_id, collection.get("id"))
            if status != 200:
                continue
            for entry in entries or []:
                evidence = entry.get("evidence") if isinstance(entry.get("evidence"), dict) else None
                if not evidence or not isinstance(evidence.get("id"), int):
                    continue
                item = found.setdefault(evidence["id"], {
                    "evidence_id": evidence["id"], "name": str(evidence.get("name") or ""),
                    "kind": str(evidence.get("latest_version_type") or ""),
                    "created_at": str(evidence.get("created_at") or ""),
                    "updated_at": str(evidence.get("latest_version_created_at") or ""),
                    "collections": [], "skills": set()})
                name = str(collection.get("name") or "")
                if name and name not in item["collections"]:
                    item["collections"].append(name)
                for goal in evidence.get("goals") or []:
                    code = skill_for_goal_name(goal.get("name")) if isinstance(goal, dict) else None
                    if code:
                        item["skills"].add(code)
    with conn:
        conn.execute("DELETE FROM evidence_items WHERE student_id = ?", (student_id,))
        conn.executemany(
            "INSERT INTO evidence_items (student_id, evidence_id, name, kind, created_at, updated_at, collections, skills) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [(student_id, i["evidence_id"], i["name"], i["kind"], i["created_at"], i["updated_at"],
              "; ".join(i["collections"]), ",".join(s for s in SKILLS if s in i["skills"])) for i in found.values()])
        conn.execute("INSERT INTO evidence_fetches (student_id, fetched_at, collections, error) VALUES (?, ?, ?, '') "
                     "ON CONFLICT(student_id) DO UPDATE SET fetched_at = excluded.fetched_at, "
                     "collections = excluded.collections, error = ''", (student_id, now().isoformat(), collection_count))
    return None


def last_fetch(conn: sqlite3.Connection, student_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM evidence_fetches WHERE student_id = ?", (student_id,)).fetchone()
    return dict(row) if row else None


def _nl(day: date | None) -> str:
    return f"{day.day}-{day.month}-{day.year}" if day else "onbekend"


def timeline(conn: sqlite3.Connection, student_id: int, start: date, end: date) -> dict:
    """F2-F4: one row per skill (OC ... RE) and Overig; per row the dots of evidence added in the
    period, one dot per day (with a count when more than one). Positions in percent of the weeks of
    the period (the same weeks as the evaluation timeline)."""
    first = start - timedelta(days=start.weekday())
    span = ((end - first).days // 7 + 1) * 7
    rows = {code: {} for code in list(SKILLS) + [OTHER]}
    total = 0
    for item in conn.execute("SELECT * FROM evidence_items WHERE student_id = ? ORDER BY created_at, evidence_id",
                             (student_id,)):
        day = _local_day(item["created_at"])
        if day is None or not start <= day <= end:
            continue
        total += 1
        skills = [s for s in item["skills"].split(",") if s] or [OTHER]
        tip = (f"{item['name'] or 'Bewijsstuk'} ({KINDS.get(item['kind'], item['kind'] or 'onbekend')})"
               f", toegevoegd {_nl(day)}")
        updated = _local_day(item["updated_at"])
        if updated and updated != day:
            tip += f", laatste versie {_nl(updated)}"
        if item["collections"]:
            tip += f", collectie {item['collections']}"
        tip += ", " + (", ".join(skills) if skills != [OTHER] else "geen vaardigheid")
        for code in skills:
            dot = rows[code].setdefault(day, {"day": day, "kinds": set(), "tips": []})
            dot["kinds"].add(item["kind"])
            dot["tips"].append(tip)
    result = []
    for code, dots in rows.items():
        result.append({
            "code": code, "name": NAMES.get(code, "Niet aan een vaardigheid gekoppeld"),
            "dots": [{"left": round(100 * ((d["day"] - first).days + 0.5) / span, 2), "count": len(d["tips"]),
                      "kind": next(iter(d["kinds"])) if len(d["kinds"]) == 1 else "mixed",
                      "tip": "\n".join(d["tips"])} for d in dots.values()],
        })
    return {"rows": result, "total": total}
