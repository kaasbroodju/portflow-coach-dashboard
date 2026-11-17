"""Version, updating and stopping (spec 020: R1, R6, I4, I5, U2-U5)."""

import os
import threading

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for

from . import updates
from .version import VERSION

bp = Blueprint("updates", __name__)
APP_ID = "portflow-coach-dashboard"   # I4: app.py recognises a running dashboard by this


def _updater() -> updates.Updater:
    return current_app.extensions["updater"]


def _port() -> int:
    host = request.host.rsplit(":", 1)
    return int(host[1]) if len(host) == 2 and host[1].isdigit() else 80


def stop_process() -> None:
    """I5: stop shortly after the answer has been sent."""
    threading.Timer(0.5, os._exit, args=(0,)).start()


def _shutdown():
    return current_app.config.get("SHUTDOWN", stop_process)


@bp.get("/versie")
def version():
    """I4: lets app.py see that the dashboard already runs; U3: the update page polls this."""
    updater = _updater()
    return jsonify(app=APP_ID, version=VERSION, installed=updater.can_update(),   # spec 020, I11
                   update=updater.state, result=updater.result())


@bp.get("/nieuwe-versie")
def whats_new():
    """R6: the release note of the newest version."""
    latest = _updater().latest()
    return render_template("whats_new.html", page={"title": "Wat is er nieuw", "label": "Wat is er nieuw"},
                           active=None, latest=latest, notes=updates.notes_html(latest["notes"]) if latest else "",
                           newer=bool(latest and updates.is_newer(latest.get("version"))),
                           can_update=_updater().can_update(), version=VERSION)


@bp.post("/bijwerken/later")
def later():
    """U2: hide the bar until the next version."""
    _updater().dismiss()
    return redirect(request.form.get("next") or url_for("pages.overview"))


@bp.post("/bijwerken")
def start_update():
    """U3: one click; the page shows the progress and reloads when the new version runs."""
    started = _updater().start_update(_port(), _shutdown())
    return redirect(url_for("updates.updating", gestart=int(started)))


@bp.get("/bijwerken")
def updating():
    updater = _updater()
    return render_template("updating.html", page={"title": "Bijwerken", "label": "Bijwerken"}, active=None,
                           state=updater.state, version=VERSION, started=request.args.get("gestart") == "1",
                           can_update=updater.can_update(), update_dir=str(updater.update_dir()))


@bp.post("/instellingen/versies")
def save_check():
    """U4: switch checking for new versions on or off; switched on, check right away."""
    updater = _updater()
    updater.set_enabled(request.form.get("controleren") == "1")
    if updater.enabled():
        threading.Thread(target=updater.check_now, daemon=True).start()
    return redirect(url_for("pages.settings", _anchor="versie"))


@bp.post("/instellingen/versie-controleren")
def check_now():
    """U6: check GitHub right away (also when switched off or put off with "Later")."""
    release = _updater().check_now()
    outcome = "mislukt" if release is None else ("nieuw" if updates.is_newer(release["version"]) else "actueel")
    return redirect(url_for("pages.settings", versie=outcome, _anchor="versie"))


@bp.post("/afsluiten")
def stop():
    """I5: stop the dashboard."""
    _shutdown()()
    return render_template("stopped.html")
