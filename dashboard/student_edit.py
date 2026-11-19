"""Editing one student (spec 011; guilds: spec 016): choices, checks, saving and no longer following."""

import sqlite3
from datetime import date

from . import choices, overview, student_guilds
from .progress import name_key


def find(conn: sqlite3.Connection, student_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()


def form_values(conn: sqlite3.Connection, student: sqlite3.Row) -> dict:
    """The current values, as strings for the form (F2)."""
    text = lambda value: "" if value is None else str(value)
    guilds = [{"guild_id": str(g["guild_id"]), "guild_master_id": text(g["guild_master_id"])}
              for g in student_guilds.of_student(conn, student["id"])]
    return {
        "name": student["name"], "student_number": text(student["student_number"]),
        "semester": text(student["semester"]), "start_date": text(student["start_date"]),
        "squad_id": text(student["squad_id"]), "track": text(student["track_id"]),
        "squad_role": text(student["squad_role_id"]), "guilds": guilds, "coach_id": text(student["coach_id"]),
        "notes": text(student["notes"]),
        # Spec 026: the values of the custom columns, by column id (as text).
        "custom": {str(r["column_id"]): r["value"] for r in conn.execute(
            "SELECT column_id, value FROM custom_values WHERE student_id = ?", (student["id"],))},
    }


def options(conn: sqlite3.Connection) -> dict:
    """The choices of the form (F2)."""
    rows = lambda sql: [dict(r) for r in conn.execute(sql)]
    return {
        "semesters": rows("SELECT number, osiris_code FROM semesters ORDER BY number"),
        # The display name of the project (spec 012, F12), in the order of the project numbers.
        "squads": [dict(s, full_name=s["display_name"] or s["full_name"]) for s in
                   rows("SELECT id, name, full_name, display_name FROM squads ORDER BY full_name")],
        # Spec 024: the choice lists; the value is the item id.
        "tracks": [(str(i["id"]), i["label"], i["code"]) for i in choices.kind_items(conn, choices.TRACK)],
        "squad_roles": [(str(i["id"]), i["code"], i["description"]) for i in choices.kind_items(conn, choices.SQUAD_ROLE)],
        "guilds": rows("SELECT id, code, name FROM guilds ORDER BY code"),   # spec 018, F6
        "coaches": rows("SELECT id, name FROM staff WHERE is_coach = 1 ORDER BY name COLLATE NOCASE"),
        "guild_masters": rows("SELECT id, name FROM staff WHERE is_guild_master = 1 ORDER BY name COLLATE NOCASE"),
        # Spec 026, F1, F2: the custom columns in their order, a choice column with its items.
        "custom_columns": [dict(c, choices=choices.column_items(conn, c["id"]) if c["type"] == "choice" else [])
                           for c in overview.custom_columns(conn)],
    }


def portflow_link(conn: sqlite3.Connection, student: sqlite3.Row) -> dict:
    """F3: the Portflow link, read only."""
    portfolios = [r[0] for r in conn.execute(
        "SELECT portfolio_id FROM student_portfolios WHERE student_id = ? ORDER BY portfolio_id", (student["id"],))]
    if student["portflow_user_id"] is None:
        status = "Niet gekoppeld"
    elif not student["has_access"]:
        status = "Portfolio niet gedeeld"
    else:
        status = "Gekoppeld"
    return {"status": status, "portfolios": portfolios}


def _choice(conn, value: str, sql: str) -> tuple[int | None, bool]:
    """(id or None, valid): an empty choice is None; otherwise the id must exist."""
    if not value:
        return None, True
    if not value.isdigit() or not conn.execute(sql, (int(value),)).fetchone():
        return None, False
    return int(value), True


def validate(conn: sqlite3.Connection, form: dict) -> tuple[dict | None, str | None]:
    """F5: returns (clean values, None) or (None, Dutch error message)."""
    name = " ".join((form.get("name") or "").split())
    if not name:
        return None, "Vul een naam in."
    start = (form.get("start_date") or "").strip()
    if start:
        try:
            start = date.fromisoformat(start).isoformat()
        except ValueError:
            return None, "Vul een geldige startdatum in, of laat het veld leeg."
    values = {"name": name, "student_number": " ".join((form.get("student_number") or "").split()) or None,
              "start_date": start or None,
              "notes": "\n".join(line.rstrip() for line in (form.get("notes") or "").strip().splitlines()) or None}
    checks = {
        "semester": ("SELECT 1 FROM semesters WHERE number = ?", "Kies een semester uit de lijst."),
        "squad_id": ("SELECT 1 FROM squads WHERE id = ?", "Kies een project uit de lijst."),
        "coach_id": ("SELECT 1 FROM staff WHERE id = ? AND is_coach = 1", "Kies een coach uit de lijst."),
    }
    for field, (sql, message) in checks.items():
        value, ok = _choice(conn, (form.get(field) or "").strip(), sql)
        if not ok:
            return None, message
        values[field] = value
    track = (form.get("track") or "").strip()
    squad_role = (form.get("squad_role") or "").strip()
    track_id, ok = _item(conn, track, choices.TRACK)
    if not ok:
        return None, "Kies een invulling uit de lijst."
    role_id, ok = _item(conn, squad_role, choices.SQUAD_ROLE)
    if not ok:
        return None, "Kies een rol uit de lijst."
    values["track_id"], values["squad_role_id"] = track_id, role_id
    # Spec 016, F4 (spec 018, F6): guild rows (guild + guild master); an empty guild is ignored.
    pairs: list[tuple[int, int | None]] = []
    for row in form.get("guilds") or []:
        guild_id, ok = _choice(conn, (row.get("guild_id") or "").strip(), "SELECT 1 FROM guilds WHERE id = ?")
        if not ok:
            return None, "Kies een gilde uit de lijst."
        if guild_id is None:
            continue
        if guild_id in [r for r, _ in pairs]:
            code = conn.execute("SELECT code FROM guilds WHERE id = ?", (guild_id,)).fetchone()[0]
            return None, f"{code} staat er twee keer in."
        master, ok = _choice(conn, (row.get("guild_master_id") or "").strip(),
                             "SELECT 1 FROM staff WHERE id = ? AND is_guild_master = 1")
        if not ok:
            return None, "Kies een gildemeester uit de lijst."
        pairs.append((guild_id, master))
    values["guilds"] = pairs
    # Spec 026, F3, F4: the custom columns, with the same check as in the table. A column that is
    # not in the form (for example added in the meantime) is left as it is.
    values["custom"] = {}
    sent = form.get("custom") or {}
    for column in conn.execute("SELECT * FROM custom_columns ORDER BY position, id").fetchall():
        if str(column["id"]) not in sent:
            continue
        value, error = overview.check_custom_value(conn, column, sent[str(column["id"])])
        if error:
            return None, error
        values["custom"][column["id"]] = value
    return values, None


def _item(conn: sqlite3.Connection, value: str, kind: str) -> tuple[int | None, bool]:
    """Spec 024: an item id of the list of `kind`; (None, True) for empty."""
    if not value:
        return None, True
    ok = value.isdigit() and any(i["id"] == int(value) for i in choices.kind_items(conn, kind))
    return (int(value), True) if ok else (None, False)


def _with_track(conn: sqlite3.Connection, values: dict) -> dict:
    """Spec 025, F1: an empty invulling follows from the semester."""
    item = choices.track_for_semester(conn, values.get("semester"), values.get("track_id"))
    return dict(values, track_id=item) if item else values


def save(conn: sqlite3.Connection, student_id: int, values: dict) -> None:
    """F4."""
    values = _with_track(conn, values)
    with conn:
        conn.execute(
            "UPDATE students SET name = :name, student_number = :student_number, semester = :semester, "
            "start_date = :start_date, squad_id = :squad_id, track_id = :track_id, squad_role_id = :squad_role_id, "
            "coach_id = :coach_id, notes = :notes WHERE id = :id",
            {k: v for k, v in dict(values, id=student_id).items() if k not in ("guilds", "custom")})
        student_guilds.replace(conn, student_id, values["guilds"])
        overview.set_custom_values(conn, student_id, values.get("custom", {}))   # spec 026, F3


def empty_form() -> dict:
    """Spec 017, F2: the edit form, empty."""
    keys = ("name", "student_number", "semester", "start_date", "squad_id", "track", "squad_role", "coach_id", "notes")
    return dict({key: "" for key in keys}, guilds=[], custom={})


def same_name(conn: sqlite3.Connection, name: str) -> dict | None:
    """Spec 017, F3: an existing student with the same name (case, spaces and accents ignored)."""
    key = name_key(name)
    return next((dict(r) for r in conn.execute("SELECT id, name FROM students ORDER BY id") if name_key(r["name"]) == key), None)


def number_owner(conn: sqlite3.Connection, number: str | None, student_id: int | None = None) -> str | None:
    """Spec 017, F3: the name of another student with this student number, if any."""
    if not number:
        return None
    row = conn.execute("SELECT name FROM students WHERE student_number = ? AND id != ?", (number, student_id or -1)).fetchone()
    return row[0] if row else None


def create(conn: sqlite3.Connection, values: dict) -> int:
    """Spec 017, F4: add a student with all values of the form."""
    values = _with_track(conn, values)
    with conn:
        student_id = conn.execute(
            "INSERT INTO students (name, student_number, semester, start_date, squad_id, track_id, squad_role_id, coach_id, notes) "
            "VALUES (:name, :student_number, :semester, :start_date, :squad_id, :track_id, :squad_role_id, :coach_id, :notes)",
            {k: v for k, v in values.items() if k not in ("guilds", "custom")}).lastrowid
        student_guilds.replace(conn, student_id, values["guilds"])
        overview.set_custom_values(conn, student_id, values.get("custom", {}))   # spec 026, F5
    return student_id


# Inline changes in the student list (spec 022) ---------------------------------------------

INLINE_FIELDS = ("semester", "squad_id", "track", "squad_role", "coach_id", "guild")


def inline_options(conn: sqlite3.Connection) -> dict:
    """The choices of the lists in the student list (F1). A current coach or guild master who no
    longer has that role stays a choice, so that the cell is right (Data)."""
    people = lambda role, used: [
        dict(r, first=r["first_name"] or r["name"]) for r in conn.execute(
            f"SELECT id, name, first_name FROM staff WHERE {role} = 1 OR id IN ({used}) ORDER BY name COLLATE NOCASE")]
    return dict(options(conn),
                coaches=people("is_coach", "SELECT coach_id FROM students WHERE coach_id IS NOT NULL"),
                guild_masters=people("is_guild_master",
                                     "SELECT guild_master_id FROM student_guilds WHERE guild_master_id IS NOT NULL"))


def _one_of(conn: sqlite3.Connection, sql: str, value: str) -> int | None:
    """The id if `value` is an id in the result of `sql`, otherwise None."""
    if not value.isdigit():
        return None
    return int(value) if conn.execute(sql, (int(value),)).fetchone() else None


def save_inline(conn: sqlite3.Connection, student_id: int, field: str, raw: str) -> str | None:
    """F1, F4: one field of one student; empty clears. Returns an error message (Dutch) or None."""
    if field not in INLINE_FIELDS:
        return "Dit veld kun je hier niet wijzigen."
    if find(conn, student_id) is None:
        return "Deze student bestaat niet (meer)."
    value = raw.strip()
    if field == "guild":
        return _save_guild(conn, student_id, value)
    stored: object = None
    if value:
        if field == "semester":
            stored = int(value) if value.isdigit() and 1 <= int(value) <= 8 else None
        elif field == "squad_id":
            stored = _one_of(conn, "SELECT 1 FROM squads WHERE id = ?", value)
        elif field in ("track", "squad_role"):   # spec 024: an item of the list
            stored, _ = _item(conn, value, choices.TRACK if field == "track" else choices.SQUAD_ROLE)
        elif field == "coach_id":
            stored = _one_of(conn, "SELECT 1 FROM staff WHERE id = ? AND (is_coach = 1 OR id IN "
                                   "(SELECT coach_id FROM students WHERE id = %d))" % student_id, value)
        if stored is None:
            return "Kies een waarde uit de lijst."
    column = {"track": "track_id", "squad_role": "squad_role_id"}.get(field, field)
    with conn:
        conn.execute(f"UPDATE students SET {column} = ? WHERE id = ?", (stored, student_id))
        if field == "semester":
            choices.fill_track(conn, student_id)   # spec 025, F1
    return None


def _save_guild(conn: sqlite3.Connection, student_id: int, value: str) -> str | None:
    """F4: only with zero or one guild; another guild replaces it, without guild master."""
    current = student_guilds.of_student(conn, student_id)
    if len(current) > 1:
        return "Deze student heeft meer gildes. Wijzig ze via Student bewerken."
    guild_id = _one_of(conn, "SELECT 1 FROM guilds WHERE id = ?", value) if value else None
    if value and guild_id is None:
        return "Kies een gilde uit de lijst."
    if current and current[0]["guild_id"] == guild_id:
        return None   # the same guild: keep its guild master
    with conn:
        student_guilds.replace(conn, student_id, [(guild_id, None)] if guild_id else [])
    return None


def save_inline_guild_master(conn: sqlite3.Connection, student_id: int, guild_id: int, raw: str) -> str | None:
    """F5: the guild master of one guild of the student; empty clears."""
    if not conn.execute("SELECT 1 FROM student_guilds WHERE student_id = ? AND guild_id = ?",
                        (student_id, guild_id)).fetchone():
        return "Deze student heeft dit gilde niet (meer)."
    value = raw.strip()
    master = None
    if value:
        master = _one_of(conn, "SELECT 1 FROM staff WHERE id = ? AND (is_guild_master = 1 OR id IN (SELECT guild_master_id "
                               "FROM student_guilds WHERE student_id = %d AND guild_id = %d))" % (student_id, guild_id), value)
        if master is None:
            return "Kies een gildemeester uit de lijst."
    with conn:
        conn.execute("UPDATE student_guilds SET guild_master_id = ? WHERE student_id = ? AND guild_id = ?",
                     (master, student_id, guild_id))
    return None
