"""Tests for spec 022: lists in the student list and the pencils above the columns. Invented names."""

import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

from dashboard import create_app


class ListInlineCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        self.sql("INSERT INTO guilds (id, code, name) VALUES (1, 'AI', 'Artificial Intelligence'), (2, 'BE', 'Back-end')")
        self.sql("INSERT INTO squads (id, name, full_name) VALUES (7, 'P7', 'Project Zeven')")
        self.sql("INSERT INTO staff (id, name, first_name, is_coach, is_guild_master) VALUES "
                 "(1, 'Joost Visser', 'Joost', 1, 0), (2, 'Ilse Dekker', 'Ilse', 0, 1), (3, 'Ruud Kok', 'Ruud', 0, 1)")
        self.sql("INSERT INTO students (id, name) VALUES (1, 'Lotte Bakker'), (2, 'Sem de Wit')")
        self.sql("INSERT INTO student_guilds (student_id, guild_id) VALUES (2, 1), (2, 2)")

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

    def post(self, path, value):
        return self.client.post(path, data={"waarde": value}, headers={"X-Requested-With": "fetch"})

    def test_fields_save_and_clear(self):   # F1
        item = lambda code: self.sql("SELECT id FROM choice_items WHERE code = ?", (code,))[0][0]   # spec 024
        stage, sm = item("Stage"), item("SM")
        for field, value, column, stored in [("semester", "5", "semester", 5), ("squad_id", "7", "squad_id", 7),
                                             ("track", str(stage), "track_id", stage),
                                             ("squad_role", str(sm), "squad_role_id", sm),
                                             ("coach_id", "1", "coach_id", 1)]:
            with self.subTest(field=field):
                self.assertEqual(self.post(f"/studenten/1/veld/{field}", value).status_code, 204)
                self.assertEqual(self.sql(f"SELECT {column} FROM students WHERE id = 1")[0][0], stored)
                self.assertEqual(self.post(f"/studenten/1/veld/{field}", "").status_code, 204)
                self.assertIsNone(self.sql(f"SELECT {column} FROM students WHERE id = 1")[0][0])

    def test_invalid_values(self):   # F1
        for field, value in [("semester", "9"), ("squad_id", "99"), ("track", "Vakantie"), ("squad_role", "CEO"),
                             ("coach_id", "2"), ("name", "X"), ("guild", "99")]:
            with self.subTest(field=field):
                self.assertEqual(self.post(f"/studenten/1/veld/{field}", value).status_code, 400)
        self.assertEqual(self.sql("SELECT semester, coach_id FROM students WHERE id = 1")[0], (None, None))

    def test_guild_replaces_and_drops_guild_master(self):   # F4
        self.post("/studenten/1/veld/guild", "1")
        self.post("/studenten/1/gildemeester/1", "2")
        self.post("/studenten/1/veld/guild", "1")    # same guild: the guild master stays
        self.assertEqual(self.sql("SELECT guild_id, guild_master_id FROM student_guilds WHERE student_id = 1"), [(1, 2)])
        self.post("/studenten/1/veld/guild", "2")
        self.assertEqual(self.sql("SELECT guild_id, guild_master_id FROM student_guilds WHERE student_id = 1"), [(2, None)])
        self.post("/studenten/1/veld/guild", "")
        self.assertEqual(self.sql("SELECT * FROM student_guilds WHERE student_id = 1"), [])

    def test_more_guilds_stay_text(self):   # F4
        self.assertEqual(self.post("/studenten/2/veld/guild", "1").status_code, 400)
        html = self.client.get("/studenten").get_data(as_text=True)
        self.assertNotIn("/studenten/2/veld/guild", html)
        self.assertIn("/studenten/1/veld/guild", html)

    def test_guild_master_per_guild(self):   # F5
        html = self.client.get("/studenten").get_data(as_text=True)
        self.assertEqual(sorted(set(re.findall(r"/studenten/2/gildemeester/(\d+)", html))), ["1", "2"])
        self.assertNotIn("/studenten/1/gildemeester/", html)   # no guild: no list
        self.assertEqual(self.post("/studenten/2/gildemeester/2", "3").status_code, 204)
        self.assertEqual(self.sql("SELECT guild_id, guild_master_id FROM student_guilds WHERE student_id = 2 ORDER BY guild_id"),
                         [(1, None), (2, 3)])
        self.assertEqual(self.post("/studenten/2/gildemeester/2", "1").status_code, 400)   # not a guild master
        self.assertEqual(self.post("/studenten/1/gildemeester/1", "2").status_code, 400)   # student has no guild

    def test_former_coach_stays_a_choice(self):   # Data
        self.sql("UPDATE students SET coach_id = 1 WHERE id = 1")
        self.sql("UPDATE staff SET is_coach = 0 WHERE id = 1")
        html = self.client.get("/studenten").get_data(as_text=True)
        self.assertIn('<option value="1" selected>Joost</option>', html)
        self.assertIn('<option value="1" selected>Joost Visser</option>', html)   # F6
        self.assertEqual(self.post("/studenten/1/veld/coach_id", "1").status_code, 204)
        self.assertEqual(self.post("/studenten/2/veld/coach_id", "1").status_code, 400)

    def test_pencils_only_in_student_list(self):   # F2, F7
        html = self.client.get("/studenten").get_data(as_text=True)
        links = re.findall(r'class="col-manage" href="([^"]+)"', html)
        self.assertEqual(links, ["/semesters", "/projecten", "/keuzelijsten#invulling", "/keuzelijsten#rol", "/gildes",
                                 "/coaches", "/coaches", "/gildemeesters", "/gildemeesters"])   # spec 024, G4
        self.assertNotIn("col-manage", self.client.get("/?wie=alle").get_data(as_text=True))

    def test_without_javascript_back_to_the_list(self):
        response = self.client.post("/studenten/1/veld/semester", data={"waarde": "2", "next": "/studenten?groep=none"})
        self.assertEqual(response.headers["Location"], "/studenten?groep=none")


if __name__ == "__main__":
    unittest.main()
