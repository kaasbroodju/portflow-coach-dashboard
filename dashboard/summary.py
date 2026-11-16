"""The management bar on top of every Beheer page (spec 027): at most three counts, always in
the same order: the page's own items, the students (or evaluations) with them, and what still
needs attention. Labels are Dutch: they are shown to the user."""

import sqlite3


def _count(conn: sqlite3.Connection, sql: str) -> int:
    return conn.execute(sql).fetchone()[0]


def _item(value: int, one: str, many: str, attention: bool = False, extra: dict | None = None) -> dict:
    """F2: a bold number with a short label; an attention count is highlighted when above 0."""
    return {"value": value, "label": one if value == 1 else many,
            "attention": attention and value > 0, "extra": extra}


def students(conn: sqlite3.Connection) -> list[dict]:
    return [
        _item(_count(conn, "SELECT COUNT(*) FROM students"), "student", "studenten"),
        _item(_count(conn, "SELECT COUNT(*) FROM students WHERE is_hidden = 1"), "verborgen", "verborgen"),
        _item(_count(conn, "SELECT COUNT(*) FROM students WHERE squad_id IS NULL"),
              "zonder project", "zonder project", attention=True),
    ]


def semesters(conn: sqlite3.Connection) -> list[dict]:
    active = _count(conn, "SELECT COUNT(DISTINCT semester) FROM students WHERE semester IS NOT NULL")
    return [
        _item(_count(conn, "SELECT COUNT(*) FROM semesters"), "semester", "semesters",
              extra={"value": active, "label": "actief"}),
        _item(_count(conn, "SELECT COUNT(*) FROM students WHERE semester IS NOT NULL"), "student", "studenten"),
        _item(_count(conn, "SELECT COUNT(*) FROM students WHERE semester IS NULL"),
              "zonder semester", "zonder semester", attention=True),
    ]


def guilds(conn: sqlite3.Connection) -> list[dict]:
    return [
        _item(_count(conn, "SELECT COUNT(*) FROM guilds"), "gilde", "gildes"),
        _item(_count(conn, "SELECT COUNT(DISTINCT student_id) FROM student_guilds"), "student", "studenten"),
        _item(_count(conn, "SELECT COUNT(*) FROM students WHERE id NOT IN (SELECT student_id FROM student_guilds)"),
              "zonder gilde", "zonder gilde", attention=True),
    ]


def staff(conn: sqlite3.Connection, role: str, people: int, evaluations: int) -> list[dict]:
    """Coaches or guild masters; `people` and `evaluations` come from the page's own list."""
    evaluations_item = _item(evaluations, "evaluatie telt mee", "evaluaties tellen mee")
    if role == "coach":
        return [
            _item(people, "coach", "coaches"),
            evaluations_item,
            _item(_count(conn, "SELECT COUNT(*) FROM students WHERE coach_id IS NULL"),
                  "student zonder coach", "studenten zonder coach", attention=True),
        ]
    without = _count(conn, "SELECT COUNT(*) FROM guilds WHERE id NOT IN ("
                           "SELECT sg.guild_id FROM staff_guilds sg JOIN staff s ON s.id = sg.staff_id "
                           "WHERE s.is_guild_master = 1)")
    return [
        _item(people, "gildemeester", "gildemeesters"),
        evaluations_item,
        _item(without, "gilde zonder gildemeester", "gildes zonder gildemeester", attention=True),
    ]


def projects(conn: sqlite3.Connection) -> list[dict]:
    return [
        _item(_count(conn, "SELECT COUNT(DISTINCT squad_id) FROM students WHERE squad_id IS NOT NULL"),
              "actief project", "actieve projecten"),
        _item(_count(conn, "SELECT COUNT(*) FROM students WHERE squad_id IS NOT NULL"), "student", "studenten"),
        _item(_count(conn, "SELECT COUNT(*) FROM students WHERE squad_id IS NULL"),
              "zonder project", "zonder project", attention=True),
    ]


def columns(conn: sqlite3.Connection) -> list[dict]:
    return [_item(_count(conn, "SELECT COUNT(*) FROM custom_columns"), "eigen kolom", "eigen kolommen")]


def choice_lists(lists: list[dict]) -> list[dict]:
    return [
        _item(len(lists), "keuzelijst", "keuzelijsten"),
        _item(sum(len(l["entries"]) for l in lists), "keuze", "keuzes"),
    ]
