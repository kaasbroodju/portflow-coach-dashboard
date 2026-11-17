"""Where the code and the data are (spec 020, I3).

A git checkout keeps its data in data/ next to the code. An installed dashboard (install/,
spec 020) has this layout, with the marker file app/.installed written by the install script:

    <root>/app/       the code (replaced on every update)
    <root>/data/      database, browser profile, backups (never touched by an update)
    <root>/venv/      Python and the packages (made by uv)

PORTFLOW_DASHBOARD_DATA overrides the data folder (for example for a test install).
"""

import json
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
INSTALL_MARKER = PROJECT_DIR / ".installed"
DATA_ENV = "PORTFLOW_DASHBOARD_DATA"


def install_info(project_dir: Path = PROJECT_DIR) -> dict | None:
    """The contents of the marker file of an installed dashboard, or None for a git checkout."""
    try:
        # utf-8-sig: Windows PowerShell 5 writes a BOM
        data = json.loads((project_dir / ".installed").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def install_root(project_dir: Path = PROJECT_DIR) -> Path | None:
    return project_dir.parent if install_info(project_dir) is not None else None


def data_dir(project_dir: Path = PROJECT_DIR) -> Path:
    if os.environ.get(DATA_ENV):
        return Path(os.environ[DATA_ENV])
    root = install_root(project_dir)
    return root / "data" if root else project_dir / "data"
