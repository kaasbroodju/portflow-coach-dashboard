"""Portflow coach dashboard: a local Flask web app (see docs/architectuur.md)."""

import threading
import time
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, abort, request

from . import db, evidence_files, excel_routes, hide_names, paths, portflow_routes, routes, update_routes, updates
from .portflow_connection import PortflowConnection
from .portflow_fetch import Fetcher
from .portflow_token import TokenStore

PROJECT_DIR = paths.PROJECT_DIR
DATA_DIR = paths.data_dir()          # spec 020, I3: next to the code, or the folder of an installation
DEFAULT_DATABASE = DATA_DIR / "dashboard.sqlite3"
LOCAL_HOSTS = {"127.0.0.1", "localhost"}
TICK_SECONDS = 30


def create_app(
    database_path: Path | str | None = None,
    start_background: bool = False,
    data_source: str | None = None,
) -> Flask:
    """start_background=True (only from app.py) connects to Portflow, starts the refresh timer and
    checks for a new version (spec 020, U1)."""
    app = Flask(__name__)
    app.config["DATABASE"] = str(database_path or DEFAULT_DATABASE)
    # Spec 031: where the database comes from; the browser profile and backups live next to it.
    app.config["DATA_SOURCE"] = data_source or (paths.data_source() if database_path is None else "opdrachtregel")
    app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024  # Excel import: files up to 10 MB (spec 013)

    db.init_app(app)
    app.extensions["portflow"] = PortflowConnection(
        app.config["DATABASE"],
        TokenStore(app.config["DATABASE"]),
        Path(app.config["DATABASE"]).parent / "browser-profile",
    )
    app.extensions["fetcher"] = Fetcher(app.config["DATABASE"], app.extensions["portflow"])  # spec 005
    app.extensions["portflow"].after_connect = app.extensions["fetcher"].start_first   # spec 019, F2
    app.add_url_rule("/favicon.ico", "favicon",
                     lambda: app.send_static_file("favicon.svg"))
    app.register_blueprint(routes.bp)
    app.register_blueprint(portflow_routes.bp)
    app.register_blueprint(excel_routes.bp)  # spec 013
    app.register_blueprint(update_routes.bp)  # spec 020
    hide_names.init_app(app, db.get_db)       # spec 033
    app.extensions["updater"] = updates.Updater(app.config["DATABASE"])

    if start_background:
        evidence_files.clean_up(app.config["DATABASE"])   # spec 038, F7
        start_portflow(app.extensions["portflow"])
        app.extensions["updater"].start_checking()

    @app.before_request
    def only_local_requests():
        # The app only listens on 127.0.0.1. These checks also stop other
        # websites from using the browser to reach it (DNS rebinding, CSRF).
        if request.host.rsplit(":", 1)[0] not in LOCAL_HOSTS:
            abort(400)
        origin = request.headers.get("Origin")
        if request.method == "POST" and origin and urlparse(origin).netloc != request.host:
            abort(403)

    return app


def start_portflow(connection: PortflowConnection) -> None:
    """Connect at start-up (spec 003, F6) and check every 30 s whether to refresh (F7)."""

    def loop():
        connection.start_up()
        while True:
            time.sleep(TICK_SECONDS)
            connection.tick()

    threading.Thread(target=loop, daemon=True).start()
