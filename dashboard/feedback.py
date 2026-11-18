"""Feedbackvragen en reacties (spec 035): the feedback requests of a student on his evidence, the
replies to them, key figures, two rows for the evidence timeline and the side panel.

The comments are fetched together with the evidence (evidence.fetch_for_student)."""

import sqlite3
from datetime import date, timedelta

from .evidence import KINDS, _local_day, plain_text
from .progress import name_key

ROLES = {"medestudent": "medestudent", "coach": "coach", "gildemeester": "gildemeester",
         "zelf": "de student zelf", "overig": "overig"}


def _staff(conn: sqlite3.Connection) -> dict[str, str]:
    roles = {}
    for row in conn.execute("SELECT name, is_coach, is_guild_master FROM staff"):
        roles[name_key(row["name"])] = "gildemeester" if row["is_guild_master"] else ("coach" if row["is_coach"] else "overig")
    return roles


def role_of(comment: dict, own_id: int | None, staff: dict[str, str]) -> str:
    """F3: the role of whoever wrote a comment: the lists Coaches and Gildemeesters first, then Portflow."""
    if own_id is not None and comment["author_id"] == own_id:
        return "zelf"
    if name_key(comment["author_name"]) in staff:
        return staff[name_key(comment["author_name"])]
    portflow_role = (comment["author_role"] or "").casefold()
    if portflow_role == "student":
        return "medestudent"
    if portflow_role in ("coach", "teacher", "assessor"):
        return "coach"
    return "overig"


def _requests(conn: sqlite3.Connection, student_id: int, start: date, end: date) -> list[dict]:
    """The feedback requests asked in the period, each with its replies (oldest first) and roles."""
    own = conn.execute("SELECT portflow_user_id FROM students WHERE id = ?", (student_id,)).fetchone()
    own_id = own[0] if own else None
    staff = _staff(conn)
    comments = [dict(r) for r in conn.execute(
        "SELECT * FROM evidence_comments WHERE student_id = ? ORDER BY created_at, comment_id", (student_id,))]
    replies: dict[int, list[dict]] = {}
    for c in comments:
        c["day"] = _local_day(c["created_at"])
        c["role"] = role_of(c, own_id, staff)
        if c["parent_id"] is not None:
            replies.setdefault(c["parent_id"], []).append(c)
    result = []
    for c in comments:
        if c["parent_id"] is None and c["kind"] == "feedback_request" and c["day"] and start <= c["day"] <= end:
            c["replies"] = replies.get(c["comment_id"], [])
            c["from_others"] = [r for r in c["replies"] if r["role"] != "zelf"]
            result.append(c)
    return result


def summary(conn: sqlite3.Connection, student_id: int, start: date, end: date) -> dict:
    """F2: the key figures of the requests asked in the period; replies by the student himself do not count."""
    requests = _requests(conn, student_id, start, end)
    answered = [r for r in requests if r["from_others"]]
    replies = [reply for r in requests for reply in r["from_others"]]
    people = {reply["author_id"] or reply["author_name"] for reply in replies}
    waits = [(r["from_others"][0]["day"] - r["day"]).days for r in answered if r["from_others"][0]["day"]]
    return {"requests": len(requests), "answered": len(answered), "replies": len(replies), "people": len(people),
            "first_reply_days": round(sum(waits) / len(waits), 1) if waits else None}


def rows(conn: sqlite3.Connection, student_id: int, start: date, end: date) -> list[dict]:
    """F3: the rows Feedbackvraag (a mark per day; open when one of them has no reply yet) and
    Reactie (a mark per day, coloured by role), positioned like the evidence dots."""
    first = start - timedelta(days=start.weekday())
    span = ((end - first).days // 7 + 1) * 7
    left = lambda day: round(100 * ((day - first).days + 0.5) / span, 2)
    names = {r["evidence_id"]: r["name"] for r in conn.execute(
        "SELECT evidence_id, name FROM evidence_items WHERE student_id = ?", (student_id,))}
    asked: dict[date, dict] = {}
    answers: dict[date, dict] = {}
    for request in _requests(conn, student_id, start, end):
        mark = asked.setdefault(request["day"], {"ids": [], "open": False, "tips": []})
        mark["ids"].append(request["comment_id"])
        mark["open"] = mark["open"] or not request["from_others"]
        count = len(request["from_others"])
        mark["tips"].append(f"Feedbackvraag bij {names.get(request['evidence_id']) or 'een bewijsstuk'} · "
                            + (f"{count} reactie{'s' if count != 1 else ''}" if count else "nog geen reactie"))
        for reply in request["replies"]:
            if reply["day"] and start <= reply["day"] <= end:
                mark = answers.setdefault(reply["day"], {"ids": [], "roles": set(), "tips": []})
                if request["comment_id"] not in mark["ids"]:
                    mark["ids"].append(request["comment_id"])
                mark["roles"].add(reply["role"])
                mark["tips"].append(f"Reactie van {reply['author_name'] or 'onbekend'} ({ROLES[reply['role']]})")

    def marks(by_day: dict, kind) -> list[dict]:
        return [{"left": left(day), "count": len(m["tips"]), "ids": ",".join(map(str, m["ids"])),
                 "kind": kind(m), "tip": "\n".join(m["tips"])} for day, m in sorted(by_day.items())]

    return [{"code": "Feedbackvraag", "shape": "request",
             "marks": marks(asked, lambda m: "open" if m["open"] else "answered")},
            {"code": "Reactie", "shape": "reply",
             "marks": marks(answers, lambda m: next(iter(m["roles"])) if len(m["roles"]) == 1 else "gemengd")}]


def threads(conn: sqlite3.Connection, student_id: int, request_ids: list[int], start: date, end: date) -> list[dict]:
    """F4: for the side panel: per request the evidence, the request and the replies."""
    wanted = set(request_ids)
    items = {r["evidence_id"]: dict(r) for r in conn.execute(
        "SELECT * FROM evidence_items WHERE student_id = ?", (student_id,))}
    result = []
    for request in _requests(conn, student_id, start, end):
        if request["comment_id"] not in wanted:
            continue
        item = items.get(request["evidence_id"], {})
        result.append({
            "evidence_id": request["evidence_id"], "evidence": item.get("name") or "Bewijsstuk", "raw_kind": item.get("kind") or "",
            "kind": KINDS.get(item.get("kind"), item.get("kind") or ""),
            "skills": [s for s in (item.get("skills") or "").split(",") if s],
            "request": _show(request),
            "replies": [_show(reply) for reply in request["replies"]],
        })
    return result


def _show(comment: dict) -> dict:
    day = comment["day"]
    return {"author": comment["author_name"] or "Onbekend", "role": ROLES[comment["role"]],
            "date": f"{day.day}-{day.month}-{day.year}" if day else "", "text": plain_text(comment["text"])}
