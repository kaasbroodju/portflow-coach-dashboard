"""Tests for spec 038: viewing the files of a piece of evidence. A fake Portflow; invented data."""

import json
import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from dashboard import create_app, evidence, evidence_files, reset
from dashboard.portflow_connection import PortflowConnection
from tests.test_evidence_detail import FakeApi as DetailApi

S3 = "https://portflow-euw1-production-storage.s3.eu-west-1.amazonaws.com/x?X-Amz-Signature=abc"
PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
FILES = {"id": 7, "name": "Presentatie sprint 3", "latest_version_type": "file", "created_at": "2026-10-01T09:00:00Z",
         "latest_version_created_at": "2026-10-01T09:00:00Z", "versions_count": 1,
         "latest_version": {"files": [
             {"id": 21, "display_name": "sprint3.pptx", "file": {"file_name": "sprint3.pptx", "type": PPTX}},
             {"id": 22, "file": {"file_name": "bord.png", "type": "image/png"}},
             {"id": 23, "file": {"file_name": "demo.mp4", "type": "video/mp4"}},
             {"id": 24, "file": {"file_name": "model.zip", "type": "application/zip"}}]}}
PREVIEWS = {
    21: {"mime_class": "ppt", "preview_state": "available", "download_url": S3 + "&o=pptx", "preview_url": S3 + "&p=pdf"},
    22: {"mime_class": "image", "preview_state": "available", "download_url": S3 + "&o=png", "object_url": S3 + "&p=png"},
    23: {"mime_class": "video", "preview_state": "inconvertible", "download_url": S3 + "&o=mp4"},
    24: {"mime_class": "other", "preview_state": "inconvertible", "download_url": S3 + "&o=zip"},
    25: {"mime_class": "pdf", "preview_state": "available", "preview_url": "https://example.org/evil.pdf"},
}
CONTENT = {"&p=pdf": ("application/pdf", b"%PDF-1.4 preview"), "&p=png": ("image/png", b"\x89PNG..."),
           "&o=mp4": ("video/mp4", b"video-bytes")}


class FakeApi:
    def __init__(self, status=200):
        self.status, self.calls = status, 0

    def preview_url(self, token, portfolio_id, file_id):
        self.calls += 1
        return (self.status, PREVIEWS.get(file_id)) if self.status == 200 else (self.status, None)

    def evidence_detail(self, token, portfolio_id, evidence_id):
        return (200, FILES) if evidence_id == 7 else DetailApi().evidence_detail(token, portfolio_id, evidence_id)


class FakeDownload:
    def __init__(self):
        self.urls = []

    def __call__(self, url, target):
        self.urls.append(url)
        mime, body = next(v for k, v in CONTENT.items() if url.endswith(k))
        target.write_bytes(body)
        return mime


class FilesCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        with self.conn:
            self.conn.execute("INSERT INTO students (id, name) VALUES (1, 'Lotte Bakker'), (2, 'Daan Visser')")
            self.conn.execute("INSERT INTO student_portfolios (student_id, portfolio_id) VALUES (1, 101), (2, 202)")
            self.conn.execute("INSERT INTO evidence_items (student_id, evidence_id, name, kind, skills) "
                              "VALUES (1, 7, 'Presentatie sprint 3', 'file', 'BD')")
            self.conn.execute("INSERT INTO settings (key, value) VALUES ('semester_start', '2026-09-01'), ('semester_end', '2027-01-31')")
        self.api, self.download = FakeApi(), FakeDownload()

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def shown(self, file_id, student_id=1, portfolio_id=101, token="token"):
        return evidence_files.shown_file(self.db_path, self.conn, token, student_id, portfolio_id, file_id,
                                         api=self.api, download=self.download)


class TestFilesOfEvidence(FilesCase):
    def test_every_file_with_how_it_is_shown(self):   # F1, F3, F5, F5a
        item, _ = evidence.detail(self.conn, 1, 7, "token", api=FakeApi())
        self.assertEqual([(f["id"], f["display"]) for f in item["files"]],
                         [(21, "pdf"), (22, "image"), (23, "video"), (24, "")])
        self.assertEqual(item["portfolio_id"], 101)

    def test_display_by_type(self):   # F1
        for mime, display in (("application/pdf", "pdf"), ("application/msword", "pdf"),
                              ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "pdf"),
                              ("image/jpeg", "image"), ("image/svg+xml", ""), ("text/html", ""), ("video/mp4", "video")):
            self.assertEqual(evidence_files.display(mime), display, mime)


class TestShownFile(FilesCase):
    def test_office_is_shown_as_the_pdf_preview_and_kept(self):   # F1, storage
        path, mime = self.shown(21)
        self.assertEqual((mime, path.read_bytes()), ("application/pdf", b"%PDF-1.4 preview"))
        self.assertEqual(path.parent, Path(self.tmp.name) / "bestanden")
        self.assertEqual(path.name, "101-21.pdf")   # no names of students in the file name
        self.assertEqual(self.download.urls, [S3 + "&p=pdf"])

    def test_second_time_from_the_cache(self):   # storage
        self.shown(21)
        self.shown(21)
        self.assertEqual((self.api.calls, len(self.download.urls)), (1, 1))

    def test_image_and_video(self):   # F1, F5
        self.assertEqual(self.shown(22)[1], "image/png")
        self.assertEqual(self.shown(23)[1], "video/mp4")
        self.assertEqual(self.download.urls[-1], S3 + "&o=mp4")

    def test_not_shown(self):   # F5a
        with self.assertRaises(evidence_files.FileError) as error:
            self.shown(24)
        self.assertIn("kan niet in het dashboard worden getoond", error.exception.message)

    def test_only_portflow_storage_is_followed(self):   # privacy
        with self.assertRaises(evidence_files.FileError):
            self.shown(25)
        self.assertEqual(self.download.urls, [])
        self.assertFalse(evidence_files.is_portflow_storage("http://portflow-x.s3.amazonaws.com/a"))
        self.assertFalse(evidence_files.is_portflow_storage("https://evil.example.org/portflow-.amazonaws.com"))

    def test_only_files_of_this_student(self):
        with self.assertRaises(evidence_files.FileError):
            self.shown(21, student_id=2, portfolio_id=101)
        self.assertEqual(self.api.calls, 0)

    def test_problems(self):   # F6
        with self.assertRaises(evidence_files.FileError) as error:
            self.shown(21, token=None)
        self.assertIn("Niet verbonden", error.exception.message)
        self.api = FakeApi(401)
        with self.assertRaises(evidence_files.FileError) as error:
            self.shown(21)
        self.assertIn("verbind opnieuw", error.exception.message)


class TestCleanUp(FilesCase):
    def test_files_not_opened_for_30_days_go(self):   # F7 acceptance
        old, recent = self.shown(21)[0], self.shown(22)[0]
        folder = old.parent
        long_ago = time.time() - 31 * 24 * 3600
        os.utime(folder / "101-21.json", (long_ago, long_ago))
        os.utime(folder / "101-22.json", (time.time() - 24 * 3600,) * 2)
        self.assertEqual(evidence_files.clean_up(self.db_path), 1)
        self.assertFalse(old.exists())
        self.assertTrue(recent.exists())

    def test_opening_counts_as_use(self):   # F7
        self.shown(21)
        meta = Path(self.tmp.name) / "bestanden" / "101-21.json"
        os.utime(meta, (time.time() - 31 * 24 * 3600,) * 2)
        self.shown(21)
        self.assertEqual(evidence_files.clean_up(self.db_path), 0)

    def test_everything_away_removes_the_folder(self):   # F7, spec 014
        self.shown(21)
        reset.reset_all(self.app)
        self.assertFalse((Path(self.tmp.name) / "bestanden").exists())
        backups = list((Path(self.tmp.name) / "reservekopieen").iterdir())
        self.assertTrue(all(p.suffix == ".sqlite3" for p in backups))   # backups contain no files


class TestRoutes(FilesCase):
    def setUp(self):
        super().setUp()
        self.originals = (evidence_files.portflow_api, evidence_files._download, evidence.portflow_api)
        evidence_files.portflow_api = evidence.portflow_api = FakeApi()
        evidence_files._download = self.download
        self.token = mock.patch.object(PortflowConnection, "token", new_callable=mock.PropertyMock, return_value="token")
        self.token.start()

    def tearDown(self):
        evidence_files.portflow_api, evidence_files._download, evidence.portflow_api = self.originals
        self.token.stop()
        super().tearDown()

    def test_panel_shows_the_files(self):   # F1, F1a, F3, F4, F5, F5a
        import dashboard.evidence as module
        original = module.detail
        module.detail = lambda conn, sid, eid, token, api=None: original(conn, sid, eid, "token", api=FakeApi())
        try:
            html = self.client.get("/studenten/1/bewijsstuk?ids=7", headers={"X-Requested-With": "fetch"}).get_data(as_text=True)
        finally:
            module.detail = original
        self.assertIn('<iframe src="/studenten/1/bestand/101/21"', html)
        self.assertIn('<img src="/studenten/1/bestand/101/22"', html)
        self.assertIn('<video src="/studenten/1/bestand/101/23"', html)
        self.assertEqual(html.count("Groot bekijken"), 3)
        self.assertEqual(html.count("Downloaden"), 4)
        self.assertIn("kan niet in het dashboard worden getoond", html)
        self.assertNotIn(S3, html)   # signed links never reach the page

    def test_file_route(self):   # F1
        response = self.client.get("/studenten/1/bestand/101/21")
        self.assertEqual((response.status_code, response.mimetype), (200, "application/pdf"))
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        response.close()

    def test_file_route_message(self):   # F5a, F6
        response = self.client.get("/studenten/1/bestand/101/24")
        self.assertEqual(response.status_code, 415)
        self.assertIn("kan niet in het dashboard worden getoond", response.get_data(as_text=True))

    def test_download_goes_to_the_original(self):   # F4
        response = self.client.get("/studenten/1/bestand/101/21/downloaden")
        self.assertEqual((response.status_code, response.headers["Location"]), (302, S3 + "&o=pptx"))
        self.assertFalse((Path(self.tmp.name) / "bestanden").exists())   # not kept


if __name__ == "__main__":
    unittest.main()
