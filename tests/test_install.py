"""Tests for spec 020: version, data folder, checking for and installing updates, stopping, and the
install scripts. No real downloads: GitHub is faked."""

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
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

    def test_notes_with_code_block_in_a_list_item(self):   # R6
        notes = ("## Let op\n- **Windows:** voer in *PowerShell* deze regel uit:\n\n  ```\n  irm https://x/install.ps1 | iex\n"
                 "  ```\n\n  Je gegevens blijven staan.\n\n## Nieuw\n- De knop `Nu bijwerken`.")
        html = str(updates.notes_html(notes))
        self.assertIn("<em>PowerShell</em>", html)
        self.assertIn("<pre><code>irm https://x/install.ps1 | iex</code></pre>", html)
        self.assertNotIn("```", html)
        self.assertIn("<code>Nu bijwerken</code>", html)
        self.assertIn("<p>Je gegevens blijven staan.</p>", html)

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

    def test_leftovers_are_cleaned_but_backups_stay(self):   # U7
        root = self.dir / "root"
        for folder in ("app-nieuw", "app-mislukt", "app-oud", "data-leeg-20261117"):
            (root / folder).mkdir()
        self.updater.update_dir().mkdir(parents=True, exist_ok=True)
        (self.updater.update_dir() / updates.ZIP_NAME).write_bytes(b"oud")
        self.assertEqual(sorted(self.updater.clean_leftovers()), sorted(["app-nieuw", "app-mislukt", updates.ZIP_NAME]))
        self.assertTrue((root / "app-oud").exists())
        self.assertTrue((root / "data-leeg-20261117").exists())

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


SHA = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"
SHA2 = "b" * 40


def commit_json(sha=SHA, message="Eerste regel\n\nTweede regel", date="2026-11-20T10:30:00Z"):
    return {"sha": sha, "commit": {"message": message, "committer": {"date": date}}}


class TestBeta(UpdaterCase):   # B1-B8
    def setUp(self):
        super().setUp()
        (self.project / ".installed").write_text(json.dumps({"uv": "/bin/uv"}), encoding="utf-8")
        self.archive = zip_bytes({f"portflow-coach-dashboard-{SHA}/app.py": "print('beta')",
                                  f"portflow-coach-dashboard-{SHA}/dashboard/version.py": 'VERSION = "9.9.9"',
                                  f"portflow-coach-dashboard-{SHA}/uv.lock": ""})
        self.answers[updates.archive_url(SHA)] = self.archive
        self.stopped = []

    def start(self, commit=SHA, branch="main"):
        with mock.patch.object(updates, "launch_detached") as launch:
            started = self.updater.start_beta(commit, branch, 5050, shutdown=lambda: self.stopped.append(True))
        return started, launch

    def test_branches_start_with_main_and_commits_are_listed(self):   # B2, B3
        self.answers[updates.BRANCHES_URL] = json.dumps([{"name": "zeta"}, {"name": "main"}, {"name": "Alfa"}]).encode()
        self.assertEqual(self.updater.branches(), ["main", "Alfa", "zeta"])
        data = [commit_json(message=""), commit_json(SHA2, "Tweede"), {"sha": "kapot"}] + [commit_json()] * 12
        self.answers[updates.commits_url("feature/x y")] = json.dumps(data).encode()
        (self.project / updates.BETA_FILE).write_text(json.dumps({"commit": SHA2, "branch": "main"}))
        rows = self.updater.commits("feature/x y")
        self.assertIn("sha=feature%2Fx%20y&per_page=10", updates.commits_url("feature/x y"))
        self.assertEqual(len(rows), 9)   # the first 10 of the list, without the broken one
        self.assertEqual([r["installed"] for r in rows[:2]], [False, True])
        self.assertEqual((rows[1]["short"], rows[1]["message"]), ("bbbbbbb", "Tweede"))
        first = updates.commit_rows([commit_json()])[0]
        self.assertEqual(first["message"], "Eerste regel")
        self.assertRegex(first["date"], r"^\d\d-\d\d-\d{4} \d\d:\d\d$")

    def test_fetch_errors(self):   # B4
        self.assertIsNone(self.updater.branches())
        self.assertIsNone(self.updater.commits("main"))
        self.answers[updates.BRANCHES_URL] = b"<html>"
        self.assertIsNone(self.updater.branches())

    def test_backup_then_download_unpack_and_restart(self):   # B6, B7, B8
        started, launch = self.start()
        self.assertTrue(started)
        self.assertEqual(self.updater.state["error"], "")
        new = self.dir / "root" / "app-nieuw"
        self.assertEqual((new / "app.py").read_text(), "print('beta')")
        self.assertEqual(json.loads((new / updates.BETA_FILE).read_text()), {"commit": SHA, "branch": "main"})
        self.assertEqual(json.loads((new / ".installed").read_text()), {"uv": "/bin/uv"})
        self.assertEqual(len(list((self.dir / "data" / "reservekopieen").iterdir())), 1)
        self.assertEqual(self.requests, [updates.archive_url(SHA)])
        self.assertEqual(launch.call_args.args[0][-1], f"beta {SHA[:7]}")
        self.assertEqual(self.stopped, [True])

    def test_beta_is_recognised_in_the_app_folder(self):   # B7
        self.assertIsNone(self.updater.beta())
        (self.project / updates.BETA_FILE).write_text(json.dumps({"commit": SHA, "branch": "main"}))
        self.assertEqual(self.updater.beta(), {"commit": SHA, "branch": "main"})
        (self.project / updates.BETA_FILE).write_text("{}")
        self.assertIsNone(self.updater.beta())

    def test_failed_backup_downloads_nothing(self):   # B8
        with mock.patch.object(updates.reset, "backup", side_effect=OSError("schijf vol")):
            self.start()
        self.assertEqual(self.updater.state["error"], "De reservekopie is niet gelukt; er is niets veranderd.")
        self.assertEqual(self.requests, [])
        self.assertEqual(self.stopped, [])

    def test_latest_release_is_backed_up_too(self):   # B8
        with mock.patch.object(updates.reset, "backup", side_effect=OSError("schijf vol")):
            self.answers[updates.LATEST_URL] = json.dumps(release()).encode()
            self.updater.check_now()
            self.requests.clear()
            self.updater.start_update(5050, shutdown=lambda: self.stopped.append(True))
        self.assertIn("reservekopie is niet gelukt", self.updater.state["error"])
        self.assertEqual(self.requests, [])

    def test_zip_of_another_commit_is_refused(self):   # B6
        self.answers[updates.archive_url(SHA)] = zip_bytes({f"portflow-coach-dashboard-{SHA2}/app.py": "x"})
        started, launch = self.start()
        self.assertIn("niet van de gekozen commit", self.updater.state["error"])
        launch.assert_not_called()
        self.assertFalse((self.dir / "root" / "app-nieuw").exists())

    def test_zip_without_version_or_lockfile_is_refused(self):   # B6
        self.answers[updates.archive_url(SHA)] = zip_bytes({f"portflow-coach-dashboard-{SHA}/app.py": "x"})
        started, launch = self.start()
        self.assertIn("geen dashboard", self.updater.state["error"])
        launch.assert_not_called()

    def test_only_a_full_commit_code_in_an_installation(self):   # B1, B5
        self.assertFalse(self.start("main")[0])
        self.assertFalse(self.start("../../etc")[0])
        (self.project / ".installed").unlink()   # a git checkout
        self.assertFalse(self.start()[0])
        self.assertEqual(self.requests, [])


class TestSwap(TempCase):   # U3, second half
    def setUp(self):
        super().setUp()
        self.root = self.dir / "root"
        for folder, text in (("app", "oud"), ("app-nieuw", "nieuw")):
            (self.root / folder).mkdir(parents=True)
            (self.root / folder / "app.py").write_text(text)
        (self.root / "data" / "bijwerken").mkdir(parents=True)
        # The script logs next to itself; in tests in a temporary folder, without waiting between tries.
        for name, value in (("HERE", self.root / "data" / "bijwerken"), ("WAIT_BETWEEN_TRIES_S", 0)):
            patcher = mock.patch.object(update_swap, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_main(self, **patches):
        started = []
        args = ["--root", str(self.root), "--uv", "uv", "--python", "python", "--attempt", "a1",
                "--version", "9.9.9", "--port", "5097"]
        with mock.patch.object(update_swap, "wait_until_stopped"), \
             mock.patch.object(update_swap, "stop_installation_processes"), \
             mock.patch.object(update_swap, "start_dashboard", side_effect=lambda *a: started.append(a)):
            with mock.patch.multiple(update_swap, **patches) if patches else mock.patch.object(update_swap, "TRIES", 10):
                update_swap.main(args)
        result = json.loads((self.root / "data" / "bijwerken" / "resultaat.json").read_text())
        return result, started

    def test_success_swaps_folders(self):
        with mock.patch.object(update_swap, "sync_packages", return_value=True):
            self.assertIsNone(update_swap.swap(self.root, "uv"))
        self.assertEqual((self.root / "app" / "app.py").read_text(), "nieuw")
        self.assertEqual((self.root / "app-oud" / "app.py").read_text(), "oud")

    def test_failed_packages_bring_old_version_back(self):
        with mock.patch.object(update_swap, "sync_packages", return_value=False):
            self.assertIn("pakketten", update_swap.swap(self.root, "uv"))
        self.assertEqual((self.root / "app" / "app.py").read_text(), "oud")

    def test_rename_tries_again(self):   # a virus scanner may hold new files for a moment
        real = Path.rename
        calls = []

        def flaky(path, target):
            calls.append(path.name)
            if len(calls) < 3:
                raise PermissionError("in gebruik")
            return real(path, target)

        with mock.patch.object(Path, "rename", flaky):
            self.assertTrue(update_swap.rename(self.root / "app-nieuw", self.root / "elders"))
        self.assertEqual(len(calls), 3)
        self.assertIn("poging 2", (self.root / "data" / "bijwerken" / "bijwerken.log").read_text())

    def test_main_success_logs_and_starts_new_version(self):
        (self.root / "data" / "bijwerken" / "portflow-coach-dashboard.zip").write_bytes(b"zip")
        result, started = self.run_main(sync_packages=mock.Mock(return_value=True))
        self.assertTrue(result["ok"])
        self.assertFalse((self.root / "data" / "bijwerken" / "portflow-coach-dashboard.zip").exists())   # U7
        self.assertEqual(len(started), 1)
        self.assertEqual((self.root / "app" / "app.py").read_text(), "nieuw")
        self.assertIn("uitkomst: gelukt", (self.root / "data" / "bijwerken" / "bijwerken.log").read_text())

    def test_new_folder_locked_brings_old_back_and_starts_it(self):
        real = Path.rename

        def locked(path, target):
            if path.name == "app-nieuw":
                raise PermissionError("in gebruik")
            return real(path, target)

        with mock.patch.object(Path, "rename", locked):
            result, started = self.run_main(sync_packages=mock.Mock(return_value=True))
        self.assertFalse(result["ok"])
        self.assertIn("nieuwe versie kon niet", result["message"])
        self.assertEqual((self.root / "app" / "app.py").read_text(), "oud")
        self.assertEqual(len(started), 1)

    def test_unexpected_error_still_restarts_a_dashboard(self):   # the bug seen on Windows
        def broken(root, uv):
            (root / "app").rename(root / "app-oud")
            raise RuntimeError("onverwacht")

        result, started = self.run_main(swap=broken)
        self.assertFalse(result["ok"])
        self.assertIn("onverwacht gestopt", result["message"])
        self.assertEqual((self.root / "app" / "app.py").read_text(), "oud")   # put back
        self.assertEqual(len(started), 1)
        self.assertIn("RuntimeError: onverwacht", (self.root / "data" / "bijwerken" / "bijwerken.log").read_text())

    def test_installation_processes_skip_this_one_and_its_parent(self):
        output = f"{os.getpid()} python update_swap.py\n{os.getppid()} pythonw.exe\n4242 chrome --user-data-dir=x\n"
        with mock.patch.object(update_swap.subprocess, "run", return_value=mock.Mock(stdout=output)):
            self.assertEqual(update_swap.installation_processes(self.root), [(4242, "chrome --user-data-dir=x")])

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
        answer = self.client.get("/versie").get_json()
        self.assertEqual(answer["app"], "portflow-coach-dashboard")
        self.assertFalse(answer["installed"])   # I11: a git checkout
        (self.project / ".installed").write_text("{}", encoding="utf-8")
        self.assertTrue(self.client.get("/versie").get_json()["installed"])
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

    def check(self):
        response = self.client.post("/instellingen/versie-controleren")
        self.assertEqual(response.status_code, 302)
        return self.client.get(response.headers["Location"]).get_data(as_text=True)

    def test_update_now_offers_newer_version(self):   # U6 acceptance
        self.assertIn(">Nu bijwerken</button>", self.html("/instellingen"))
        (self.project / ".installed").write_text("{}", encoding="utf-8")
        self.updater.set_enabled(False)            # also when checking is switched off
        db.set_setting(self.database, updates.S_DISMISSED, "9.9.9")   # and after "Later"
        self.answers[updates.LATEST_URL] = json.dumps(release("9.9.9")).encode()
        html = self.check()
        self.assertIn(f"<strong>Versie 9.9.9 is beschikbaar</strong> (je hebt {VERSION})", html)
        self.assertIn(">Versie 9.9.9 installeren</button>", html)
        self.assertIn('action="/bijwerken"', html)

    def test_update_now_in_a_checkout_points_to_git(self):   # U6, U5
        self.answers[updates.LATEST_URL] = json.dumps(release("9.9.9")).encode()
        html = self.check()
        self.assertNotIn("installeren</button>", html)
        self.assertIn("git pull", html)

    def test_update_now_when_up_to_date_or_offline(self):   # U6
        self.answers[updates.LATEST_URL] = json.dumps(release(VERSION)).encode()
        self.assertIn(f"Je hebt de nieuwste versie ({VERSION}).", self.check())
        del self.answers[updates.LATEST_URL]
        self.assertIn("Controleren is niet gelukt.", self.check())

    def test_version_dropdown(self):   # B1
        checkout = self.html("/instellingen")
        self.assertIn("Beta (commit kiezen)", checkout)
        self.assertIn("<option value=\"beta\" disabled>", checkout)
        self.assertIn("git checkout", checkout)
        self.assertNotIn("beta-form", checkout)
        (self.project / ".installed").write_text("{}", encoding="utf-8")
        html = self.html("/instellingen")
        self.assertIn('id="beta-form"', html)
        self.assertIn("Dit is een beta-versie die niet is getest en misschien niet goed werkt.", html)   # B5
        self.assertNotIn("disabled>Beta", html)
        (self.project / updates.BETA_FILE).write_text(json.dumps({"commit": SHA, "branch": "main"}))   # B7
        settings = self.html("/instellingen")
        self.assertIn(f"Beta: commit {SHA[:7]}, na versie {VERSION}</strong> (branch main)", settings)
        self.assertIn(f"Versie {VERSION} + beta {SHA[:7]}</p>", settings)   # the sidebar, on every page

    def test_beta_endpoints(self):   # B2, B3, B4
        self.answers[updates.BRANCHES_URL] = json.dumps([{"name": "x"}, {"name": "main"}]).encode()
        self.assertEqual(self.client.get("/instellingen/beta/branches").get_json(), {"branches": ["main", "x"], "default": "main"})
        self.answers[updates.commits_url("x")] = json.dumps([commit_json()]).encode()
        commits = self.client.get("/instellingen/beta/commits?branch=x").get_json()["commits"]
        self.assertEqual(commits[0]["commit"], SHA)
        self.assertEqual(self.client.get("/instellingen/beta/commits").status_code, 400)
        response = self.client.get("/instellingen/beta/commits?branch=y")   # GitHub unreachable
        self.assertEqual(response.status_code, 502)
        self.assertIn("Ophalen is niet gelukt.", response.get_json()["error"])

    def test_install_beta_shows_progress_page(self):   # B6
        response = self.client.post("/instellingen/beta/installeren", data={"commit": "main", "branch": "main"})
        self.assertEqual(response.headers["Location"], "/bijwerken?gestart=0")   # nothing is started

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

    def test_scripts_stop_only_the_installed_dashboard(self):   # I9, I10, I11
        mac = (ROOT / "install" / "install-macos.sh").read_text(encoding="utf-8")
        self.assertIn('ps -axo command= | grep -F "$ROOT/app/app.py"', mac)
        self.assertIn('elif [ -w /Applications ]; then APPS="/Applications"', mac)
        self.assertIn('"/Applications/$NAME.app" "$HOME/Applications/$NAME.app"', mac)
        windows = (ROOT / "install" / "install-windows.ps1").read_text(encoding="utf-8")
        self.assertIn("Installed-Processes", windows)
        for text in (mac, windows):
            self.assertIn("app-mislukt", text)   # U7
            self.assertIn("vastgelopen update", text)
            self.assertIn("data-voor-overnemen-", text)
            self.assertIn("SELECT COUNT(*) FROM students", text)
            self.assertIn("draait al een ander dashboard", text)

    def test_macos_test_install_keeps_the_real_launcher(self):   # I9: a redirected (test) install
        # When PORTFLOW_APPLICATIONS redirects the Applications folder (used by tests), the script
        # must remove only that redirected launcher, never the user's real /Applications shortcut.
        mac = (ROOT / "install" / "install-macos.sh").read_text(encoding="utf-8")
        self.assertIn('if [ -n "${PORTFLOW_APPLICATIONS:-}" ]; then set -- "$LAUNCHER"', mac)

    @unittest.skipUnless(shutil.which("sh") and shutil.which("script") and sys.platform == "darwin", "alleen macOS")
    def test_macos_other_dashboard_keeps_running(self):   # I11 acceptance, without network or uv
        with tempfile.TemporaryDirectory() as folder:
            stub = Path(folder) / "versie.py"
            stub.write_text(
                "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
                "class H(BaseHTTPRequestHandler):\n"
                "    def do_GET(self):\n"
                "        self.send_response(200); self.end_headers(); self.wfile.write(b'{\"app\":\"portflow-coach-dashboard\"}')\n"
                "    def do_POST(self):\n"
                "        open(__file__ + '.gestopt', 'w').write('x'); self.send_response(200); self.end_headers()\n"
                "    def log_message(self, *a): pass\n"
                "HTTPServer(('127.0.0.1', 5097), H).serve_forever()\n")
            server = subprocess.Popen([sys.executable, str(stub)])
            try:
                time.sleep(0.8)
                env = dict(os.environ, PORTFLOW_INSTALL_ROOT=str(Path(folder) / "root"), PORTFLOW_PORT="5097",
                           PORTFLOW_APPLICATIONS=str(Path(folder) / "apps"))
                subprocess.run(["sh", str(ROOT / "install" / "install-macos.sh"), "--verwijderen"], cwd=folder,
                               env=env, capture_output=True, stdin=subprocess.DEVNULL, timeout=30)
                self.assertFalse(Path(str(stub) + ".gestopt").exists())
                self.assertIn("geïnstalleerd dashboard draait: nee",
                              (Path(folder) / "install.log").read_text(encoding="utf-8"))
            finally:
                server.terminate()
                server.wait()

    def test_scripts_keep_a_log(self):   # I8
        for name in ("install-macos.sh", "install-windows.ps1"):
            with self.subTest(name=name):
                text = (ROOT / "install" / name).read_text(encoding="utf-8")
                self.assertIn("install.log", text)
                for kind in ("OPDRACHT", "AFLOOP", "CONTROLE", "MELDING", "VRAAG", "FOUT", "EINDE"):
                    self.assertIn(kind, text)

    @unittest.skipUnless(shutil.which("sh") and sys.platform == "darwin", "alleen macOS")
    def test_macos_script_writes_log_in_current_folder(self):   # I8 acceptance (a failed run)
        with tempfile.TemporaryDirectory() as folder:
            env = dict(os.environ, PORTFLOW_INSTALL_ROOT=str(Path(folder) / "root"),
                       PORTFLOW_APPLICATIONS=str(Path(folder) / "apps"), PORTFLOW_NO_START="1",
                       PORTFLOW_PORT="5099", PORTFLOW_RELEASE_URL="file:///bestaat/niet", PATH="/usr/bin:/bin")
            done = subprocess.run(["sh", str(ROOT / "install" / "install-macos.sh")], cwd=folder, env=env,
                                  capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=60)
            self.assertNotEqual(done.returncode, 0)
            log = (Path(folder) / "install.log").read_text(encoding="utf-8")
            self.assertIn(f"[{os.path.realpath(folder)}]", log)   # the current folder on every line
            self.assertRegex(log, r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d \[")
            self.assertIn("EINDE: mislukt", log)
            self.assertIn("install.log", done.stderr)

    @unittest.skipUnless(shutil.which("sh") and sys.platform == "darwin", "alleen macOS")
    def test_macos_script_repairs_a_stuck_update(self):   # U7 acceptance
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "root"
            (root / "app-oud").mkdir(parents=True)
            (root / "app-oud" / "app.py").write_text("oud")
            (root / "app-nieuw").mkdir()
            (root / "data-leeg-20261117").mkdir()
            (root / "data" / "bijwerken").mkdir(parents=True)
            (root / "data" / "bijwerken" / updates.ZIP_NAME).write_bytes(b"oud")
            env = dict(os.environ, PORTFLOW_INSTALL_ROOT=str(root), PORTFLOW_APPLICATIONS=str(Path(folder) / "apps"),
                       PORTFLOW_NO_START="1", PORTFLOW_PORT="5096", PORTFLOW_RELEASE_URL="file:///bestaat/niet")
            subprocess.run(["sh", str(ROOT / "install" / "install-macos.sh")], cwd=folder, env=env,
                           capture_output=True, stdin=subprocess.DEVNULL, timeout=60)   # stops at the download
            self.assertEqual((root / "app" / "app.py").read_text(), "oud")
            self.assertFalse((root / "app-nieuw").exists())
            self.assertFalse((root / "data" / "bijwerken" / updates.ZIP_NAME).exists())
            self.assertTrue((root / "data-leeg-20261117").exists())
            log = (Path(folder) / "install.log").read_text(encoding="utf-8")
            self.assertIn("vastgelopen update; app-oud wordt teruggezet", log)
            self.assertIn("resten van eerdere pogingen opgeruimd:  app-nieuw portflow-coach-dashboard.zip", log)

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
