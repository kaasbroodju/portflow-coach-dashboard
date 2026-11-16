"""The Portflow bearer token: reading its expiry, and keeping it in the database.

The token is a secret. It is only stored in the local database (settings table,
see CLAUDE.md), never in backups, and never shown in the browser, in logs or in
error messages.
"""

import base64
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from . import db

TOKEN_KEY = "portflow_token"   # key in the settings table


def decode_payload(token: str) -> dict | None:
    """Return the (unverified) JWT payload, or None if this is not a JWT."""
    parts = token.strip().split(".")
    if len(parts) != 3:
        return None
    try:
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
    except (ValueError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def expires_at(token: str) -> datetime | None:
    """Expiry time (UTC) from the 'exp' claim, or None if unknown."""
    payload = decode_payload(token) or {}
    exp = payload.get("exp")
    if not isinstance(exp, (int, float)):
        return None
    return datetime.fromtimestamp(exp, tz=timezone.utc)


class TokenStore:
    """Reads and writes the token in the settings table of the database."""

    def __init__(self, database: Path | str):
        self.database = str(database)

    def read(self) -> str | None:
        return db.get_setting(self.database, TOKEN_KEY) or None

    def save(self, token: str) -> None:
        db.set_setting(self.database, TOKEN_KEY, token)
        os.chmod(self.database, 0o600)  # readable for the user only

    def delete(self) -> None:
        remove_token(self.database)


def remove_token(database: Path | str) -> None:
    """Delete the token from a database file (also used to clean a backup copy)."""
    conn = sqlite3.connect(str(database))
    try:
        with conn:
            conn.execute("DELETE FROM settings WHERE key = ?", (TOKEN_KEY,))
    finally:
        conn.close()
