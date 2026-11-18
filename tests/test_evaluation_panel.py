"""Tests for spec 037: reading evaluations in the side panel. Invented names and texts."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from dashboard import create_app, db, evaluation_panel, overview

FETCH = {"X-Requested-With": "fetch"}


class PanelCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        db.set_setting(self.db_path, "portflow_user_name", "Marieke Ploeg")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        overview.save_semester_period(self.conn, "2026-09-01", "2027-01-31")
        with self.conn:
            self.conn.execute("INSERT INTO students (id, name, semester) VALUES (1, 'Lotte Bakker', 3)")
            self.conn.execute("INSERT INTO staff (name, is_coach, is_guild_master) VALUES "
                              "('Joost Visser', 1, 1), ('Anke Mol', 1, 0)")
            # Request 7 (OC and KO): OC assessed, KO not yet. Request 9 (PL), later, assessed.
            self.add("OC", "self", "2026-09-22", 7, "OC en KO", level="1", text="<p>Ik heb <b>overzicht</b><script>x()</script></p>")
            self.add("KO", "self", "2026-09-22", 7, "OC en KO", text="<p>Bronnen vergeleken</p>")
            self.add("OC", "assessed", "2026-10-01", 7, "OC en KO", level="1", assessor="Joost Visser", text="<p>Goed onderbouwd</p>")
            self.add("PL", "self", "2026-10-10", 9, "Plannen", text=None)
            self.add("PL", "assessed", "2026-10-12", 9, "Plannen", level="2", assessor="Joost Visser", text="")

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def add(self, skill, kind, day, rid, title, level=None, assessor=None, text=None, status="scored"):
        with self.conn:
            self.conn.execute("INSERT INTO evaluations (student_id, skill, kind, level, date, assessor, review_request_id, "
                              "review_request_title, review_request_status, text) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                              (skill, kind, level, day, assessor, rid, title, status, text))

    def panel(self, query):
        return self.client.get(f"/studenten/1/evaluaties?{query}", headers=FETCH).get_data(as_text=True)


class TestConversation(PanelCase):   # F2
    def test_whole_request_per_skill(self):   # F2 acceptance
        html = self.panel("verzoeken=7")
        self.assertIn("OC en KO", html)
        self.assertLess(html.index("Overzicht creëren"), html.index("Kritisch oordelen"))
        self.assertLess(html.index("Ik heb <strong>overzicht</strong>"), html.index("Goed onderbouwd"))
        self.assertIn("Lotte Bakker</strong> · zelfevaluatie · niveau 1 · 22-9-2026", html)
        self.assertIn("Nog niet beoordeeld.", html)   # KO
        self.assertNotIn("<html", html)

    def test_role_follows_the_skill_for_someone_who_is_both(self):
        requests = evaluation_panel.conversations(self.conn, 1, [7, 9])
        self.assertEqual([r["title"] for r in requests], ["Plannen", "OC en KO"])   # newest first
        self.assertEqual(requests[1]["skills"][0]["assessed"][0]["role"], "gildemeester")   # OC: product skill
        self.assertEqual(requests[0]["skills"][0]["assessed"][0]["role"], "coach")          # PL: social skill

    def test_without_text(self):   # F6
        self.assertEqual(self.panel("verzoeken=9").count("(geen tekst)"), 2)

    def test_safe(self):   # F4
        self.assertNotIn("<script", self.panel("verzoeken=7"))

    def test_unknown(self):
        self.assertIn("niet (meer) gevonden", self.panel("verzoeken=99"))
        self.assertEqual(self.client.get("/studenten/5/evaluaties?verzoeken=7").status_code, 404)

    def test_as_a_page_without_javascript(self):
        html = self.client.get("/studenten/1/evaluaties?verzoeken=7").get_data(as_text=True)
        self.assertIn("Terug naar de student", html)
        self.assertIn("Goed onderbouwd", html)

    def test_names_hidden(self):   # F5
        self.client.post("/namen-verbergen", data={"aan": "1"})
        html = self.client.get("/studenten/1/evaluaties?verzoeken=7").get_data(as_text=True)
        self.assertNotIn("Lotte Bakker", html)
        self.assertIn("Joost Visser", html)   # staff stays visible


class TestWhereToClick(PanelCase):   # F3
    def test_cells_on_overview_evaluations_and_student_page(self):
        for path in ("/", "/evaluaties?wie=iedereen", "/studenten/1"):
            with self.subTest(path=path):
                html = self.client.get(path).get_data(as_text=True)
                self.assertIn('href="/studenten/1/evaluaties?verzoeken=7" data-feedback', html)   # OC
                self.assertIn('id="feedback-panel"', html)

    def test_cell_with_more_evaluations_shows_all_requests(self):
        self.add("OC", "self", "2026-10-20", 11, "OC opnieuw", level="2")
        self.add("OC", "assessed", "2026-10-25", 11, "OC opnieuw", level="2", assessor="Joost Visser")
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn('href="/studenten/1/evaluaties?verzoeken=7,11"', html)
        panel = self.panel("verzoeken=7,11")
        self.assertLess(panel.index("OC opnieuw"), panel.index("OC en KO"))

    def test_blocks_on_the_student_page(self):
        html = self.client.get("/studenten/1").get_data(as_text=True)
        self.assertRegex(html, r'<a class="skill-block skill-product"[^>]*data-feedback[^>]*\n\s*href="/studenten/1/evaluaties\?verzoeken=7">OC 1</a>')

    def test_evaluation_without_request(self):
        with self.conn:
            self.conn.execute("INSERT INTO evaluations (student_id, skill, kind, level, date, assessor, text) "
                              "VALUES (1, 'RE', 'assessed', '1', '2026-10-05', 'Anke Mol', '<p>Mooi</p>')")
            loose = self.conn.execute("SELECT id FROM evaluations WHERE skill = 'RE'").fetchone()[0]
        self.assertIn(f'href="/studenten/1/evaluaties?losse={loose}"', self.client.get("/").get_data(as_text=True))
        self.assertIn("Mooi", self.panel(f"losse={loose}"))

    def test_evidence_dot_shows_only_the_evidence_and_its_feedback(self):
        with self.conn:
            self.conn.execute("INSERT INTO evidence_items (student_id, evidence_id, name, kind, skills, created_at) "
                              "VALUES (1, 5, 'Planning sprint 2', 'file', 'PL', '2026-10-08T09:00:00Z')")
            self.conn.execute("INSERT INTO evidence_fetches (student_id, fetched_at, collections) VALUES (1, '2026-11-18T10:00:00+00:00', 1)")
            self.conn.execute("INSERT INTO evidence_comments (comment_id, student_id, evidence_id, kind, text, created_at, "
                              "author_name, author_role) VALUES (1, 1, 5, 'feedback_request', 'Klopt mijn planning?', "
                              "'2026-10-09T10:00:00Z', 'Lotte Bakker', 'student')")
        page = self.client.get("/studenten/1").get_data(as_text=True)
        self.assertIn('href="/studenten/1/bewijsstuk?ids=5"', page)
        html = self.client.get("/studenten/1/bewijsstuk?ids=5", headers=FETCH).get_data(as_text=True)
        self.assertLess(html.index("Planning sprint 2"), html.index("Klopt mijn planning?"))
        self.assertNotIn("evaluation-thread", html)   # no evaluations (changed 2026-11-18)
        self.assertNotIn("Evaluaties van", html)


class TestStoredText(unittest.TestCase):   # F1
    def test_old_database_gets_the_column(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "old.sqlite3")
            conn = sqlite3.connect(path)
            conn.execute("CREATE TABLE evaluations (id INTEGER PRIMARY KEY, student_id INTEGER NOT NULL, skill TEXT NOT NULL, "
                         "kind TEXT NOT NULL, level TEXT, date TEXT NOT NULL, assessor TEXT, review_request_id INTEGER, "
                         "review_request_title TEXT, review_request_status TEXT, is_demo INTEGER NOT NULL DEFAULT 0)")
            conn.close()
            create_app(path)
            conn = sqlite3.connect(path)
            columns = {r[1] for r in conn.execute("PRAGMA table_info(evaluations)")}
            conn.close()
            self.assertIn("text", columns)


if __name__ == "__main__":
    unittest.main()
