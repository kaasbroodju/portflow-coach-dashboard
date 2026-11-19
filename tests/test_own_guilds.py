"""Tests for spec 019, F6 (2026-11-19): "Studenten van wie ik gildemeester ben" and a choice per own
guild. All names are invented."""

import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

from dashboard import create_app, db

USER = "Marieke Ploeg"


class OwnGuildsCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        db.set_setting(self.db_path, "portflow_user_name", USER)
        conn = sqlite3.connect(self.db_path)
        with conn:
            conn.execute("INSERT INTO guilds (id, code, name) VALUES (1, 'UX', 'UI/UX gilde'), (2, 'FE', 'Front-end gilde'), "
                         "(3, 'BE', 'Back-end gilde')")
            conn.execute("INSERT INTO staff (id, name, is_guild_master) VALUES (1, ?, 1), (2, 'Joost Visser', 1)", (USER,))
            conn.execute("INSERT INTO staff_guilds (staff_id, guild_id) VALUES (1, 1), (1, 2), (2, 3)")
            conn.execute("INSERT INTO students (id, name, semester, is_hidden) VALUES (1, 'Lotte Bakker', 3, 0), "
                         "(2, 'Sem de Wit', 3, 1), (3, 'Noor Smit', 3, 0)")
            # Lotte: FE, guild master someone else; Sem (hidden): FE with the user; Noor: BE.
            conn.execute("INSERT INTO student_guilds (student_id, guild_id, guild_master_id) VALUES "
                         "(1, 2, 2), (2, 2, 1), (3, 3, 2)")
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def html(self, path="/", **query):
        return self.client.get(path, query_string=query).get_data(as_text=True)

    @staticmethod
    def options(html):
        select = html[html.index('name="wie"'):html.index("</select>", html.index('name="wie"'))]
        return re.findall(r'<option value="([^"]+)"[^>]*>([^<]+)</option>', select)


class TestOptions(OwnGuildsCase):
    def test_a_line_per_own_guild_after_guild_master(self):
        for path in ("/", "/evaluaties"):
            with self.subTest(path=path):
                options = self.options(self.html(path))
                labels = [label for _, label in options]
                at = labels.index("Studenten van wie ik gildemeester ben")
                self.assertEqual(labels[at + 1:at + 3], ["Alle studenten in mijn Front-end gilde",
                                                         "Alle studenten in mijn UI/UX gilde"])   # by code: FE, UX
                self.assertNotIn("Mijn gildestudenten", labels)
                self.assertNotIn("Alle studenten in mijn Back-end gilde", labels)

    def test_no_guilds_no_extra_lines(self):
        db.set_setting(self.db_path, "portflow_user_name", "Joop Zonder")
        labels = [label for _, label in self.options(self.html())]
        self.assertFalse(any(label.startswith("Alle studenten in mijn") for label in labels))


class TestFilter(OwnGuildsCase):
    def test_all_students_of_the_guild_also_hidden(self):
        html = self.html(f="1", wie="gilde-2")
        self.assertIn("Lotte Bakker", html)
        self.assertIn("Sem de Wit", html)
        self.assertNotIn("Noor Smit", html)
        self.assertIn('value="gilde-2" selected', html)

    def test_guild_master_choice_unchanged(self):
        html = self.html(f="1", wie="gilde")
        self.assertIn("Sem de Wit", html)
        self.assertNotIn("Lotte Bakker", html)

    def test_a_guild_that_is_not_yours_falls_back(self):
        html = self.html(f="1", wie="gilde-3")
        self.assertIn('value="zichtbaar" selected', html)
        self.assertNotIn("Sem de Wit", html)   # hidden, so not in the standard choice

    def test_evaluations_page_remembers_the_guild(self):
        self.html("/evaluaties", wie="gilde-1")
        self.assertIn('value="gilde-1" selected', self.html("/evaluaties"))


if __name__ == "__main__":
    unittest.main()
