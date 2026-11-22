"""Bestanden bekijken (spec 038): the file of a piece of evidence, shown in the dashboard.

Portflow gives per version file a preview (`GET /portfolios/{pid}/evidence-version-files/{id}/preview-url`):
Word, Excel and PowerPoint as pdf, an image as itself; a video has no preview, so the original is used.
The links are signed S3 links (30 minutes, no token). The dashboard fetches the preview once and keeps
it in the folder `bestanden/` next to the database; a file not opened for 30 days is removed at start-up
(F7), and "Alles verwijderen" removes the folder (spec 014).

The Portflow token only goes to Portflow (portflow_api); the S3 links are fetched without it, without
following redirects, and are never stored or logged.
"""

import json
import os
import shutil
import sqlite3
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from . import portflow_api

CACHE_DIR = "bestanden"
KEEP_DAYS = 30
TIMEOUT_S = 60
MAX_BYTES = 1024 * 1024 * 1024   # 1 GB: a long video still fits, a runaway download does not
CHUNK = 1024 * 1024

# How a file is shown in the panel, by the MIME type Portflow gives in the evidence details.
OFFICE = {"application/msword", "application/vnd.ms-excel", "application/vnd.ms-powerpoint"}
# What the dashboard serves inline. Not svg or html: those could run scripts in the dashboard.
SERVED = {"application/pdf", "image/png", "image/jpeg", "image/gif", "image/webp", "image/bmp",
          "video/mp4", "video/webm", "video/quicktime", "video/ogg"}
EXTENSIONS = {"application/pdf": ".pdf", "image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif",
              "image/webp": ".webp", "image/bmp": ".bmp", "video/mp4": ".mp4", "video/webm": ".webm",
              "video/quicktime": ".mov", "video/ogg": ".ogv"}

NOT_SHOWN = "Dit bestand kan niet in het dashboard worden getoond."


class FileError(Exception):
    """`message` is shown to the user (Dutch)."""

    def __init__(self, message: str, status: int = 404):
        super().__init__(message)
        self.message = message
        self.status = status


def display(mime: str) -> str:
    """F1, F5, F5a: how the panel shows a file: pdf (also Word, Excel, PowerPoint), image, video or none."""
    mime = (mime or "").lower()
    if mime == "application/pdf" or mime in OFFICE or mime.startswith("application/vnd.openxmlformats-officedocument.") \
            or mime.startswith("application/vnd.oasis.opendocument."):
        return "pdf"
    if mime in SERVED and mime.startswith("image/"):
        return "image"
    if mime in SERVED and mime.startswith("video/"):
        return "video"
    return ""


def files_of(version: dict) -> list[dict]:
    """F3: the files of the latest version of a piece of evidence (from the evidence details)."""
    result = []
    for f in version.get("files") or []:
        if not isinstance(f, dict) or not isinstance(f.get("file"), dict) or not str(f.get("id") or "").isdigit():
            continue
        mime = str(f["file"].get("type") or "")
        result.append({"id": int(f["id"]), "name": str(f["file"].get("file_name") or f.get("display_name") or "bestand"),
                       "mime": mime, "display": display(mime)})
    return result


def cache_dir(database: str | Path) -> Path:
    return Path(database).parent / CACHE_DIR


def is_portflow_storage(url: str) -> bool:
    """Only signed links of Portflow's own storage are followed."""
    parsed = urlparse(url or "")
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and host.startswith("portflow-") and host.endswith(".amazonaws.com")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def _student_portfolio(conn: sqlite3.Connection, student_id: int, portfolio_id: int) -> bool:
    return conn.execute("SELECT 1 FROM student_portfolios WHERE student_id = ? AND portfolio_id = ?",
                        (student_id, portfolio_id)).fetchone() is not None


def links(conn: sqlite3.Connection, token: str | None, student_id: int, portfolio_id: int, file_id: int, *,
          api=None) -> dict:
    """The answer of preview-url for a file of this student. Raises FileError."""
    if not _student_portfolio(conn, student_id, portfolio_id):
        raise FileError("Dit bestand hoort niet bij deze student.")
    if not token:
        raise FileError("Niet verbonden met Portflow: het bestand kan niet worden opgehaald.", 503)
    status, info = (api or portflow_api).preview_url(token, portfolio_id, file_id)
    if status == 401:
        raise FileError("Portflow accepteert de verbinding niet meer; verbind opnieuw.", 503)
    if status == 0:
        raise FileError("Portflow is niet bereikbaar; probeer het later opnieuw.", 503)
    if status != 200 or not isinstance(info, dict):
        raise FileError("Dit bestand is niet (meer) te openen; misschien is het niet meer gedeeld.")
    return info


def _shown_link(info: dict) -> str | None:
    """F1, F5: the preview (pdf) or the image itself; for a video the original."""
    if info.get("preview_state") == "available":
        for key in ("preview_url", "object_url"):
            if isinstance(info.get(key), str):
                return info[key]
    if info.get("mime_class") == "video" and isinstance(info.get("download_url"), str):
        return info["download_url"]
    return None


def _download(url: str, target: Path) -> str:
    """Fetch a signed link (no token, no redirects) into target; returns the MIME type."""
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    partial = target.with_name(target.name + ".deel")
    try:
        with _opener.open(request, timeout=TIMEOUT_S) as response:
            mime = (response.headers.get_content_type() or "").lower()
            if mime not in SERVED:
                raise FileError(NOT_SHOWN, 415)
            size = 0
            with partial.open("wb") as out:
                while chunk := response.read(CHUNK):
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise FileError("Dit bestand is te groot om in het dashboard te tonen.", 413)
                    out.write(chunk)
        partial.replace(target)
        return mime
    except (urllib.error.URLError, TimeoutError, OSError):
        raise FileError("Het bestand kon niet worden opgehaald; probeer het later opnieuw.", 503) from None
    finally:
        partial.unlink(missing_ok=True)


def shown_file(database: str, conn: sqlite3.Connection, token: str | None, student_id: int, portfolio_id: int,
               file_id: int, *, api=None, download=None) -> tuple[Path, str]:
    """F1, F5, F7: (path, MIME type) of the file to show, from the cache or fetched now. Raises FileError."""
    folder = cache_dir(database)
    meta = folder / f"{portfolio_id}-{file_id}.json"
    if meta.exists():
        try:
            info = json.loads(meta.read_text(encoding="utf-8"))
            path = folder / info["file"]
            if path.exists() and info["mime"] in SERVED and _student_portfolio(conn, student_id, portfolio_id):
                now = time.time()
                os.utime(meta, (now, now))   # F7: opened now
                return path, info["mime"]
        except (OSError, ValueError, KeyError, TypeError):
            pass
    link = _shown_link(links(conn, token, student_id, portfolio_id, file_id, api=api))
    if not link or not is_portflow_storage(link):
        raise FileError(NOT_SHOWN, 415)
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"{portfolio_id}-{file_id}"
    target = folder / f"{stem}.bestand"
    mime = (download or _download)(link, target)
    path = target.with_suffix(EXTENSIONS.get(mime, ".bestand"))
    target.replace(path)
    meta.write_text(json.dumps({"file": path.name, "mime": mime}), encoding="utf-8")
    return path, mime


def original_link(conn: sqlite3.Connection, token: str | None, student_id: int, portfolio_id: int, file_id: int, *,
                  api=None) -> str:
    """F4: a fresh signed link to the original (a download, not stored). Raises FileError."""
    link = links(conn, token, student_id, portfolio_id, file_id, api=api).get("download_url")
    if not isinstance(link, str) or not is_portflow_storage(link):
        raise FileError("Dit bestand kan niet worden gedownload.")
    return link


def clean_up(database: str | Path, days: int = KEEP_DAYS, now: float | None = None) -> int:
    """F7: remove files not opened for `days` days (and leftovers of an interrupted download)."""
    folder = cache_dir(database)
    if not folder.is_dir():
        return 0
    limit = (now or time.time()) - days * 24 * 3600
    removed = 0
    for meta in folder.glob("*.json"):
        try:
            if meta.stat().st_mtime >= limit:
                continue
            name = json.loads(meta.read_text(encoding="utf-8")).get("file")
            if isinstance(name, str) and name and "/" not in name and "\\" not in name:
                (folder / name).unlink(missing_ok=True)
        except (OSError, ValueError, AttributeError):
            pass
        meta.unlink(missing_ok=True)
        removed += 1
    known = {meta.stem for meta in folder.glob("*.json")}
    for path in folder.iterdir():
        if path.suffix != ".json" and path.name.split(".")[0] not in known:
            try:
                if path.stat().st_mtime < (now or time.time()) - 3600:   # not one being downloaded right now
                    path.unlink()
            except OSError:
                pass
    return removed


def remove_all(database: str | Path) -> None:
    """Spec 014: "Alles verwijderen" also removes the kept files."""
    shutil.rmtree(cache_dir(database), ignore_errors=True)
