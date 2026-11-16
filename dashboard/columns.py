"""Custom columns (spec 024, K1-K5): add, edit, order and delete. Values are filled in the tables."""

import sqlite3

from . import choices
from .skills import SKILLS

TYPES = [("percentage", "Percentage"), ("text", "Vrije tekst"), ("choice", "Keuzelijst")]
TYPE_LABELS = dict(TYPES)


def all_columns(conn: sqlite3.Connection) -> list[dict]:
    """K1: in their order, with the number of students with a value."""
    counts = {r[0]: r[1] for r in conn.execute("SELECT column_id, COUNT(*) FROM custom_values GROUP BY column_id")}
    return [dict(r, type_label=TYPE_LABELS.get(r["type"], r["type"]), students=counts.get(r["id"], 0))
            for r in conn.execute("SELECT * FROM custom_columns ORDER BY position, id")]


def find(conn: sqlite3.Connection, column_id: int) -> dict | None:
    return next((c for c in all_columns(conn) if c["id"] == column_id), None)


def validate(conn: sqlite3.Connection, code: str, name: str, description: str, kind: str | None,
             column_id: int | None = None) -> tuple[dict | None, str | None]:
    """K2, K3. `kind` is None when editing: the type does not change."""
    code, name, description = " ".join(code.split()), " ".join(name.split()), description.strip()
    if not code:
        return None, "Vul een code in."
    if len(code) > 12:
        return None, "Houd de code kort (hooguit 12 tekens); hij staat boven de kolom."
    if not name:
        return None, "Vul een naam in."
    if code.casefold() in {s.casefold() for s in SKILLS}:
        return None, f"{code} is al een vaardigheid. Kies een andere code."
    if any(c["code"].casefold() == code.casefold() and c["id"] != column_id for c in all_columns(conn)):
        return None, f"Er is al een kolom met de code {code}."
    if kind is not None and kind not in TYPE_LABELS:
        return None, "Kies een type."
    return {"code": code, "name": name, "description": description, "type": kind}, None


def create(conn: sqlite3.Connection, values: dict) -> int:
    """K2: a new column comes last; a choice column gets its own (empty) list."""
    with conn:
        position = conn.execute("SELECT COALESCE(MAX(position), -1) + 1 FROM custom_columns").fetchone()[0]
        column_id = conn.execute("INSERT INTO custom_columns (code, name, description, type, position) "
                                 "VALUES (?, ?, ?, ?, ?)",
                                 (values["code"], values["name"], values["description"], values["type"], position)).lastrowid
        if values["type"] == "choice":
            choices.column_list_id(conn, column_id)
    return column_id


def update(conn: sqlite3.Connection, column_id: int, values: dict) -> None:
    """K3: code, name and description; never the type."""
    with conn:
        conn.execute("UPDATE custom_columns SET code = ?, name = ?, description = ? WHERE id = ?",
                     (values["code"], values["name"], values["description"], column_id))


def move(conn: sqlite3.Connection, column_id: int, step: int) -> None:
    """K4: one place to the left (-1) or right (+1)."""
    order = [c["id"] for c in all_columns(conn)]
    if column_id not in order:
        return
    index = order.index(column_id)
    other = index + step
    if 0 <= other < len(order):
        order[index], order[other] = order[other], order[index]
    with conn:
        conn.executemany("UPDATE custom_columns SET position = ? WHERE id = ?", [(p, i) for p, i in enumerate(order)])


def delete(conn: sqlite3.Connection, column_id: int) -> None:
    """K5: values and the list go along (foreign keys)."""
    with conn:
        conn.execute("DELETE FROM custom_columns WHERE id = ?", (column_id,))
