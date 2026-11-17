"""Tests for spec 020: version, data folder, checking for and installing updates, stopping, and the
install scripts. No real downloads: GitHub is faked."""

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import tomllib
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from dashboard import create_app, db, paths, update_swap, updates
from dashboard.version import VERSION

ROOT = Path(__file__).resolve().parent.parent


def release(version="9.9.9", notes="## Nieuw\n- Iets moois", zip_url="https://x/zip", sha_url="https://x/sha"):
    return {"tag_name": f"v{version}", "body": notes, "html_url": "https://github.com/x/releases/tag/v" + version,
            "assets": [{"name": updates.ZIP_NAME, "browser_download_url": zip_url},
                       {"name": updates.SHA_NAME, "browser_download_url": sha_url}]}


def zip_bytes(files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, text in files.items():
            archive.writestr(name, text)
    return buffer.getvalue()


class TempCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()


class TestVersion(unittest.TestCase):   # R1
    def test_one_version_in_code_and_pyproject(self):
        self.assertRegex(VERSION, r"^\d+\.\d+\.\d+$")
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(project["project"]["version"], VERSION)
        lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
        own = [p for p in lock["package"] if p["name"] == "portflow-coach-dashboard"]
        self.assertEqual(own[0]["version"], VERSION)

    def test_lockfile_matches_requirements(self):   # technical requirement: same packages as requirements.txt
        lock = (ROOT / "uv.lock").read_text(encoding="utf-8")
        for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").split():
            name, version = line.split("==")
            self.assertRegex(lock, rf'name = "{name.lower()}"\nversion = "{re.escape(version)}"')


class TestDataFolder(TempCase):   # I3
    def test_checkout_uses_data_next_to_code(self):
        with mock.patch.dict(os.environ, {paths.DATA_ENV: ""}):
            self.assertEqual(paths.data_dir(self.dir / "repo"), self.dir / "repo" / "data")
            self.assertIsNone(paths.install_root(self.dir / "repo"))

    def test_installed_uses_data_next_to_app_folder(self):
        app = self.dir / "Portflow coach dashboard" / "app"
        app.mkdir(parents=True)
        (app / ".installed").write_bytes(b"\xef\xbb\xbf" + json.dumps({"uv": "C:\\uv.exe"}).encode())   # with a BOM
        with mock.patch.dict(os.environ, {paths.DATA_ENV: ""}):
            self.assertEqual(paths.data_dir(app), self.dir / "Portflow coach dashboard" / "data")
        self.assertEqual(paths.install_info(app), {"uv": "C:\\uv.exe"})

    def test_environment_overrides(self):
        with mock.patch.dict(os.environ, {paths.DATA_ENV: str(self.dir / "elders")}):
            self.assertEqual(paths.data_dir(self.dir), self.dir / "elders")


class TestVersions(unittest.TestCase):   # U1
    def test_compare(self):
        self.assertTrue(updates.is_newer("v1.10.0", "1.9.3"))
        self.assertFalse(updates.is_newer("1.0.0", "1.0.0"))
        self.assertFalse(updates.is_newer("v0.9.9", "1.0.0"))
        self.assertFalse(updates.is_newer("nieuw", "1.0.0"))

    def test_release_fields(self):
        data = updates.release_from_github(release())
        self.assertEqual((data["version"], data["zip_url"], data["sha_url"]), ("9.9.9", "https://x/zip", "https://x/sha"))
        self.assertIsNone(updates.release_from_github({"tag_name": "laatste"}))

    def test_install_lines_stay_on_github(self):   # I1, R6
        block = (ROOT / "install" / "release-installatie.md").read_text(encoding="utf-8")
        self.assertIn("releases/latest/download/install-macos.sh | sh", block)
        self.assertIn("releases/latest/download/install-windows.ps1 | iex", block)
        data = updates.release_from_github(release(notes="## Nieuw\n- Weekgrafiek\n" + block))
        self.assertEqual(data["notes"], "## Nieuw\n- Weekgrafiek")
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn("install/release-installatie.md", workflow)

    def test_notes_are_escaped_and_formatted(self):   # R6
        html = str(updates.notes_html("## Nieuw\n- **Evaluaties** per week\n- <script>x</script>\n\nTot ziens."))
        self.assertIn("<h3>Nieuw</h3>", html)
        self.assertIn("<li><strong>Evaluaties</strong> per week</li>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("<p>Tot ziens.</p>", html)


class UpdaterCase(TempCase):
    def setUp(self):
        super().setUp()
        self.database = str(self.dir / "data" / "dashboard.sqlite3")
        db.init_db(self.database)
        self.answers = {}
        self.requests = []
        self.project = self.dir / "root" / "app"
        self.project.mkdir(parents=True)
        self.updater = updates.Updater(self.database, fetch=self.fetch, project_dir=self.project,
                                       spawn=lambda work: work())

    def fetch(self, url, timeout=None):
        self.requests.append(url)
        answer = self.answers.get(url)
        if isinstance(answer, Exception):
            raise answer
        if answer is None:
            raise OSError("geen internet")
        return answer


class TestChecking(UpdaterCase):   # U1, U2, U4, U5
    def test_newer_release_is_announced_until_later(self):
        self.answers[updates.LATEST_URL] = json.dumps(release("9.9.9")).encode()
        self.updater.check_now()
        self.assertEqual(self.updater.available()["version"], "9.9.9")
        self.updater.dismiss()
        self.assertIsNone(self.updater.available())
        self.answers[updates.LATEST_URL] = json.dumps(release("9.10.0")).encode()
        self.updater.check_now()
        self.assertEqual(self.updater.available()["version"], "9.10.0")   # U2 acceptance

    def test_same_version_is_not_announced(self):
        self.answers[updates.LATEST_URL] = json.dumps(release(VERSION)).encode()
        self.updater.check_now()
        self.assertIsNone(self.updater.available())

    def test_without_internet_nothing_happens(self):
        self.assertIsNone(self.updater.check_now())
        self.answers[updates.LATEST_URL] = b"<html>niet json"
        self.assertIsNone(self.updater.check_now())
        self.assertIsNone(self.updater.latest())

    def test_switched_off(self):   # U4
        self.assertTrue(self.updater.enabled())
        self.answers[updates.LATEST_URL] = json.dumps(release()).encode()
        self.updater.check_now()
        self.updater.set_enabled(False)
        self.assertIsNone(self.updater.available())

    def test_only_an_installation_updates_itself(self):   # U5
        self.assertFalse(self.updater.can_update())
        self.answers[updates.LATEST_URL] = json.dumps(release()).encode()
        self.updater.check_now()
        self.assertFalse(self.updater.start_update(5050, shutdown=lambda: None))


class TestUpdating(UpdaterCase):   # U3
    def setUp(self):
        super().setUp()
        (self.project / ".installed").write_text(json.dumps({"uv": "/bin/uv"}), encoding="utf-8")
        self.archive = zip_bytes({"app.py": "print('nieuw')", "dashboard/version.py": 'VERSION = "9.9.9"'})
        self.answers.update({updates.LATEST_URL: json.dumps(release()).encode(), "https://x/zip": self.archive,
                             "https://x/sha": f"{hashlib.sha256(self.archive).hexdigest()}  {updates.ZIP_NAME}\n".encode()})
        self.updater.check_now()
        self.stopped = []

    def start(self):
        with mock.patch.object(updates, "launch_detached") as launch:
            started = self.updater.start_update(5050, shutdown=lambda: self.stopped.append(True))
        return started, launch

    def test_backup_download_unpack_and_restart(self):
        started, launch = self.start()
        self.assertTrue(started)
        self.assertEqual(self.updater.state["error"], "")
        new = self.dir / "root" / "app-nieuw"
        self.assertEqual((new / "app.py").read_text(), "print('nieuw')")
        self.assertEqual(json.loads((new / ".installed").read_text()), {"uv": "/bin/uv"})
        self.assertEqual(len(list((self.dir / "data" / "reservekopieen").iterdir())), 1)   # backup first
        command = launch.call_args.args[0]
        self.assertIn("--root", command)
        self.assertEqual(Path(command[1]).name, "update_swap.py")
        self.assertTrue(Path(command[1]).exists() and not Path(command[1]).is_relative_to(self.project))
        self.assertEqual(self.stopped, [True])

    def test_wrong_checksum_keeps_old_version(self):
        self.answers["https://x/sha"] = b"0" * 64
        started, launch = self.start()
        self.assertIn("controlesom", self.updater.state["error"])
        launch.assert_not_called()
        self.assertEqual(self.stopped, [])
        self.assertFalse(self.updater.state["busy"])

    def test_download_failure(self):
        del self.answers["https://x/zip"]
        self.start()
        self.assertIn("Downloaden is niet gelukt", self.updater.state["error"])
        self.assertEqual(self.stopped, [])

    def test_zip_with_paths_outside_is_refused(self):
        bad = self.dir / "slecht.zip"
        bad.write_bytes(zip_bytes({"../buiten.txt": "x"}))
        with self.assertRaises(updates.UpdateError):
            updates.extract_zip(bad, self.dir / "doel")
        self.assertFalse((self.dir / "buiten.txt").exists())


class TestSwap(TempCase):   # U3, second half
    def setUp(self):
        super().setUp()
        self.root = self.dir / "root"
        for folder, text in (("app", "oud"), ("app-nieuw", "nieuw")):
            (self.root / folder).mkdir(parents=True)
            (self.root / folder / "app.py").write_text(text)

    def test_success_swaps_folders(self):
        with mock.patch.object(update_swap, "sync_packages", return_value=True):
            self.assertIsNone(update_swap.swap(self.root, "uv"))
        self.assertEqual((self.root / "app" / "app.py").read_text(), "nieuw")
        self.assertEqual((self.root / "app-oud" / "app.py").read_text(), "oud")

    def test_failed_packages_bring_old_version_back(self):
        with mock.patch.object(update_swap, "sync_packages", return_value=False):
            self.assertIn("pakketten", update_swap.swap(self.root, "uv"))
        self.assertEqual((self.root / "app" / "app.py").read_text(), "oud")

    def test_sync_runs_uv_in_the_app_folder(self):
        uv = self.dir / ("uv.bat" if os.name == "nt" else "uv")
        uv.write_text("@exit /b 0" if os.name == "nt" else "#!/bin/sh\nexit 0\n")
        uv.chmod(0o755)
        self.assertTrue(update_swap.sync_packages(str(uv), self.root))
        self.assertFalse(update_swap.sync_packages(str(self.dir / "bestaat-niet"), self.root))


class TestPages(UpdaterCase):   # R1, U2, U4, I5
    def setUp(self):
        super().setUp()
        self.app = create_app(self.database)
        self.app.extensions["updater"] = self.updater
        self.app.config["SHUTDOWN"] = lambda: self.stopped.append(True)
        self.stopped = []
        self.client = self.app.test_client()

    def html(self, path):
        return self.client.get(path).get_data(as_text=True)

    def test_version_endpoint_and_settings(self):
        self.assertEqual(self.client.get("/versie").get_json()["app"], "portflow-coach-dashboard")
        self.assertIn(f"Versie {VERSION}", self.html("/instellingen"))

    def test_banner_with_later_and_whats_new(self):   # U2, U5, R6
        self.assertNotIn("update-banner", self.html("/"))
        self.answers[updates.LATEST_URL] = json.dumps(release("9.9.9", notes="## Nieuw\n- Weekgrafiek")).encode()
        self.updater.check_now()
        html = self.html("/")
        self.assertIn(f"Versie 9.9.9 is beschikbaar (je hebt {VERSION}).", html)
        self.assertNotIn("Nu bijwerken", html)   # a git checkout only gets the notice (U5)
        self.assertIn("<li>Weekgrafiek</li>", self.html("/nieuwe-versie"))
        self.client.post("/bijwerken/later", data={"next": "/"})
        self.assertNotIn("update-banner", self.html("/"))

    def test_update_button_for_an_installation(self):   # U2
        (self.project / ".installed").write_text("{}", encoding="utf-8")
        self.answers[updates.LATEST_URL] = json.dumps(release()).encode()
        self.updater.check_now()
        self.assertIn("Nu bijwerken", self.html("/"))

    def test_switch_checking_off(self):   # U4
        self.assertIn('name="controleren" value="1" checked', self.html("/instellingen"))
        self.client.post("/instellingen/versies", data={})
        self.assertFalse(self.updater.enabled())
        self.assertNotIn('name="controleren" value="1" checked', self.html("/instellingen"))

    def test_stop(self):   # I5
        self.assertIn("Dashboard afsluiten", self.html("/"))
        response = self.client.post("/afsluiten")
        self.assertIn("Het dashboard is gestopt.", response.get_data(as_text=True))
        self.assertIn("Open het weer met de snelkoppeling.", response.get_data(as_text=True))
        self.assertEqual(self.stopped, [True])


class TestScripts(unittest.TestCase):   # I1, I2, I7, R2, R3
    def test_fixed_addresses(self):   # R3
        latest = "https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download"
        for name in ("install-macos.sh", "install-windows.ps1"):
            with self.subTest(name=name):
                text = (ROOT / "install" / name).read_text(encoding="utf-8")
                self.assertIn(f"{latest}/{name}", text)
                self.assertIn("--verwijderen", text)
                self.assertIn(updates.ZIP_NAME, text)

    @unittest.skipUnless(shutil.which("sh"), "geen sh")
    def test_macos_script_syntax(self):
        subprocess.run(["sh", "-n", str(ROOT / "install" / "install-macos.sh")], check=True)

    def test_workflow_builds_what_the_app_downloads(self):   # R2
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        for name in (updates.ZIP_NAME, updates.SHA_NAME, "install-macos.sh", "install-windows.ps1"):
            self.assertIn(name.replace(".sha256", ""), workflow)
        self.assertIn("macos-latest", workflow)
        self.assertIn("windows-latest", workflow)

    def test_icons_exist(self):   # I4
        for name in ("icon.icns", "icon.ico"):
            self.assertGreater((ROOT / "install" / name).stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
