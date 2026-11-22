"""New versions on GitHub (spec 020, U1-U5, R6, B1-B8).

The check asks GitHub for the latest release; nothing is sent but the request itself (with the
version in the User-Agent). Updating is only possible for an installed dashboard (paths.py): the
new code is downloaded, checked against its SHA-256 and unpacked next to the old code; then the
app starts update_swap.py and stops. That script swaps the folders, lets uv update the packages
and starts the new version (or the old one again when something fails).

A beta (B1-B8) is the code of one commit: the same steps, with GitHub's zip of that commit instead of
a release (there is no checksum for a commit, so the folder name in the zip must carry the commit).
"""

import hashlib
import json
import os
import re
import shutil
import sqlite3
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
from urllib.parse import quote

from markupsafe import Markup, escape

from . import db, paths, reset
from .version import VERSION

REPOSITORY = "petersnoek-hu/portflow-coach-dashboard"
INSTALL_MARKER = "<!-- installatie"   # the release page adds the install lines after this (spec 020, I1)
LATEST_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
BRANCHES_URL = f"https://api.github.com/repos/{REPOSITORY}/branches?per_page=100"
DEFAULT_BRANCH = "main"
COMMITS_SHOWN = 10   # B2
BETA_FILE = ".beta"  # B7: in the app folder: {"commit": ..., "branch": ...}
COMMIT_RE = re.compile(r"[0-9a-f]{40}")
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
        "notes": str(data.get("body") or "").split(INSTALL_MARKER)[0].strip(),   # R6: without the install lines
        "url": str(data.get("html_url") or f"https://github.com/{REPOSITORY}/releases/latest"),
        "zip_url": assets.get(ZIP_NAME),
        "sha_url": assets.get(SHA_NAME),
    }


def commits_url(branch: str) -> str:
    return f"https://api.github.com/repos/{REPOSITORY}/commits?sha={quote(branch, safe='')}&per_page={COMMITS_SHOWN}"


def archive_url(commit: str) -> str:
    return f"https://github.com/{REPOSITORY}/archive/{commit}.zip"


def branch_names(data: list) -> list[str]:
    """B3: the branches, with the default branch first."""
    names = [str(b["name"]) for b in data if isinstance(b, dict) and b.get("name")]
    return sorted(names, key=lambda name: (name != DEFAULT_BRANCH, name.lower()))


def commit_rows(data: list, installed: str = "") -> list[dict]:
    """B2: what the list shows per commit: the code, the first line of the message and the local time."""
    rows = []
    for item in data[:COMMITS_SHOWN]:
        commit = item.get("commit") if isinstance(item, dict) else None
        sha = str(item.get("sha") or "") if isinstance(item, dict) else ""
        if not isinstance(commit, dict) or not COMMIT_RE.fullmatch(sha):
            continue
        lines = str(commit.get("message") or "").strip().splitlines()
        when = ""
        try:
            raw = (commit.get("committer") or {}).get("date") or ""
            when = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone().strftime("%d-%m-%Y %H:%M")
        except (ValueError, AttributeError):
            pass
        rows.append({"commit": sha, "short": sha[:7], "message": lines[0] if lines else "", "date": when,
                     "installed": sha == installed})
    return rows


def notes_html(text: str) -> Markup:
    """R6: the release note (Markdown from GitHub) as simple, escaped HTML: headings, lists, bold,
    *italic*, `code` and fenced code blocks (for example an install line in a list item)."""
    def inline(line: str) -> str:
        html = str(escape(line))
        html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        return re.sub(r"\*([^*\s][^*]*)\*", r"<em>\1</em>", html)

    parts, items, paragraph, code = [], [], [], None

    def flush():
        if items:
            parts.append("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")
            items.clear()
        if paragraph:
            parts.append("<p>" + " ".join(paragraph) + "</p>")
            paragraph.clear()

    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if line.startswith("```"):
            if code is None:          # opening fence: the block belongs after what came before
                flush()
                code = []
            else:
                parts.append("<pre><code>" + str(escape("\n".join(code))) + "</code></pre>")
                code = None
        elif code is not None:
            code.append(line)
        elif not line:
            flush()
        elif line.startswith("#"):
            flush()
            parts.append(f"<h3>{inline(line.lstrip('#').strip())}</h3>")
        elif line[:2] in ("- ", "* "):
            if paragraph:
                flush()
            items.append(inline(line[2:]))
        else:
            if items and raw[:1] in (" ", "\t"):   # an indented line continues the list item
                items[-1] += " " + inline(line)
                continue
            if items:
                flush()
            paragraph.append(inline(line))
    if code is not None:
        parts.append("<pre><code>" + str(escape("\n".join(code))) + "</code></pre>")
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

    # Beta versions (B1-B3, B7) ----------------------------------------------------------------

    def beta(self) -> dict | None:
        """B7: the commit and branch of the installed beta, or None for a release."""
        try:
            data = json.loads((self.project_dir / BETA_FILE).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        ok = isinstance(data, dict) and COMMIT_RE.fullmatch(str(data.get("commit")))
        return {"commit": data["commit"], "branch": str(data.get("branch") or "")} if ok else None

    def branches(self) -> list[str] | None:
        """B3; None when GitHub cannot be reached (B4)."""
        try:
            data = json.loads(self.fetch(BRANCHES_URL))
        except (OSError, ValueError):
            return None
        return branch_names(data) if isinstance(data, list) else None

    def commits(self, branch: str) -> list[dict] | None:
        """B2; None when GitHub cannot be reached (B4)."""
        try:
            data = json.loads(self.fetch(commits_url(branch)))
        except (OSError, ValueError):
            return None
        return commit_rows(data, (self.beta() or {}).get("commit", "")) if isinstance(data, list) else None

    # Updating (U3) --------------------------------------------------------------------------------

    def update_dir(self) -> Path:
        return Path(self.database).parent / "bijwerken"

    def result(self) -> dict | None:
        """What update_swap.py wrote after the last attempt."""
        try:
            return json.loads((self.update_dir() / "resultaat.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def clean_leftovers(self) -> list[str]:
        """U7: what earlier, failed attempts left behind. app-oud stays as the one backup; copies of
        data are never removed. Returns the names that were removed."""
        root = self.project_dir.parent
        removed = []
        for folder in (root / "app-nieuw", root / "app-mislukt"):
            if folder.exists():
                shutil.rmtree(folder, ignore_errors=True)
                removed.append(folder.name)
        old_zip = self.update_dir() / ZIP_NAME
        if old_zip.exists():
            old_zip.unlink(missing_ok=True)
            removed.append(old_zip.name)
        return removed

    def start_update(self, port: int, shutdown) -> bool:
        latest = self.available() or self.latest()
        if not self.can_update() or not latest or not is_newer(latest.get("version")):
            return False
        return self._begin(lambda: self._prepare_release(latest, port), shutdown)

    def start_beta(self, commit: str, branch: str, port: int, shutdown) -> bool:
        """B5, B6: install the code of one commit."""
        if not self.can_update() or not COMMIT_RE.fullmatch(commit or ""):
            return False
        return self._begin(lambda: self._prepare_beta(commit, branch[:200], port), shutdown)

    def _begin(self, prepare, shutdown) -> bool:
        with self._lock:
            if self.state["busy"]:
                return False
            self.state = {"busy": True, "step": "Reservekopie maken", "error": "", "attempt": uuid.uuid4().hex}
        self.spawn(lambda: self._update(prepare, shutdown))
        return True

    def _update(self, prepare, shutdown) -> None:
        try:
            prepare()
        except UpdateError as error:
            self.state.update(busy=False, error=error.message)
            return
        except Exception:
            self.state.update(busy=False, error="Bijwerken is niet gelukt. De huidige versie blijft werken.")
            return
        self.state["step"] = "Opnieuw starten"
        shutdown()

    def _backup(self) -> None:
        """B8: before anything is downloaded or replaced; without the token, like spec 014."""
        try:
            reset.backup(self.database)
        except (OSError, sqlite3.Error):
            raise UpdateError("De reservekopie is niet gelukt; er is niets veranderd.") from None

    def _prepare_release(self, latest: dict, port: int) -> None:
        if not latest.get("zip_url") or not latest.get("sha_url"):
            raise UpdateError("Deze versie heeft geen downloadbestand. Probeer het later opnieuw.")
        self._backup()
        self.update_dir().mkdir(parents=True, exist_ok=True)
        self.clean_leftovers()   # U7

        self.state["step"] = "Nieuwe versie downloaden"
        try:
            archive = self.fetch(latest["zip_url"], timeout=120)
            expected = self.fetch(latest["sha_url"]).decode("ascii", "replace").split()[0].lower()
        except (OSError, IndexError):
            raise UpdateError("Downloaden is niet gelukt. Controleer je internetverbinding en probeer het opnieuw.")
        if hashlib.sha256(archive).hexdigest() != expected:
            raise UpdateError("De download is beschadigd (de controlesom klopt niet). Probeer het opnieuw.")
        self._stage(archive, port, latest["version"])

    def _prepare_beta(self, commit: str, branch: str, port: int) -> None:
        self._backup()
        self.update_dir().mkdir(parents=True, exist_ok=True)
        self.clean_leftovers()   # U7

        self.state["step"] = "Beta-versie downloaden"
        try:
            archive = self.fetch(archive_url(commit), timeout=120)
        except OSError:
            raise UpdateError("Downloaden is niet gelukt. Controleer je internetverbinding en probeer het opnieuw.")
        self._stage(archive, port, f"beta {commit[:7]}", commit=commit, branch=branch)

    def _stage(self, archive: bytes, port: int, label: str, *, commit: str = "", branch: str = "") -> None:
        """Unpack in <root>/app-nieuw and start update_swap.py (U3, B6)."""
        work = self.update_dir()
        zip_path = work / ZIP_NAME
        zip_path.write_bytes(archive)

        self.state["step"] = "Uitpakken"
        root = self.project_dir.parent
        target = root / "app-nieuw"
        shutil.rmtree(target, ignore_errors=True)
        try:
            extract_zip(zip_path, target, commit=commit)
            info = paths.install_info(self.project_dir) or {}
            (target / ".installed").write_text(json.dumps(info), encoding="utf-8")
            if commit:   # B7
                (target / BETA_FILE).write_text(json.dumps({"commit": commit, "branch": branch}), encoding="utf-8")
            required = ("app.py", "dashboard/version.py", "uv.lock") if commit else ("app.py",)
            if not all((target / name).exists() for name in required):
                raise UpdateError("De download bevat geen dashboard. Probeer het later opnieuw.")
        except UpdateError:
            shutil.rmtree(target, ignore_errors=True)
            raise
        except zipfile.BadZipFile:
            shutil.rmtree(target, ignore_errors=True)
            raise UpdateError("De download is beschadigd. Probeer het opnieuw.") from None

        # update_swap.py runs outside the app folder, because that folder is replaced.
        script = work / "update_swap.py"
        shutil.copyfile(Path(__file__).with_name("update_swap.py"), script)
        (work / "resultaat.json").unlink(missing_ok=True)
        launch_detached([sys.executable, str(script), "--root", str(root), "--uv", str(info.get("uv", "uv")),
                         "--port", str(port), "--python", sys.executable, "--attempt", self.state["attempt"],
                         "--version", label], cwd=str(work))


def extract_zip(zip_path: Path, target: Path, commit: str = "") -> None:
    """Unpack, refusing paths that would end up outside the target folder. GitHub's zip of a commit
    has one folder around everything, named after the repository and the commit (B6): check that it
    is that commit and unpack without the folder."""
    target.mkdir(parents=True)
    base = target.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        for member in names:
            if not (base / member).resolve().is_relative_to(base):
                raise UpdateError("De download bevat ongeldige bestanden.")
        top = {name.split("/")[0] for name in names}
        if commit and (len(top) != 1 or not next(iter(top)).endswith(commit)):
            raise UpdateError("De download komt niet van de gekozen commit. Probeer het opnieuw.")
        archive.extractall(target)
    if commit:
        inner = target / top.pop()
        for child in inner.iterdir():
            child.rename(target / child.name)
        inner.rmdir()


def launch_detached(command: list[str], cwd: str) -> None:
    """Start a process that keeps running after this app stops, without a window."""
    if os.name == "nt":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(command, cwd=cwd, creationflags=flags, close_fds=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(command, cwd=cwd, start_new_session=True, close_fds=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
