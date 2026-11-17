"""Start the Portflow coach dashboard.

    python app.py              # http://127.0.0.1:5050
    python app.py --port 8000  # choose another port
    python app.py --no-browser # do not open the browser

Port 5000 is avoided on purpose: on macOS it is taken by the AirPlay receiver.
"""

import argparse
import json
import socket
import sys
import threading
import urllib.request
import webbrowser

from pathlib import Path

from dashboard import DATA_DIR, create_app
from dashboard.update_routes import APP_ID

HOST = "127.0.0.1"
DEFAULT_PORT = 5050

BANNER = r"""
  ____            _    __ _
 |  _ \ ___  _ __| |_ / _| | _____      __
 | |_) / _ \| '__| __| |_| |/ _ \ \ /\ / /
 |  __/ (_) | |  | |_|  _| | (_) \ V  V /
 |_|   \___/|_|   \__|_| |_|\___/ \_/\_/
      coach dashboard
"""


def port_is_free(port: int, host: str = HOST) -> bool:
    """Return True if nothing is listening on host:port yet."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
        except OSError:
            return False
    # A wildcard listener (such as macOS AirPlay on *:5000) does not always
    # block a bind on 127.0.0.1, so also check whether something answers.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((host, port)) != 0


def running_dashboard(port: int, host: str = HOST) -> bool:
    """Spec 020, I4: is the dashboard itself already listening on this port?"""
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/versie", timeout=2) as response:
            return json.loads(response.read()).get("app") == APP_ID
    except (OSError, ValueError):
        return False


def log_without_terminal(data_dir: Path) -> None:
    """Started from the shortcut (pythonw on Windows) there is no terminal: write to a log file."""
    if sys.stdout is None or sys.stderr is None:
        data_dir.mkdir(parents=True, exist_ok=True)
        log = open(data_dir / "dashboard.log", "a", encoding="utf-8", buffering=1)
        sys.stdout = sys.stdout or log
        sys.stderr = sys.stderr or log


def database_from_option(value: str) -> Path | None:
    """Spec 031, F4, F5: the chosen database file, or None (with a message) if it does not exist."""
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        print(f"Het databestand {path} bestaat niet. Controleer het pad.")
        return None
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Portflow coach dashboard")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"poort (standaard {DEFAULT_PORT})")
    parser.add_argument("--no-browser", action="store_true", help="browser niet automatisch openen")
    parser.add_argument("--database", metavar="PAD",
                        help="ander databestand; Chrome-profiel en reservekopieën komen in dezelfde map")
    args = parser.parse_args()
    database = None
    if args.database:
        database = database_from_option(args.database)
        if database is None:
            sys.exit(1)
    log_without_terminal(database.parent if database else DATA_DIR)

    url = f"http://{HOST}:{args.port}"
    if not port_is_free(args.port):
        if running_dashboard(args.port):   # spec 020, I4: a second click opens the dashboard
            if not args.no_browser:
                webbrowser.open(url)
            print(f"Het dashboard draait al: {url}")
            if database:   # spec 031, F6
                print(f"Let op: het draaiende dashboard gebruikt misschien een ander databestand dan {database}.")
            return
        print(f"Poort {args.port} is al in gebruik. Draait het dashboard al?")
        print(f"Kies een andere poort, bijvoorbeeld: python app.py --port {args.port + 1}")
        sys.exit(1)

    print(BANNER)
    print(f"  → {url}")
    print("  Stoppen: Ctrl+C\n")

    if database:
        print(f"  Databestand: {database}")
    app = create_app(database, start_background=True,  # connects to Portflow (spec 003)
                     data_source="opdrachtregel" if database else None)
    if not args.no_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    app.run(host=HOST, port=args.port, debug=False)


if __name__ == "__main__":
    main()
