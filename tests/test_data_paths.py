"""Tests for spec 031: showing and choosing the database file. Invented data only."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import app as app_module
from dashboard import create_app, db, paths

ROOT = Path(__file__).resolve().parent.parent


class DataPathsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name).resolve() / "test"
        self.database = self.folder / "dashboard.sqlite3"

    def tearDown(self):
        self.tmp.cleanup()

    def test_settings_show_paths_and_source(self):   # F1, F2, F4
        app = create_app(self.database, data_source="opdrachtregel")
        html = app.test_client().get("/instellingen").get_data(as_text=True)
        self.assertIn(f"<code>{self.database}</code>", html)
        self.assertIn("Herkomst: opdrachtregel (--database)", html)
        self.assertIn(f"<code>{self.folder / 'browser-profile'}</code>", html)
        self.assertIn(f"<code>{self.folder / 'reservekopieen'}</code>", html)
        self.assertIn("nog niet aangemaakt", html)   # no dashboard.log yet
        (self.folder / "dashboard.log").write_text("x")
        self.assertIn(f"<code>{self.folder / 'dashboard.log'}</code>", app.test_client().get("/instellingen").get_data(as_text=True))

    def test_browser_profile_next_to_database(self):   # F4
        app = create_app(self.database)
        self.assertEqual(Path(app.extensions["portflow"].profile_dir), self.folder / "browser-profile")

    def test_source_labels(self):   # F2
        with mock.patch.dict(os.environ, {paths.DATA_ENV: ""}):
            self.assertEqual(paths.data_source(self.folder), "standaard")
        with mock.patch.dict(os.environ, {paths.DATA_ENV: str(self.folder)}):
            self.assertEqual(paths.data_source(self.folder), "omgevingsvariabele")
        for key in ("standaard", "installatie", "omgevingsvariabele", "opdrachtregel"):
            self.assertIn(key, paths.SOURCES)

    def test_open_folder_opens_only_the_database_folder(self):   # F3
        opened = []
        app = create_app(self.database)
        app.config["OPEN_FOLDER"] = opened.append
        response = app.test_client().post("/instellingen/data/openen", data={"map": "/etc"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(opened, [str(self.folder)])

    def test_option_resolves_relative_and_home(self):   # F4
        db.init_db(str(self.database))
        old = os.getcwd()
        try:
            os.chdir(self.folder.parent)
            self.assertEqual(app_module.database_from_option("test/dashboard.sqlite3"), self.database)
        finally:
            os.chdir(old)
        with mock.patch.dict(os.environ, {"HOME": str(self.folder.parent), "USERPROFILE": str(self.folder.parent)}):
            self.assertEqual(app_module.database_from_option("~/test/dashboard.sqlite3"), self.database)

    def test_missing_file_stops_with_message(self):   # F5
        done = subprocess.run([sys.executable, str(ROOT / "app.py"), "--database", str(self.folder / "bestaat-niet.sqlite3"),
                               "--no-browser", "--port", "5098"], capture_output=True, text=True, timeout=30)
        self.assertEqual(done.returncode, 1)
        self.assertIn("bestaat niet. Controleer het pad.", done.stdout)
        self.assertFalse((self.folder / "bestaat-niet.sqlite3").exists())


if __name__ == "__main__":
    unittest.main()
