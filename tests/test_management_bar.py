"""Tests for spec 027: the management bar on the Beheer pages. All names are invented."""

import re
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from dashboard import create_app


class ManagementBarTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "data" / "test.sqlite3"
        self.client = create_app(self.db_path).test_client()

    def tearDown(self):
        self.tmp.cleanup()

    @contextmanager
    def db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def counts(self, path: str) -> list[tuple[str, str, bool]]:
        """(number, label, attention) per count in the bar, or [] without a bar."""
        html = self.client.get(path).get_data(as_text=True)
        bar = re.search(r'<ul class="management-counts">(.*?)</ul>', html, re.S)
        if not bar:
            return []
        return [(m.group(3), re.sub(r"<[^>]+>", "", m.group(4)).strip(), bool(m.group(1)))
                for m in re.finditer(r'<li( class="is-attention")?()><strong>(\d+)</strong>(.*?)</li>', bar.group(1), re.S)]

    def fill(self):
        """5 students: 1 hidden, 2 without project, 1 without coach, 1 without guild, 1 without semester."""
        with self.db() as conn:
            conn.execute("INSERT INTO squads (id, number, name, full_name) VALUES (1, '01', 'Verzonnen project', 'Verzonnen project (01)')")
            conn.execute("INSERT INTO guilds (id, code, name, role_name) VALUES (1, 'FE', 'Front-end gilde', 'Front-end developer')")
            conn.execute("INSERT INTO guilds (id, code, name, role_name) VALUES (2, 'UX', 'UX gilde', 'UX designer')")
            conn.execute("INSERT INTO staff (id, name, is_coach, is_guild_master) VALUES (1, 'Kees Coach', 1, 1)")
            conn.execute("INSERT INTO staff_guilds (staff_id, guild_id) VALUES (1, 1)")
            conn.execute("INSERT INTO semesters (number) VALUES (3)")
            for i, (name, squad, coach, hidden, semester) in enumerate([
                    ("Anna Appel", 1, 1, 0, 3), ("Bram Beuk", 1, 1, 1, 3), ("Cas Ceder", 1, 1, 0, 4),
                    ("Dirk Den", None, 1, 0, 3), ("Eva Es", None, None, 0, None)], start=1):
                conn.execute("INSERT INTO students (id, name, squad_id, coach_id, is_hidden, semester) VALUES (?, ?, ?, ?, ?, ?)",
                             (i, name, squad, coach, hidden, semester))
                if i < 5:
                    conn.execute("INSERT INTO student_guilds (student_id, guild_id) VALUES (?, 1)", (i,))

    def test_counts_per_page(self):   # F2, F3
        self.fill()
        self.assertEqual(self.counts("/studenten"),
                         [("5", "studenten", False), ("1", "verborgen", False), ("2", "zonder project", True)])
        self.assertEqual(self.counts("/semesters"),
                         [("1", "semester, waarvan 2 actief", False), ("4", "studenten", False), ("1", "zonder semester", True)])
        self.assertEqual(self.counts("/gildes"),
                         [("2", "gildes", False), ("4", "studenten", False), ("1", "zonder gilde", True)])
        self.assertEqual(self.counts("/coaches"),
                         [("1", "coach", False), ("0", "evaluaties tellen mee", False), ("1", "student zonder coach", True)])
        self.assertEqual(self.counts("/gildemeesters"),
                         [("1", "gildemeester", False), ("0", "evaluaties tellen mee", False),
                          ("1", "gilde zonder gildemeester", True)])
        self.assertEqual(self.counts("/projecten"),
                         [("1", "actief project", False), ("3", "studenten", False), ("2", "zonder project", True)])
        self.assertEqual(len(self.counts("/keuzelijsten")), 2)

    def test_attention_only_above_zero(self):   # F2
        with self.db() as conn:
            conn.execute("INSERT INTO squads (id, number, name, full_name) VALUES (1, '01', 'Verzonnen project', 'Verzonnen project (01)')")
            conn.execute("INSERT INTO students (name, squad_id) VALUES ('Anna Appel', 1)")
        self.assertEqual(self.counts("/projecten")[2], ("0", "zonder project", False))

    def test_one_bar_with_the_button(self):   # F1
        self.fill()
        for path, button in (("/studenten", "+ Student toevoegen"), ("/semesters", "+ Semester toevoegen"),
                             ("/gildes", "+ Gilde toevoegen"), ("/coaches", "+ Coach toevoegen"),
                             ("/gildemeesters", "+ Gildemeester toevoegen"), ("/projecten", "+ Nieuw project")):
            with self.subTest(path=path):
                html = self.client.get(path).get_data(as_text=True)
                self.assertEqual(html.count('class="management-bar'), 1)
                self.assertRegex(html, rf'(?s)management-actions">\s*<a [^>]*>{re.escape(button)}</a>')
                self.assertNotIn('class="page-actions"', html)

    def test_no_bar_on_an_empty_page(self):   # F4
        for path in ("/gildes", "/projecten", "/coaches", "/kolommen", "/studenten"):
            with self.subTest(path=path):
                self.assertEqual(self.counts(path), [])
        self.assertIn("+ Gilde toevoegen", self.client.get("/gildes").get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
