"""New versions on GitHub (spec 020, U1-U5, R6).

The check asks GitHub for the latest release; nothing is sent but the request itself (with the
version in the User-Agent). Updating is only possible for an installed dashboard (paths.py): the
new code is downloaded, checked against its SHA-256 and unpacked next to the old code; then the
app starts update_swap.py and stops. That script swaps the folders, lets uv update the packages
and starts the new version (or the old one again when something fails).
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from markupsafe import Markup, escape

from . import db, paths, reset
from .version import VERSION

REPOSITORY = "petersnoek-hu/portflow-coach-dashboard"
LATEST_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
ZIP_NAME = "portflow-coach-dashboard.zip"
SHA_NAME = ZIP_NAME + ".sha256"
CHECK_EVERY_S = 24 * 60 * 60
FIRST_CHECK_AFTER_S = 5
TIMEOUT_S = 10

S_CHECK = "update_check"          # U4: "0" switches the check off
S_DISMISSED = "update_dismissed"  # U2: "Later" hides the bar until a newer version
S_LATEST = "update_latest"        # the last answer of GitHub (JSON)


def parse_version(text: str | None) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", (text or "").strip())
    return tuple(int(part) for part in match.groups()) if match else None


def is_newer(candidate: str | None, current: str = VERSION) -> bool:
    new, old = parse_version(candidate), parse_version(current)
    return bool(new and old and new > old)


def release_from_github(data: dict) -> dict | None:
    """The fields the app needs from GET /releases/latest."""
    version = parse_version(data.get("tag_name"))
    if version is None:
        return None
    assets = {a.get("name"): a.get("browser_download_url") for a in data.get("assets") or [] if isinstance(a, dict)}
    return {
        "version": ".".join(map(str, version)),
        "notes": str(data.get("body") or ""),
        "url": str(data.get("html_url") or f"https://github.com/{REPOSITORY}/releases/latest"),
        "zip_url": assets.get(ZIP_NAME),
        "sha_url": assets.get(SHA_NAME),
    }


def notes_html(text: str) -> Markup:
    """R6: the release note (Markdown from GitHub) as simple, escaped HTML: headings, lists, bold."""
    def inline(line: str) -> str:
        return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", str(escape(line)))

    parts, items, paragraph = [], [], []

    def flush():
        if items:
            parts.append("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")
            items.clear()
        if paragraph:
            parts.append("<p>" + " ".join(paragraph) + "</p>")
            paragraph.clear()

    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if not line:
            flush()
        elif line.startswith("#"):
            flush()
            parts.append(f"<h3>{inline(line.lstrip('#').strip())}</h3>")
        elif line[:2] in ("- ", "* "):
            if paragraph:
                flush()
            items.append(inline(line[2:]))
        else:
            if items:
                flush()
            paragraph.append(inline(line))
    flush()
    return Markup("\n".join(parts))


def _get(url: str, timeout: float = TIMEOUT_S) -> bytes:
    request = urllib.request.Request(url, headers={
        "User-Agent": f"portflow-coach-dashboard/{VERSION}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UpdateError(Exception):
    """Updating stopped; `message` is shown to the user (Dutch). The old version keeps working."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class Updater:
    def __init__(self, database: str, *, fetch=_get, project_dir: Path = paths.PROJECT_DIR, spawn=None):
        self.database = database
        self.fetch = fetch
        self.project_dir = project_dir
        self.spawn = spawn or (lambda work: threading.Thread(target=work, daemon=True).start())
        self.state = {"busy": False, "step": "", "error": "", "attempt": ""}
        self._lock = threading.Lock()

    # Checking (U1, U2, U4) ------------------------------------------------------------------

    def enabled(self) -> bool:
        return db.get_setting(self.database, S_CHECK) != "0"

    def set_enabled(self, on: bool) -> None:
        db.set_setting(self.database, S_CHECK, "1" if on else "0")

    def check_now(self) -> dict | None:
        """U1: ask GitHub; without internet (or any other failure) nothing happens."""
        try:
            data = json.loads(self.fetch(LATEST_URL))
        except (OSError, ValueError, urllib.error.URLError):
            return None
        release = release_from_github(data) if isinstance(data, dict) else None
        if release:
            db.set_setting(self.database, S_LATEST, json.dumps(dict(release, checked_at=_now())))
        return release

    def start_checking(self) -> None:
        def loop():
            time.sleep(FIRST_CHECK_AFTER_S)
            while True:
                if self.enabled():
                    self.check_now()
                time.sleep(CHECK_EVERY_S)
        threading.Thread(target=loop, daemon=True).start()

    def latest(self) -> dict | None:
        try:
            data = json.loads(db.get_setting(self.database, S_LATEST) or "null")
        except ValueError:
            return None
        return data if isinstance(data, dict) else None

    def available(self) -> dict | None:
        """U2: the newer release to announce, unless switched off or put off with "Later"."""
        latest = self.latest()
        if not self.enabled() or not latest or not is_newer(latest.get("version")):
            return None
        if db.get_setting(self.database, S_DISMISSED) == latest["version"]:
            return None
        return latest

    def dismiss(self) -> None:
        latest = self.latest()
        if latest:
            db.set_setting(self.database, S_DISMISSED, latest["version"])

    def can_update(self) -> bool:
        """U5: only an installed dashboard updates itself; a git checkout uses git."""
        return paths.install_info(self.project_dir) is not None

    # Updating (U3) --------------------------------------------------------------------------------

    def update_dir(self) -> Path:
        return Path(self.database).parent / "bijwerken"

    def result(self) -> dict | None:
        """What update_swap.py wrote after the last attempt."""
        try:
            return json.loads((self.update_dir() / "resultaat.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def start_update(self, port: int, shutdown) -> bool:
        latest = self.available() or self.latest()
        if not self.can_update() or not latest or not is_newer(latest.get("version")):
            return False
        with self._lock:
            if self.state["busy"]:
                return False
            self.state = {"busy": True, "step": "Reservekopie maken", "error": "", "attempt": uuid.uuid4().hex}
        self.spawn(lambda: self._update(latest, port, shutdown))
        return True

    def _update(self, latest: dict, port: int, shutdown) -> None:
        try:
            self._prepare(latest, port)
        except UpdateError as error:
            self.state.update(busy=False, error=error.message)
            return
        except Exception:
            self.state.update(busy=False, error="Bijwerken is niet gelukt. De huidige versie blijft werken.")
            return
        self.state["step"] = "Opnieuw starten"
        shutdown()

    def _prepare(self, latest: dict, port: int) -> None:
        if not latest.get("zip_url") or not latest.get("sha_url"):
            raise UpdateError("Deze versie heeft geen downloadbestand. Probeer het later opnieuw.")
        reset.backup(self.database)   # without the token, like spec 014
        work = self.update_dir()
        work.mkdir(parents=True, exist_ok=True)

        self.state["step"] = "Nieuwe versie downloaden"
        try:
            archive = self.fetch(latest["zip_url"], timeout=120)
            expected = self.fetch(latest["sha_url"]).decode("ascii", "replace").split()[0].lower()
        except (OSError, IndexError, urllib.error.URLError):
            raise UpdateError("Downloaden is niet gelukt. Controleer je internetverbinding en probeer het opnieuw.")
        if hashlib.sha256(archive).hexdigest() != expected:
            raise UpdateError("De download is beschadigd (de controlesom klopt niet). Probeer het opnieuw.")
        zip_path = work / ZIP_NAME
        zip_path.write_bytes(archive)

        self.state["step"] = "Uitpakken"
        root = self.project_dir.parent
        target = root / "app-nieuw"
        shutil.rmtree(target, ignore_errors=True)
        extract_zip(zip_path, target)
        info = paths.install_info(self.project_dir) or {}
        (target / ".installed").write_text(json.dumps(info), encoding="utf-8")
        if not (target / "app.py").exists():
            raise UpdateError("De download bevat geen dashboard. Probeer het later opnieuw.")

        # update_swap.py runs outside the app folder, because that folder is replaced.
        script = work / "update_swap.py"
        shutil.copyfile(Path(__file__).with_name("update_swap.py"), script)
        (work / "resultaat.json").unlink(missing_ok=True)
        launch_detached([sys.executable, str(script), "--root", str(root), "--uv", str(info.get("uv", "uv")),
                         "--port", str(port), "--python", sys.executable, "--attempt", self.state["attempt"],
                         "--version", latest["version"]], cwd=str(work))


def extract_zip(zip_path: Path, target: Path) -> None:
    """Unpack, refusing paths that would end up outside the target folder."""
    target.mkdir(parents=True)
    base = target.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.namelist():
            if not (base / member).resolve().is_relative_to(base):
                raise UpdateError("De download bevat ongeldige bestanden.")
        archive.extractall(target)


def launch_detached(command: list[str], cwd: str) -> None:
    """Start a process that keeps running after this app stops, without a window."""
    if os.name == "nt":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(command, cwd=cwd, creationflags=flags, close_fds=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(command, cwd=cwd, start_new_session=True, close_fds=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
