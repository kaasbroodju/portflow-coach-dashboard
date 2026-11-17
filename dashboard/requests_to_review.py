"""Te beoordelen (spec 030): the open review requests sent to the user, oldest first.

The requests are stored by the fetch round (portflow_fetch.Fetcher._save_requests); the skills
of a request come from the stored self-evaluations with the same review_request_id. Labels are
Dutch: they are shown to the user.
"""

import sqlite3
from datetime import date, datetime

from .portflow_connection import initials
from .skills import SKILLS

OPEN_STATUSES = ("not_started", "in_progress")   # F1


def _local_day(value: str) -> date | None:
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    return moment.astimezone().date() if moment.tzinfo else moment.date()


def waiting_text(days: int) -> str:
    """F1: 'vandaag', '1 dag', '5 dagen'."""
    if days <= 0:
        return "vandaag"
    return "1 dag" if days == 1 else f"{days} dagen"


def open_count(conn: sqlite3.Connection) -> int:
    """F6: the number for the menu."""
    return conn.execute("SELECT COUNT(*) FROM received_requests WHERE status IN (?, ?)", OPEN_STATUSES).fetchone()[0]


def open_requests(conn: sqlite3.Connection, today: date) -> list[dict]:
    """F1-F4: one dict per open request, the one waiting longest first."""
    names = {r["portflow_user_id"]: r["name"] for r in conn.execute(
        "SELECT portflow_user_id, name FROM students WHERE portflow_user_id IS NOT NULL")}
    skills: dict[int, set[str]] = {}
    for r in conn.execute("SELECT DISTINCT review_request_id, skill FROM evaluations "
                          "WHERE kind = 'self' AND review_request_id IN "
                          "(SELECT review_request_id FROM received_requests)"):
        skills.setdefault(r["review_request_id"], set()).add(r["skill"])
    result = []
    for r in conn.execute("SELECT * FROM received_requests WHERE status IN (?, ?)", OPEN_STATUSES):
        name = names.get(r["student_portflow_id"]) or r["student_name"] or "Onbekende student"
        found = skills.get(r["review_request_id"], set())
        day = _local_day(r["created_at"])
        result.append({
            "id": r["review_request_id"],
            "student": name,
            "initials": initials(name),
            "followed": r["student_portflow_id"] in names,
            "title": r["title"] or "Evaluatieverzoek",
            "skills": [s for s in SKILLS if s in found],
            "full_assessment": found >= set(SKILLS),          # F4
            "submitted": day,
            "waiting": waiting_text((today - day).days) if day else "",
            "sort": r["created_at"] or "~",
        })
    return sorted(result, key=lambda r: (r["sort"], r["id"]))   # F2: oldest first
