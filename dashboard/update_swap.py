"""Second half of updating (spec 020, U3). Started by updates.Updater from a copy outside the app
folder, after the app has unpacked the new version in <root>/app-nieuw; then the app stops.

1. Wait until the dashboard has stopped (its port is free).
2. <root>/app becomes <root>/app-oud, <root>/app-nieuw becomes <root>/app.
3. uv brings the packages in <root>/venv up to date with the new uv.lock.
4. Start the dashboard again. If step 2 or 3 fails, the old version comes back and starts.

Only the standard library: this file runs on its own. The result goes to resultaat.json next to it.
"""

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def wait_until_stopped(port: int, seconds: float = 60) -> None:
    deadline = time.monotonic() + seconds
    while port_in_use(port) and time.monotonic() < deadline:
        time.sleep(0.5)
    time.sleep(1)   # let the process release its files (Windows)


def sync_packages(uv: str, root: Path) -> bool:
    env = dict(os.environ, UV_PROJECT_ENVIRONMENT=str(root / "venv"))
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        done = subprocess.run([uv, "sync", "--frozen", "--no-dev"], cwd=root / "app", env=env,
                              capture_output=True, timeout=900, creationflags=flags)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return done.returncode == 0


def start_dashboard(python: str, root: Path, port: int) -> None:
    log = open(root / "data" / "dashboard.log", "ab")
    command = [python, str(root / "app" / "app.py"), "--no-browser", "--port", str(port)]
    if os.name == "nt":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(command, cwd=root / "app", creationflags=flags, stdout=log, stderr=log, close_fds=True)
    else:
        subprocess.Popen(command, cwd=root / "app", start_new_session=True, stdout=log, stderr=log, close_fds=True)


def swap(root: Path, uv: str) -> str | None:
    """Steps 2 and 3. Returns an error message (Dutch), or None; on an error the old version is back."""
    app, new, old = root / "app", root / "app-nieuw", root / "app-oud"
    shutil.rmtree(old, ignore_errors=True)
    try:
        app.rename(old)
    except OSError:
        return "De oude versie kon niet worden vervangen (is er nog een venster van het dashboard open?)."
    try:
        new.rename(app)
    except OSError:
        old.rename(app)
        return "De nieuwe versie kon niet worden neergezet."
    if not sync_packages(uv, root):
        shutil.rmtree(app, ignore_errors=True)
        old.rename(app)
        sync_packages(uv, root)
        return "De pakketten konden niet worden bijgewerkt. Controleer je internetverbinding en probeer het opnieuw."
    return None


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    for name in ("--root", "--uv", "--python", "--attempt", "--version"):
        parser.add_argument(name, required=True)
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args(argv)
    root = Path(args.root)

    wait_until_stopped(args.port)
    error = swap(root, args.uv)
    result = {"attempt": args.attempt, "ok": error is None, "version": args.version, "message": error or ""}
    Path(__file__).with_name("resultaat.json").write_text(json.dumps(result), encoding="utf-8")
    start_dashboard(args.python, root, args.port)


if __name__ == "__main__":
    main(sys.argv[1:])
