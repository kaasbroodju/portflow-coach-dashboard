"""The timeline of evaluations on the page Evaluaties (spec 029): per week of the semester
period the achieved and the handed-in, not yet assessed evaluations.

Which evaluations count is decided by progress.py (via overview.student_rows); this module
only puts them in weeks. Labels are Dutch: they are shown to the user.
"""

import math
import sqlite3
from datetime import date, timedelta

from .overview import WHO, WHO_DEFAULT

S_WHO = "evaluations_who"   # F2: the choice of Evaluaties, apart from Overzicht
MONTHS = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
          "augustus", "september", "oktober", "november", "december"]


def long_date(day: date) -> str:
    """'1 september 2026'."""
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def _day(value: str) -> date | None:
    try:
        return date.fromisoformat((value or "")[:10])
    except ValueError:
        return None


def week_counts(rows: list[dict], start: date, end: date) -> list[dict]:
    """F1, F3, F3a: one entry per week (Monday to Sunday) from the week of `start` to the week of
    `end`. An evaluation counts in the week it was handed in; one without a date is left out."""
    first = start - timedelta(days=start.weekday())
    weeks = [{"number": i + 1, "monday": first + timedelta(weeks=i), "achieved": 0, "pending": 0}
             for i in range((end - first).days // 7 + 1)]

    def add(value: str, kind: str) -> None:
        day = _day(value)
        if day is not None and start <= day <= end:
            weeks[(day - first).days // 7][kind] += 1

    for row in rows:
        for cell in row["progress"].cells.values():
            for evaluation in cell.evaluations:
                add(evaluation.submitted or evaluation.date, "achieved")
            if cell.pending:   # a full assessment has no pending cells (voortgangsregels.md#openstaand)
                add(cell.pending.date, "pending")
    for week in weeks:
        week["sunday"] = week["monday"] + timedelta(days=6)
        week["total"] = week["achieved"] + week["pending"]
    return weeks


def scale(weeks: list[dict]) -> dict:
    """The vertical axis: a round top and at most about five steps; heights in percent."""
    highest = max((w["total"] for w in weeks), default=0)
    if highest == 0:
        return {"top": 0, "ticks": []}
    raw = highest / 5
    magnitude = 10 ** math.floor(math.log10(raw)) if raw >= 1 else 1
    step = next(m * magnitude for m in (1, 2, 5, 10) if m * magnitude >= raw)
    top = math.ceil(highest / step) * step
    for week in weeks:
        week["achieved_pct"] = round(100 * week["achieved"] / top, 2)
        week["pending_pct"] = round(100 * week["pending"] / top, 2)
    return {"top": top, "ticks": [{"value": v, "pct": round(100 * v / top, 2)} for v in range(0, top + 1, step)]}


# The choice "wie" (F2), remembered apart from Overzicht -----------------------------------------

def saved_who(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (S_WHO,)).fetchone()
    return row[0] if row and row[0] in dict(WHO) else WHO_DEFAULT


def save_who(conn: sqlite3.Connection, who: str) -> str:
    who = who if who in dict(WHO) else WHO_DEFAULT
    with conn:
        conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
                     "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (S_WHO, who))
    return who


# The compact progress table (spec 029, F7-F11) ----------------------------------------------------

def project_blocks(rows: list[dict]) -> list[list[dict]]:
    """F10: the students per project, in the order of the projects on Overzicht, without a project
    last; by name within a block. The template draws a thin line between blocks."""
    blocks: dict[tuple, list[dict]] = {}
    for row in rows:
        key = (0, row["squad_sort"].casefold(), row["squad_id"]) if row["squad_id"] else (1, "", 0)
        blocks.setdefault(key, []).append(row)
    return [sorted(blocks[key], key=lambda r: r["name"].casefold()) for key in sorted(blocks)]
