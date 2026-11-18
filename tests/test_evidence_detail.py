"""Tests for spec 036: reading one piece of evidence. A fake Portflow; invented data."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from dashboard import create_app, evidence

TEXT = {"id": 5, "name": "Reflectie week 6", "description": "", "latest_version_type": "free_text",
        "created_at": "2026-10-05T09:00:00Z", "latest_version_created_at": "2026-10-07T09:00:00Z", "versions_count": 2,
        "latest_version": {"version_type": "free_text", "files": [{"id": 1, "free_text": {
            "free_text": "<p>Ik heb <b>geleerd</b><script>x()</script></p><ul><li>plannen</li></ul>"
                         '<span data-mention-type="evidence" data-label="Verslag.pdf">@Verslag.pdf</span>',
            "images": [{"id": 1}], "has_pending_embedded_files": False}}]}}
FILE = {"id": 6, "name": "Sprintverslag", "latest_version_type": "file", "created_at": "2026-10-01T09:00:00Z",
        "latest_version_created_at": "2026-10-01T09:00:00Z", "versions_count": 1,
        "latest_version": {"files": [{"id": 2, "file": {"file_name": "verslag.pdf", "type": "application/pdf",
                                                         "download_state": "downloaded", "signed_id": "abc"}}]}}


class FakeApi:
    def evidence_detail(self, token, portfolio_id, evidence_id):
        return {5: (200, TEXT), 6: (200, FILE)}.get(evidence_id, (404, None))


class DetailCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        with self.conn:
            self.conn.execute("INSERT INTO students (id, name) VALUES (1, 'Lotte Bakker')")
            self.conn.execute("INSERT INTO student_portfolios (student_id, portfolio_id) VALUES (1, 101)")
            self.conn.execute("INSERT INTO evidence_items (student_id, evidence_id, name, kind, skills) "
                              "VALUES (1, 5, 'Reflectie week 6', 'free_text', 'RE,PL'), (1, 6, 'Sprintverslag', 'file', 'PL')")

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def detail(self, evidence_id, token="token"):
        return evidence.detail(self.conn, 1, evidence_id, token, api=FakeApi())


class TestDetail(DetailCase):
    def test_text_is_shown_cleaned(self):   # F3
        item, message = self.detail(5)
        self.assertIsNone(message)
        self.assertEqual(item["text"], "<p>Ik heb <strong>geleerd</strong></p><ul><li>plannen</li></ul>[Verslag.pdf]")
        self.assertEqual((item["kind"], item["versions"], item["images"], item["skills"]), ("tekst", 2, 1, ["RE", "PL"]))

    def test_file_shows_name_and_type(self):   # F3
        item, _ = self.detail(6)
        self.assertEqual((item["file_name"], item["file_type"], item["text"]), ("verslag.pdf", "pdf", ""))

    def test_problems(self):   # F2
        self.assertIn("Niet verbonden", self.detail(5, token=None)[1])
        self.assertIn("niet (meer) te openen", self.detail(99)[1])

    def test_nothing_is_stored(self):   # F2
        before = self.conn.execute("SELECT * FROM evidence_items").fetchall()
        self.detail(5)
        self.assertEqual(self.conn.execute("SELECT * FROM evidence_items").fetchall(), before)

    def test_safe_html_keeps_only_simple_markup(self):   # technical requirement
        html = evidence.safe_html('<p onclick="x">a <a href="javascript:y">b</a> <a href="https://e.nl">c</a>'
                                  '<img src=x onerror=z><style>p{}</style><iframe src="https://e.nl"></iframe></p>')
        self.assertEqual(html, '<p>a b <a href="https://e.nl" target="_blank" rel="noopener noreferrer">c</a></p>')


class TestConversation(DetailCase):   # F1-F3
    def setUp(self):
        super().setUp()
        with self.conn:
            self.conn.execute("INSERT INTO settings (key, value) VALUES ('semester_start', '2026-09-01'), ('semester_end', '2027-01-31')")
            for cid, eid in ((1, 5), (2, 6)):
                self.conn.execute("INSERT INTO evidence_comments (comment_id, student_id, evidence_id, kind, text, created_at, "
                                  "author_name, author_role) VALUES (?, 1, ?, 'feedback_request', 'Wat vind je?', "
                                  "'2026-10-08T10:00:00Z', 'Lotte Bakker', 'student')", (cid, eid))
            self.conn.execute("INSERT INTO evidence_comments (comment_id, student_id, evidence_id, parent_id, kind, text, "
                              "created_at, author_name, author_role) VALUES (3, 1, 5, 1, 'comment', 'Mooi gedaan', "
                              "'2026-10-09T10:00:00Z', 'Noor Smit', 'student')")

    def panel(self, ids, connected=True):
        import dashboard.evidence as module
        original = module.detail
        if connected:
            module.detail = lambda conn, sid, eid, token, api=None: original(conn, sid, eid, "token", api=FakeApi())
        try:
            return self.client.get(f"/studenten/1/feedback?vragen={ids}", headers={"X-Requested-With": "fetch"}).get_data(as_text=True)
        finally:
            module.detail = original

    def test_text_comes_first(self):   # F1 acceptance
        html = self.panel("1")
        self.assertIn("Bewijsstuk (tekst)", html)
        self.assertLess(html.index("geleerd"), html.index("Wat vind je?"))
        self.assertLess(html.index("Wat vind je?"), html.index("Mooi gedaan"))
        self.assertIn("1 afbeelding", html)
        self.assertNotIn("<script", html)

    def test_a_file_changes_nothing(self):   # F2
        html = self.panel("2")
        self.assertNotIn("Bewijsstuk (tekst)", html)
        self.assertIn("Wat vind je?", html)

    def test_without_connection_the_rest_stays(self):   # F3
        html = self.panel("1", connected=False)
        self.assertIn("Niet verbonden met Portflow", html)
        self.assertIn("Mooi gedaan", html)

    def test_no_second_panel_any_more(self):
        page = self.client.get("/studenten/1").get_data(as_text=True)
        self.assertNotIn('id="evidence-panel"', page)
        self.assertEqual(self.client.get("/studenten/1/bewijsstukken/5").status_code, 404)


if __name__ == "__main__":
    unittest.main()
