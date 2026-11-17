"""Everything away: back to the state right after the first connection (spec 014).
The Portflow connection stays (token, browser profile and its settings).
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from . import choices, db
from .portflow_connection import (S_ALWAYS_VISIBLE, S_CANVAS_URL, S_LAST_REFRESH, S_LAST_REFRESH_KIND,
                                  S_PORTFOLIO_ID, S_USER_NAME)
from .portflow_token import TOKEN_KEY, remove_token

CONFIRM_WORD = "VERWIJDEREN"
BACKUP_DIR = "reservekopieen"

# F5: the settings of the Portflow connection stay.
KEPT_SETTINGS = (TOKEN_KEY, S_CANVAS_URL, S_ALWAYS_VISIBLE, S_PORTFOLIO_ID, S_USER_NAME, S_LAST_REFRESH, S_LAST_REFRESH_KIND)

# F2: what disappears, with a count (table, Dutch label).
SUMMARY = [("students", "studenten"), ("evaluations", "evaluaties (bewaarde kopie uit Portflow)"),
           ("received_requests", "evaluatieverzoeken aan jou (bewaarde kopie uit Portflow)"),
           ("squads", "projecten"), ("semesters", "semesters"),
           ("guilds", "gildes"), ("staff", "coaches en gildemeesters"), ("custom_columns", "eigen kolommen"),
           ("settings", "instellingen")]


class ResetError(Exception):
    """Nothing was deleted; `message` is shown to the user (Dutch)."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _kept(table: str) -> str:
    """WHERE clause for the rows that stay (F5)."""
    if table != "settings":
        return "0"
    return "key IN (" + ", ".join("?" * len(KEPT_SETTINGS)) + ")"


def summary(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    return [(label, conn.execute(f"SELECT COUNT(*) FROM {table} WHERE NOT ({_kept(table)})",
                                 KEPT_SETTINGS if table == "settings" else ()).fetchone()[0])
            for table, label in SUMMARY]


def is_busy(app) -> bool:
    """F7: not while logging in, refreshing the token or fetching."""
    return bool(app.extensions["portflow"].status()["busy"] or app.extensions["fetcher"].running)


def backup(database: str, now: datetime | None = None) -> Path:
    """F4: a consistent copy with SQLite's backup function, in data/reservekopieen/, without the token."""
    folder = Path(database).parent / BACKUP_DIR
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"dashboard-{(now or datetime.now()).strftime('%Y-%m-%d-%H%M%S')}.sqlite3"
    source, copy = db.connect(database), sqlite3.connect(target)
    try:
        source.backup(copy)
    finally:
        copy.close()
        source.close()
    remove_token(target)
    return target


def _empty_database(database: str) -> None:
    conn = db.connect(database)
    try:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
        conn.execute("PRAGMA foreign_keys = OFF")
        with conn:
            for table in tables:
                conn.execute(f'DELETE FROM "{table}" WHERE NOT ({_kept(table)})',
                             KEPT_SETTINGS if table == "settings" else ())
        conn.execute("PRAGMA foreign_keys = ON")
        with conn:
            choices.ensure_lists(conn)   # spec 024: Invulling and Rol start with the Open-ICT items again
        conn.execute("VACUUM")  # really remove the old pages from the file
    finally:
        conn.close()


def reset_all(app) -> Path:
    """F4-F6. Returns the path of the backup. Raises ResetError if nothing was deleted."""
    if is_busy(app):
        raise ResetError("Wacht tot het inloggen of ophalen klaar is.")
    database = app.config["DATABASE"]
    try:
        copy = backup(database)
    except (OSError, sqlite3.Error):
        raise ResetError("De reservekopie is niet gelukt; er is niets verwijderd.") from None
    _empty_database(database)
    connection = app.extensions["portflow"]   # F5: the connection stays
    if connection.user_name:   # as after the first connection, the user is on Coaches (spec 007, F2a)
        db.add_user_as_coach(database, connection.user_name)
    app.extensions.get("excel_imports", {}).clear()
    fetcher = app.extensions["fetcher"]
    fetcher.done = fetcher.total = 0
    return copy
