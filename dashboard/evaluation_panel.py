"""Evaluaties lezen in een zijpaneel (spec 037): the whole evaluation request as a conversation per
skill (the self-evaluation, then the assessments), for the blocks and the level cells. The texts are stored at Verversen (portflow_fetch, F1)."""

import sqlite3
from datetime import date

from .evidence import safe_html
from .progress import name_key
from .skills import CATEGORY, NAMES, SKILLS


def _ids(value: str | None) -> list[int]:
    return [int(i) for i in (value or "").split(",") if i.strip().isdigit()]


def parse_args(args) -> tuple[list[int], list[int]]:
    """The request ids ('verzoeken') and loose evaluation ids ('losse') of a panel link."""
    return _ids(args.get("verzoeken")), _ids(args.get("losse"))


def _staff(conn: sqlite3.Connection) -> dict[str, tuple[bool, bool]]:
    return {name_key(r["name"]): (bool(r["is_coach"]), bool(r["is_guild_master"]))
            for r in conn.execute("SELECT name, is_coach, is_guild_master FROM staff")}


def _role(assessor: str | None, skill: str, staff: dict) -> str:
    """Coach or gildemeester from the lists; someone who is both gets the role that assesses this
    skill (CLAUDE.md: product skills by the guild master, the others by the coach)."""
    coach, guild_master = staff.get(name_key(assessor), (False, False))
    if coach and guild_master:
        return "gildemeester" if CATEGORY[skill] == "product" else "coach"
    if guild_master:
        return "gildemeester"
    if coach:
        return "coach"
    return "overig"


def _day(value: str | None) -> str:
    try:
        d = date.fromisoformat((value or "")[:10])
    except ValueError:
        return ""
    return f"{d.day}-{d.month}-{d.year}"


def conversations(conn: sqlite3.Connection, student_id: int, request_ids: list[int],
                  loose_ids: list[int] = ()) -> list[dict]:
    """F2: per request (newest first) the title, the date of handing in and per skill (OC ... RE)
    the self-evaluation and the assessments. Loose evaluations (without a request) are shown alone."""
    student = conn.execute("SELECT name FROM students WHERE id = ?", (student_id,)).fetchone()
    student_name = student["name"] if student else "De student"
    staff = _staff(conn)
    groups: dict = {}
    if request_ids:
        marks = ",".join("?" * len(request_ids))
        for row in conn.execute(f"SELECT * FROM evaluations WHERE student_id = ? AND review_request_id IN ({marks}) "
                                "ORDER BY date, id", (student_id, *request_ids)):
            groups.setdefault(("r", row["review_request_id"]), []).append(row)
    if loose_ids:
        marks = ",".join("?" * len(loose_ids))
        for row in conn.execute(f"SELECT * FROM evaluations WHERE student_id = ? AND id IN ({marks})",
                                (student_id, *loose_ids)):
            groups.setdefault(("e", row["id"]), []).append(row)

    result = []
    for rows in groups.values():
        selfs = [r for r in rows if r["kind"] == "self"]
        submitted = min((r["date"] for r in selfs if r["date"]), default="") or min(
            (r["date"] for r in rows if r["date"]), default="")
        skills = []
        for code in SKILLS:
            own = [r for r in rows if r["skill"] == code]
            if not own:
                continue
            skills.append({
                "code": code, "name": NAMES[code],
                "self": [{"author": student_name, "level": r["level"], "date": _day(r["date"]),
                          "text": safe_html(r["text"] or "")} for r in own if r["kind"] == "self"],
                "assessed": [{"author": r["assessor"] or "Onbekend", "role": _role(r["assessor"], code, staff),
                              "level": r["level"], "date": _day(r["date"]), "text": safe_html(r["text"] or "")}
                             for r in own if r["kind"] == "assessed"],
            })
        result.append({"title": next((r["review_request_title"] for r in rows if r["review_request_title"]), None)
                       or "Evaluatie", "submitted": submitted, "date": _day(submitted), "skills": skills})
    result.sort(key=lambda r: r["submitted"], reverse=True)
    return result

