"""Second half of updating (spec 020, U3). Started by updates.Updater from a copy outside the app
folder, after the app has unpacked the new version in <root>/app-nieuw; then the app stops.

1. Wait until the dashboard has stopped (its port is free), and stop every other process of the
   installation (Playwright, and the Chrome the dashboard started for logging in): Windows cannot
   rename a folder that a running program uses.
2. <root>/app becomes <root>/app-oud, <root>/app-nieuw becomes <root>/app (with a few tries).
3. uv brings the packages in <root>/venv up to date with the new uv.lock.
4. Start the dashboard again. If anything fails, the old version comes back and starts. Whatever
   happens, a dashboard is started at the end if there is one to start.

Only the standard library: this file runs on its own. Every step goes to bijwerken.log and the
result to resultaat.json, both next to this file (in <data>/bijwerken).
"""

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
TRIES = 10
WAIT_BETWEEN_TRIES_S = 2


def log(text: str) -> None:
    """One line per step in bijwerken.log, with date and time."""
    try:
        with open(HERE / "bijwerken.log", "a", encoding="utf-8") as file:
            for line in str(text).splitlines() or [""]:
                file.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {line}\n")
    except OSError:
        pass


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def wait_until_stopped(port: int, seconds: float = 60) -> None:
    deadline = time.monotonic() + seconds
    while port_in_use(port) and time.monotonic() < deadline:
        time.sleep(0.5)
    log(f"poort {port}: {'nog bezet' if port_in_use(port) else 'vrij'}")
    time.sleep(1)   # let the process release its files (Windows)


def installation_processes(root: Path) -> list[tuple[int, str]]:
    """(pid, description) of every process that runs from the installation or uses it, except this one
    and its parent (on Windows the venv's pythonw.exe is a small launcher that starts the real Python)."""
    own = {os.getpid(), os.getppid()}
    if os.name == "nt":
        quoted = str(root).replace("'", "''")
        script = (
            "Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and ("
            f"($_.ExecutablePath -and $_.ExecutablePath.StartsWith('{quoted}', 'OrdinalIgnoreCase')) -or "
            f"($_.CommandLine -and $_.CommandLine.IndexOf('{quoted}', 'OrdinalIgnoreCase') -ge 0)) }} | "
            "ForEach-Object { \"$($_.ProcessId) $($_.Name)\" }")
        command = ["powershell", "-NoProfile", "-NonInteractive", "-Command", script]
    else:
        command = ["pgrep", "-fl", f"{root}/"]
    try:
        output = subprocess.run(command, capture_output=True, text=True, timeout=30, creationflags=NO_WINDOW).stdout
    except (OSError, subprocess.TimeoutExpired) as error:
        log(f"processen opvragen lukte niet: {error}")
        return []
    found = []
    for line in output.splitlines():
        pid, _, name = line.strip().partition(" ")
        if pid.isdigit() and int(pid) not in own:
            found.append((int(pid), name[:120]))
    return found


def stop_installation_processes(root: Path) -> None:
    found = installation_processes(root)
    log("andere processen van de installatie: " + (", ".join(f"{name} ({pid})" for pid, name in found) or "geen"))
    for pid, _ in found:
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, timeout=30,
                               creationflags=NO_WINDOW)
            else:
                os.kill(pid, 15)
        except (OSError, subprocess.TimeoutExpired) as error:
            log(f"stoppen van {pid} lukte niet: {error}")
    if found:
        time.sleep(2)


def rename(source: Path, target: Path, tries: int = TRIES) -> bool:
    """Rename with a few tries: on Windows a virus scanner may briefly hold new files."""
    for attempt in range(1, tries + 1):
        try:
            source.rename(target)
            log(f"hernoemd: {source.name} -> {target.name}")
            return True
        except OSError as error:
            log(f"hernoemen {source.name} -> {target.name}, poging {attempt}: {error}")
            if attempt < tries:
                time.sleep(WAIT_BETWEEN_TRIES_S)
    return False


def sync_packages(uv: str, root: Path) -> bool:
    env = dict(os.environ, UV_PROJECT_ENVIRONMENT=str(root / "venv"))
    log(f"opdracht: {uv} sync --frozen --no-dev (in {root / 'app'})")
    try:
        done = subprocess.run([uv, "sync", "--frozen", "--no-dev"], cwd=root / "app", env=env,
                              capture_output=True, text=True, timeout=900, creationflags=NO_WINDOW)
    except (OSError, subprocess.TimeoutExpired) as error:
        log(f"uv: {error}")
        return False
    log((done.stdout + done.stderr).strip() or "(geen uitvoer)")
    log(f"uv: exitcode {done.returncode}")
    return done.returncode == 0


def start_dashboard(python: str, root: Path, port: int) -> None:
    log(f"starten: {python} {root / 'app' / 'app.py'} --port {port}")
    log_file = open(root / "data" / "dashboard.log", "ab")
    command = [python, str(root / "app" / "app.py"), "--no-browser", "--port", str(port)]
    if os.name == "nt":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(command, cwd=root / "app", creationflags=flags, stdout=log_file, stderr=log_file, close_fds=True)
    else:
        subprocess.Popen(command, cwd=root / "app", start_new_session=True, stdout=log_file, stderr=log_file, close_fds=True)


def restore_old(root: Path) -> None:
    """Make sure <root>/app exists again: put the old version back if the new one is not in place."""
    app, old = root / "app", root / "app-oud"
    if not app.exists() and old.exists():
        rename(old, app)


def swap(root: Path, uv: str) -> str | None:
    """Steps 2 and 3. Returns an error message (Dutch), or None; on an error the old version is back."""
    app, new, old = root / "app", root / "app-nieuw", root / "app-oud"
    shutil.rmtree(old, ignore_errors=True)
    if not rename(app, old):
        return "De oude versie kon niet worden vervangen: een ander programma gebruikt de map nog. Probeer het opnieuw."
    if not rename(new, app):
        restore_old(root)
        return "De nieuwe versie kon niet worden neergezet: een ander programma gebruikt de map nog. Probeer het opnieuw."
    if not sync_packages(uv, root):
        failed = root / "app-mislukt"
        shutil.rmtree(failed, ignore_errors=True)
        if rename(app, failed):
            restore_old(root)
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
    log("=" * 60)
    log(f"bijwerken naar {args.version} (poging {args.attempt}) in {root}")

    error = None
    try:
        wait_until_stopped(args.port)
        stop_installation_processes(root)
        error = swap(root, args.uv)
    except BaseException:   # whatever happens: write it down and start a dashboard again
        log(traceback.format_exc())
        error = "Bijwerken is onverwacht gestopt. De vorige versie wordt weer gestart."
        try:
            restore_old(root)
        except BaseException:
            log(traceback.format_exc())
    log(f"uitkomst: {error or 'gelukt'}")
    if error is None:   # U7: the download is no longer needed
        try:
            (HERE / "portflow-coach-dashboard.zip").unlink(missing_ok=True)
        except OSError:
            log(traceback.format_exc())
    result = {"attempt": args.attempt, "ok": error is None, "version": args.version, "message": error or ""}
    try:
        (HERE / "resultaat.json").write_text(json.dumps(result), encoding="utf-8")
    except OSError:
        log(traceback.format_exc())
    if (root / "app" / "app.py").exists():
        try:
            start_dashboard(args.python, root, args.port)
        except BaseException:
            log(traceback.format_exc())
    else:
        log("geen app-map om te starten; zet app-oud terug als app en start de snelkoppeling")


if __name__ == "__main__":
    main(sys.argv[1:])
