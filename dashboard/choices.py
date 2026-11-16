"""Choice lists (spec 024): simple ordered lists of items with a code and a description.

Used for Invulling (students.track_id), Rol in de squad (students.squad_role_id) and the
list of each choice column (custom_values.value holds the item id). The Open-ICT values are
taken from docs/gegevensmodel.md and docs/begrippen.md; this is the only place in the code.
"""

import sqlite3

TRACK, SQUAD_ROLE, COLUMN = "track", "squad_role", "column"
LIST_NAMES = {TRACK: "Invulling", SQUAD_ROLE: "Rol in de squad"}
ANCHORS = {TRACK: "invulling", SQUAD_ROLE: "rol"}   # spec 024, G4: the pencils go here

# L5, L6: the Open-ICT standard (code, description).
STANDARD = {
    TRACK: [("Open projecten", "Open Projecten (jaar 2)"),
            ("Open innovatieproject", "Open Innovatieproject (semester 5, 6 of 7)"),
            ("Stage", "Stage (semester 5, 6 of 7)"),
            ("Minor", "Minor (semester 6)"),
            ("Afstuderen", "Afstuderen (semester 8)")],
    SQUAD_ROLE: [("PO", "product owner"), ("SM", "scrum master"),
                 ("2ePO", "tweede product owner"), ("2eSM", "tweede scrum master")],
}
# Spec 025, F1: an empty invulling follows from these semesters (docs/gegevensmodel.md#student).
SEMESTER_TRACKS = {3: "Open projecten", 4: "Open projecten", 8: "Afstuderen"}
STAGE = "Stage"   # spec 025, F4: shown as "(Stage)" at Project

# Spec 013, F7 and spec 024, E1: the Excel import may add these to Invulling.
IMPORT_TRACKS = {"stage": "Stage", "minor": "Minor"}


# Lists -------------------------------------------------------------------------------------

def ensure_lists(conn: sqlite3.Connection) -> None:
    """Invulling and Rol always exist; a new (or emptied) database gets the Open-ICT items (L6)."""
    for kind in (TRACK, SQUAD_ROLE):
        if conn.execute("SELECT 1 FROM choice_lists WHERE kind = ?", (kind,)).fetchone() is None:
            list_id = conn.execute("INSERT INTO choice_lists (kind) VALUES (?)", (kind,)).lastrowid
            add_standard(conn, list_id)


def list_id(conn: sqlite3.Connection, kind: str) -> int:
    row = conn.execute("SELECT id FROM choice_lists WHERE kind = ?", (kind,)).fetchone()
    if row is None:
        ensure_lists(conn)
        row = conn.execute("SELECT id FROM choice_lists WHERE kind = ?", (kind,)).fetchone()
    return row[0]


def column_list_id(conn: sqlite3.Connection, column_id: int) -> int:
    """K2: the list of a choice column, made when needed."""
    row = conn.execute("SELECT id FROM choice_lists WHERE column_id = ?", (column_id,)).fetchone()
    if row:
        return row[0]
    return conn.execute("INSERT INTO choice_lists (kind, column_id) VALUES (?, ?)", (COLUMN, column_id)).lastrowid


def column_items(conn: sqlite3.Connection, column_id: int) -> list[dict]:
    """The items of a choice column (read only; empty if the column has no list)."""
    row = conn.execute("SELECT id FROM choice_lists WHERE column_id = ?", (column_id,)).fetchone()
    return items(conn, row[0]) if row else []


def items(conn: sqlite3.Connection, list_id_: int) -> list[dict]:
    return [dict(r, label=r["description"] or r["code"]) for r in conn.execute(
        "SELECT id, code, description, position FROM choice_items WHERE list_id = ? ORDER BY position, id", (list_id_,))]


def kind_items(conn: sqlite3.Connection, kind: str) -> list[dict]:
    return items(conn, list_id(conn, kind))


def usage(conn: sqlite3.Connection, item_id: int) -> int:
    """The number of students with this item (L1, L4)."""
    row = conn.execute("SELECT l.kind, l.column_id FROM choice_items i JOIN choice_lists l ON l.id = i.list_id "
                       "WHERE i.id = ?", (item_id,)).fetchone()
    if row is None:
        return 0
    if row["kind"] == COLUMN:
        return conn.execute("SELECT COUNT(*) FROM custom_values WHERE column_id = ? AND value = ?",
                            (row["column_id"], str(item_id))).fetchone()[0]
    column = "track_id" if row["kind"] == TRACK else "squad_role_id"
    return conn.execute(f"SELECT COUNT(*) FROM students WHERE {column} = ?", (item_id,)).fetchone()[0]


def all_lists(conn: sqlite3.Connection) -> list[dict]:
    """L1: Invulling, Rol, then one list per choice column (in column order)."""
    result = []
    for kind in (TRACK, SQUAD_ROLE):
        lid = list_id(conn, kind)
        result.append({"id": lid, "kind": kind, "name": LIST_NAMES[kind], "anchor": ANCHORS[kind],
                       "standard": True, "entries": items(conn, lid)})
    for column in conn.execute("SELECT c.id, c.name, l.id AS list_id FROM custom_columns c "
                               "JOIN choice_lists l ON l.column_id = c.id ORDER BY c.position, c.id").fetchall():
        lid = column["list_id"]
        result.append({"id": lid, "kind": COLUMN, "name": column["name"], "anchor": f"kolom-{column['id']}",
                       "standard": False, "entries": items(conn, lid)})
    for lst in result:
        for item in lst["entries"]:
            item["students"] = usage(conn, item["id"])
    return result


def find_list(conn: sqlite3.Connection, list_id_: int) -> dict | None:
    return next((l for l in all_lists(conn) if l["id"] == list_id_), None)


def find_item(conn: sqlite3.Connection, item_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM choice_items WHERE id = ?", (item_id,)).fetchone()
    return dict(row) if row else None


# Items (L2-L5) -----------------------------------------------------------------------------------

def _code_taken(conn: sqlite3.Connection, list_id_: int, code: str, item_id: int | None) -> bool:
    return any(i["code"].casefold() == code.casefold() and i["id"] != item_id for i in items(conn, list_id_))


def validate(conn: sqlite3.Connection, list_id_: int, code: str, description: str,
             item_id: int | None = None) -> tuple[dict | None, str | None]:
    code, description = " ".join(code.split()), " ".join(description.split())
    if not code:
        return None, "Vul een code in."
    if len(code) > 40:
        return None, "Houd de code kort (hooguit 40 tekens)."
    if _code_taken(conn, list_id_, code, item_id):
        return None, f"De code {code} staat al in deze lijst."
    return {"code": code, "description": description}, None


def add_item(conn: sqlite3.Connection, list_id_: int, code: str, description: str = "") -> int:
    position = conn.execute("SELECT COALESCE(MAX(position), -1) + 1 FROM choice_items WHERE list_id = ?",
                            (list_id_,)).fetchone()[0]
    return conn.execute("INSERT INTO choice_items (list_id, code, description, position) VALUES (?, ?, ?, ?)",
                        (list_id_, code, description, position)).lastrowid


def update_item(conn: sqlite3.Connection, item_id: int, code: str, description: str) -> None:
    with conn:
        conn.execute("UPDATE choice_items SET code = ?, description = ? WHERE id = ?", (code, description, item_id))


def move_item(conn: sqlite3.Connection, item_id: int, step: int) -> None:
    """L3: one place up (-1) or down (+1)."""
    item = find_item(conn, item_id)
    if item is None:
        return
    order = [i["id"] for i in items(conn, item["list_id"])]
    index = order.index(item_id)
    other = index + step
    if 0 <= other < len(order):
        order[index], order[other] = order[other], order[index]
    with conn:
        conn.executemany("UPDATE choice_items SET position = ? WHERE id = ?", [(p, i) for p, i in enumerate(order)])


def delete_item(conn: sqlite3.Connection, item_id: int) -> None:
    """L4: students lose the value (ON DELETE SET NULL); cells of a choice column are emptied."""
    row = conn.execute("SELECT l.column_id FROM choice_items i JOIN choice_lists l ON l.id = i.list_id WHERE i.id = ?",
                       (item_id,)).fetchone()
    with conn:
        if row and row["column_id"] is not None:
            conn.execute("DELETE FROM custom_values WHERE column_id = ? AND value = ?", (row["column_id"], str(item_id)))
        conn.execute("DELETE FROM choice_items WHERE id = ?", (item_id,))


def add_standard(conn: sqlite3.Connection, list_id_: int) -> int:
    """L5: the Open-ICT items that are missing (compared on code); returns the number added."""
    kind = conn.execute("SELECT kind FROM choice_lists WHERE id = ?", (list_id_,)).fetchone()[0]
    have = {i["code"].casefold() for i in items(conn, list_id_)}
    added = 0
    for code, description in STANDARD.get(kind, []):
        if code.casefold() not in have:
            add_item(conn, list_id_, code, description)
            added += 1
    return added


# Looking up (E1, L6) ------------------------------------------------------------------------------

def find_by_text(conn: sqlite3.Connection, list_id_: int, text: str) -> dict | None:
    """An item whose code (or else description) matches, ignoring case and spaces."""
    key = " ".join(text.split()).casefold()
    found = items(conn, list_id_)
    return (next((i for i in found if i["code"].casefold() == key), None)
            or next((i for i in found if i["description"].casefold() == key), None))


def find_or_add(conn: sqlite3.Connection, kind: str, code: str) -> int:
    """E1 and L6: the item with this code, added at the end if it is missing."""
    lid = list_id(conn, kind)
    item = find_by_text(conn, lid, code)
    return item["id"] if item else add_item(conn, lid, " ".join(code.split()))


def migrate_student_texts(conn: sqlite3.Connection) -> None:
    """L6: the old text columns students.track and students.squad_role become references."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(students)")}
    if "track_id" not in columns:
        conn.execute("ALTER TABLE students ADD COLUMN track_id INTEGER REFERENCES choice_items(id) ON DELETE SET NULL")
    if "squad_role_id" not in columns:
        conn.execute("ALTER TABLE students ADD COLUMN squad_role_id INTEGER REFERENCES choice_items(id) ON DELETE SET NULL")
    for old, new, kind in (("track", "track_id", TRACK), ("squad_role", "squad_role_id", SQUAD_ROLE)):
        if old not in columns:
            continue
        for (text,) in conn.execute(f"SELECT DISTINCT {old} FROM students WHERE {old} IS NOT NULL AND trim({old}) != ''").fetchall():
            conn.execute(f"UPDATE students SET {new} = ? WHERE {old} = ?", (find_or_add(conn, kind, text), text))
        conn.execute(f"ALTER TABLE students DROP COLUMN {old}")


# Invulling from the semester (spec 025) -----------------------------------------------------------

def track_for_semester(conn: sqlite3.Connection, semester, track_id) -> int | None:
    """F1, F3: the item id for an empty invulling at this semester (added to the list if missing),
    or None when nothing changes (the invulling is filled, or the semester has no rule)."""
    if track_id or not str(semester or "").isdigit() or int(semester) not in SEMESTER_TRACKS:
        return None
    return find_or_add(conn, TRACK, SEMESTER_TRACKS[int(semester)])


def fill_track(conn: sqlite3.Connection, student_id: int) -> bool:
    """F1 for a saved student; True if the invulling was filled."""
    row = conn.execute("SELECT semester, track_id FROM students WHERE id = ?", (student_id,)).fetchone()
    item = track_for_semester(conn, row[0], row[1]) if row else None
    if item is None:
        return False
    conn.execute("UPDATE students SET track_id = ? WHERE id = ?", (item, student_id))
    return True
