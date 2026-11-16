"""Spec 013, F7 (changed 2026-11-11): a semester that is not on the page Semesters is added
when importing, instead of being left empty. Invented names."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from dashboard import create_app, db, excel_import
from dashboard.xlsx_reader import Sheet


class ExcelSemesterCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        create_app(self.db_path)   # an empty dashboard: no semesters, as after Alles verwijderen
        self.sql("INSERT INTO students (id, name) VALUES (1, 'Lotte Bakker')")

    def tearDown(self):
        self.tmp.cleanup()

    def sql(self, query, params=()):
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                return conn.execute(query, params).fetchall()
        finally:
            conn.close()

    def test_missing_semester_is_added_on_import(self):
        conn = db.connect(self.db_path)
        try:
            sheet = Sheet("Blad1", False, [["Naam", "Semester"], ["Lotte Bakker", "Semester 4 (her)"],
                                           ["Iris Bouma", "Semester 3"], ["Bas Dekker", "Semester 9"]])
            rows = excel_import.build_preview(conn, sheet, 0, ["name", "semester"])
            self.assertEqual(rows[0].values["semester"][0], 4)
            self.assertIn("Semester 4 wordt toegevoegd aan Semesters", rows[0].warnings)
            self.assertEqual([f[0] for f in rows[0].fills], ["semester", "track"])   # spec 025: invulling too
            self.assertIn("Semester 'Semester 9' niet herkend", rows[2].warnings)
            self.assertEqual(self.sql("SELECT COUNT(*) FROM semesters"), [(0,)])   # the preview adds nothing
            excel_import.apply(conn, rows, selected_new={r.number for r in rows if r.status == "new"},
                               accepted_changes=set(), default_coach_id=None)
        finally:
            conn.close()
        self.assertEqual(self.sql("SELECT number FROM semesters ORDER BY number"), [(3,), (4,)])
        self.assertEqual(dict(self.sql("SELECT name, semester FROM students")),
                         {"Lotte Bakker": 4, "Iris Bouma": 3, "Bas Dekker": None})


if __name__ == "__main__":
    unittest.main()
