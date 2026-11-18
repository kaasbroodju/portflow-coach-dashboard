"""Namen verbergen (spec 033): replace the names of students by "Student N" in every page the
dashboard sends, for demonstrations and screenshots. Only the display changes; nothing is saved.

The replacement happens once, after a page has been rendered (F4), so new pages take part by
themselves. The switch lives in memory and is off again after a restart (F6).
"""

import json
import re
import sqlite3

from flask import Flask, current_app, request
from markupsafe import escape

from .progress import name_key

PLACEHOLDER = "Student {}"
TEXT_TYPES = ("text/html", "application/json")
# A student avatar: the initials, then (before any other avatar) the name, already replaced.
_AVATAR_BEFORE_NAME = re.compile(
    r'(<span class="avatar avatar-small">)[^<]*(</span>)((?:(?!<span class="avatar).){0,600}?Student (\d+))', re.S)
_AVATAR_WITH_TITLE = re.compile(r'(<span class="avatar[^"]*" title="Student (\d+)">)[^<]*(</span>)')


def is_on(app: Flask | None = None) -> bool:
    return bool((app or current_app).extensions.get("hide_names"))


def set_on(app: Flask, on: bool) -> None:
    app.extensions["hide_names"] = bool(on)


def numbers(conn: sqlite3.Connection) -> dict[str, str]:
    """F2: name -> "Student N". Followed students in the order they were added; then the names of
    students who sent the user a request but are not followed (spec 030). The user keeps his own
    name; coaches and guild masters keep theirs when they send a request, but a followed student
    is always hidden, also when he is on the staff list too (for example as an assessor)."""
    me = {name_key(r[0]) for r in conn.execute("SELECT value FROM settings WHERE key = 'portflow_user_name'") if r[0]}
    staff = {name_key(r[0]) for r in conn.execute("SELECT name FROM staff") if r[0]}
    names: dict[str, str] = {}

    def add(name: str | None, keep: set[str]) -> None:
        if name and name.strip() and name not in names and name_key(name) not in keep:
            names[name] = PLACEHOLDER.format(len(names) + 1)

    for (name,) in conn.execute("SELECT name FROM students ORDER BY id"):
        add(name, me)
    for (name,) in conn.execute("SELECT student_name FROM received_requests ORDER BY review_request_id"):
        add(name, me | staff)
    return names


def anonymize(text: str, names: dict[str, str]) -> str:
    """Replace every full name (as text, HTML-escaped and JSON-escaped, any case) and put the
    student's number in its avatar (F3)."""
    if not names:
        return text
    variants: dict[str, str] = {}
    for name, number in names.items():
        for form in (name, str(escape(name)), json.dumps(name)[1:-1]):
            variants.setdefault(form.casefold(), number)
    # Whole words only: a student called "Bas" must not change "Basis".
    pattern = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(v) for v in sorted(variants, key=len, reverse=True)) + r")(?!\w)",
                         re.IGNORECASE)
    text = pattern.sub(lambda m: variants.get(m.group(0).casefold(), m.group(0)), text)
    text = _AVATAR_WITH_TITLE.sub(lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}", text)
    return _AVATAR_BEFORE_NAME.sub(lambda m: f"{m.group(1)}{m.group(4)}{m.group(2)}{m.group(3)}", text)


def real_name(conn: sqlite3.Connection, student_id: int, submitted: str) -> str:
    """F7: a form sent while names are hidden carries "Student N"; keep the real name then."""
    row = conn.execute("SELECT name FROM students WHERE id = ?", (student_id,)).fetchone()
    if row and is_on() and submitted.strip() == numbers(conn).get(row[0]):
        return row[0]
    return submitted


def init_app(app: Flask, get_db) -> None:
    app.extensions["hide_names"] = False

    @app.after_request
    def hide(response):
        if (not is_on(app) or response.direct_passthrough or response.mimetype not in TEXT_TYPES
                or request.endpoint == "static"):
            return response
        names = numbers(get_db())
        response.set_data(anonymize(response.get_data(as_text=True), names))
        return response
