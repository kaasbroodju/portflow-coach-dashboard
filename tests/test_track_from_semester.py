"""Tests for spec 025: the invulling follows from the semester, and "(Stage)" at Project. Invented names."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from dashboard import create_app, db, excel_import
from dashboard.xlsx_reader import Sheet


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        self.sql("INSERT INTO students (id, name) VALUES (1, 'Lotte Bakker'), (2, 'Sem de Wit')")

    def tearDown(self):
        self.tmp.cleanup()

    def sql(self, query, params=()):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            with conn:
                return conn.execute(query, params).fetchall()
        finally:
            conn.close()

    def item(self, code):
        return self.sql("SELECT id FROM choice_items WHERE code = ?", (code,))[0][0]

    def track(self, student_id):
        row = self.sql("SELECT t.code FROM students s LEFT JOIN choice_items t ON t.id = s.track_id WHERE s.id = ?", (student_id,))
        return row[0][0]

    def html(self, path, **query):
        return self.client.get(path, query_string=query).get_data(as_text=True)


class TestTrackFromSemester(Case):
    def test_rule(self):   # F1
        fetch = {"X-Requested-With": "fetch"}
        self.assertEqual(self.client.post("/studenten/1/semester", data={"semester": "3"}, headers=fetch).status_code, 205)
        self.assertEqual(self.track(1), "Open projecten")
        self.client.post("/studenten/1/semester", data={"semester": "8"})
        self.assertEqual(self.track(1), "Open projecten")   # a filled invulling never changes
        self.client.post("/studenten/2/semester", data={"semester": "5"})
        self.assertIsNone(self.track(2))
        self.client.post("/studenten/2/veld/semester", data={"waarde": "8"})   # the Studentenlijst
        self.assertEqual(self.track(2), "Afstuderen")

    def test_existing_invulling_stays(self):   # F1
        self.sql("UPDATE students SET track_id = ? WHERE id = 1", (self.item("Stage"),))
        response = self.client.post("/studenten/1/semester", data={"semester": "4"}, headers={"X-Requested-With": "fetch"})
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.track(1), "Stage")

    def test_edit_and_add_forms(self):   # F2
        self.client.post("/studenten/1/bewerken", data={"name": "Lotte Bakker", "semester": "", "track": ""})
        self.sql("INSERT INTO semesters (number) VALUES (4), (8)")
        self.client.post("/studenten/1/bewerken", data={"name": "Lotte Bakker", "semester": "4", "track": ""})
        self.assertEqual(self.track(1), "Open projecten")
        self.client.post("/studenten/toevoegen/handmatig", data={"name": "Iris Bouma", "semester": "8", "track": ""})
        new = self.sql("SELECT id FROM students WHERE name = 'Iris Bouma'")[0][0]
        self.assertEqual(self.track(new), "Afstuderen")

    def test_missing_item_is_added(self):   # F3
        self.client.post(f"/keuzelijsten/items/{self.item('Afstuderen')}/verwijderen")
        self.client.post("/studenten/1/semester", data={"semester": "8"})
        self.assertEqual(self.track(1), "Afstuderen")
        self.assertEqual(self.sql("SELECT COUNT(*) FROM choice_items WHERE code = 'Afstuderen'")[0][0], 1)

    def test_excel_import(self):   # F2
        self.sql("INSERT INTO semesters (number) VALUES (3), (8)")
        self.sql("UPDATE students SET track_id = ? WHERE id = 1", (self.item("Stage"),))
        conn = db.connect(self.db_path)
        try:
            sheet = Sheet("Blad1", False, [["Naam", "Semester", "Invulling"],
                                           ["Lotte Bakker", "3", ""], ["Iris Bouma", "8", ""], ["Bas Dekker", "3", "Minor"]])
            rows = excel_import.build_preview(conn, sheet, 0, ["name", "semester", "track"])
            self.assertEqual([c[0] for c in rows[0].changes + rows[0].fills], ["semester"])   # Stage stays
            excel_import.apply(conn, rows, selected_new={r.number for r in rows}, accepted_changes=set(), default_coach_id=None)
        finally:
            conn.close()
        names = dict(self.sql("SELECT s.name, t.code FROM students s LEFT JOIN choice_items t ON t.id = s.track_id"))
        self.assertEqual((names["Lotte Bakker"], names["Iris Bouma"], names["Bas Dekker"]), ("Stage", "Afstuderen", "Minor"))


class TestStage(Case):
    def setUp(self):
        super().setUp()
        self.sql("INSERT INTO squads (id, name, full_name) VALUES (7, 'P7', 'Project Zeven')")
        self.sql("INSERT INTO guilds (id, code, name) VALUES (1, 'AI', 'AI')")
        self.sql("INSERT INTO students (id, name, semester, squad_id) VALUES (3, 'Noor Smit', 5, 7)")
        self.sql("UPDATE students SET semester = 5, track_id = ? WHERE id = 1", (self.item("Stage"),))
        self.sql("UPDATE students SET semester = 5 WHERE id = 2")
        self.sql("INSERT INTO student_guilds (student_id, guild_id) VALUES (1, 1), (2, 1), (3, 1)")

    def test_list_shows_stage(self):   # F4
        html = self.html("/studenten", f="1", groep="none")
        row = html.split('data-sort-name="lotte bakker"')[1].split("</tr>")[0]
        self.assertIn('<option value="">(Stage)</option>', row)
        other = html.split('data-sort-name="sem de wit"')[1].split("</tr>")[0]
        self.assertIn('<option value="">–</option>', other.split('data-col="project"')[1])

    def test_project_still_wins(self):   # F4
        self.sql("UPDATE students SET track_id = ? WHERE id = 3", (self.item("Stage"),))
        html = self.html("/studenten", f="1", groep="none")
        row = html.split('data-sort-name="noor smit"')[1].split("</tr>")[0]
        self.assertNotIn("(Stage)", row)

    def test_own_group(self):   # F5
        for path in ("/", "/studenten"):
            html = self.html(path, f="1", wie="alle", groep="squad")
            self.assertLess(html.index('group-title">P7<'), html.index('group-title">(Stage)<'))
            self.assertLess(html.index('group-title">(Stage)<'), html.index('group-title">Zonder project<'))
            stage_group = html.split('group-title">(Stage)<')[1].split('group-title">')[0]
            self.assertIn('data-sort-name="lotte bakker"', stage_group)


if __name__ == "__main__":
    unittest.main()
