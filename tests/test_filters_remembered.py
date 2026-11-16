"""Tests for spec 023: the filters of Overzicht and Studenten are remembered per page. Invented names."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from dashboard import create_app


class FiltersCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        self.sql("INSERT INTO squads (id, name, full_name) VALUES (7, 'P7', 'Project Zeven')")
        self.sql("INSERT INTO students (id, name, semester, squad_id) VALUES (1, 'Lotte Bakker', 3, 7), (2, 'Sem de Wit', 4, NULL)")

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

    def html(self, path, **query):
        return self.client.get(path, query_string=query).get_data(as_text=True)

    def test_remembered_after_coming_back(self):   # F1
        self.html("/", f="1", semester="3", groep="guild")
        html = self.html("/")
        self.assertIn('<option value="3" selected>Semester 3</option>', html)
        self.assertIn('<option value="guild" selected>', html)
        self.assertIn('data-sort-name="lotte bakker"', html)
        self.assertNotIn('data-sort-name="sem de wit"', html)
        fresh = create_app(self.db_path).test_client()   # after a restart
        self.assertIn('<option value="3" selected>Semester 3</option>', fresh.get("/").get_data(as_text=True))

    def test_per_page(self):   # F2
        self.html("/studenten", f="1", project="7")
        self.assertIn('<option value="7" selected>', self.html("/studenten"))
        self.assertNotIn('<option value="7" selected>', self.html("/"))

    def test_clear(self):   # F4
        self.assertNotIn("Filters wissen", self.html("/"))
        self.html("/", f="1", semester="3")
        self.assertIn("Filters wissen", self.html("/"))
        html = self.html("/", f="1")
        self.assertNotIn("Filters wissen", html)
        self.assertNotIn("Filters wissen", self.html("/"))
        self.assertIn('data-sort-name="sem de wit"', self.html("/"))

    def test_vanished_choice(self):   # F5
        self.html("/", f="1", project="7", semester="3")
        self.sql("UPDATE students SET squad_id = NULL")
        self.sql("DELETE FROM squads")
        html = self.html("/")
        self.assertIn('<option value="3" selected>Semester 3</option>', html)
        self.assertIn('data-sort-name="lotte bakker"', html)

    def test_standard_grouping_keeps_following(self):   # F6
        self.sql("UPDATE students SET semester = NULL, squad_id = NULL")
        self.html("/", f="1", groep="none", semester="")   # the form sends the standard: nothing stored
        self.assertEqual(self.sql("SELECT value FROM settings WHERE key = 'filters_overview'"), [("{}",)])
        self.sql("UPDATE students SET squad_id = 7 WHERE id = 1")
        self.assertIn('<option value="squad" selected>', self.html("/"))

    def test_other_parameters_do_not_count(self):   # F1: only filters are a choice
        self.html("/", f="1", semester="3")
        self.assertIn('<option value="3" selected>Semester 3</option>', self.html("/", melding="Klaar"))


if __name__ == "__main__":
    unittest.main()
