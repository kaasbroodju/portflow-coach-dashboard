"""Tests for spec 021: make me coach or guild master from the overview. All names are invented."""

import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

from dashboard import create_app, db, overview

USER = "Marieke Ploeg"


class MakeMeCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        db.set_setting(self.db_path, "portflow_user_name", USER)
        conn = self.conn()
        with conn:
            conn.executemany("INSERT INTO guilds (id, code, name) VALUES (?, ?, ?)",
                             [(1, "AI", "Artificial Intelligence"), (2, "BE", "Back-end")])
            conn.execute("INSERT INTO staff (id, name, is_coach) VALUES (9, 'Joost Visser', 1)")
            conn.executemany("INSERT INTO students (id, name, coach_id) VALUES (?, ?, ?)",
                             [(1, "Lotte Bakker", None), (2, "Sem de Wit", 9), (3, "Noor Smit", None)])
        overview.save_visible_columns(conn, ["coach", "guild_master"])
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def run_sql(self, sql, params=()):
        conn = self.conn()
        try:
            with conn:
                return conn.execute(sql, params).fetchall()
        finally:
            conn.close()

    def give_user_guilds(self, *guild_ids):
        self.run_sql("INSERT INTO staff (id, name, is_guild_master) VALUES (5, ?, 1)", (USER,))
        for guild_id in guild_ids:
            self.run_sql("INSERT INTO staff_guilds (staff_id, guild_id) VALUES (5, ?)", (guild_id,))

    def buttons(self, kind, path="/?wie=alle"):
        html = self.client.get(path).get_data(as_text=True)
        return sorted(int(n) for n in re.findall(rf'/studenten/(\d+)/mij-als-{kind}"', html))

    def post(self, student_id, kind):
        return self.client.post(f"/studenten/{student_id}/mij-als-{kind}", headers={"X-Requested-With": "fetch"})

    def test_coach_button_only_when_empty(self):   # F1
        self.assertEqual(self.buttons("coach"), [1, 3])
        self.assertEqual(self.post(1, "coach").status_code, 204)
        self.assertEqual(self.buttons("coach"), [3])
        self.assertEqual(self.run_sql("SELECT s.name FROM students st JOIN staff s ON s.id = st.coach_id "
                                      "WHERE st.id = 1")[0][0], USER)
        self.assertEqual(self.post(2, "coach").status_code, 400)   # already has a coach: nothing changes
        self.assertEqual(self.run_sql("SELECT coach_id FROM students WHERE id = 2")[0][0], 9)

    def test_role_is_added(self):   # F4
        self.post(1, "coach")
        self.assertEqual([tuple(r) for r in self.run_sql("SELECT name, is_coach FROM staff WHERE name = ?", (USER,))],
                         [(USER, 1)])
        self.post(3, "gildemeester")   # no guild and no own guild: refused
        self.run_sql("INSERT INTO student_guilds (student_id, guild_id) VALUES (3, 1)")
        self.assertEqual(self.post(3, "gildemeester").status_code, 204)
        self.assertEqual([tuple(r) for r in self.run_sql("SELECT is_coach, is_guild_master FROM staff WHERE name = ?",
                                                         (USER,))], [(1, 1)])

    def test_guild_master_on_own_guilds_only(self):   # F2: student with AI and BE, user has BE
        self.give_user_guilds(2)
        self.run_sql("INSERT INTO student_guilds (student_id, guild_id) VALUES (1, 1), (1, 2)")
        self.assertEqual(self.post(1, "gildemeester").status_code, 204)
        rows = self.run_sql("SELECT guild_id, guild_master_id FROM student_guilds WHERE student_id = 1 ORDER BY guild_id")
        self.assertEqual([tuple(r) for r in rows], [(1, None), (2, 5)])
        self.assertNotIn(1, self.buttons("gildemeester"))   # the cell is filled now

    def test_guild_master_on_other_guilds(self):   # F2: student with AI, user has BE
        self.give_user_guilds(2)
        self.run_sql("INSERT INTO student_guilds (student_id, guild_id) VALUES (1, 1)")
        self.post(1, "gildemeester")
        self.assertEqual([tuple(r) for r in self.run_sql("SELECT guild_id, guild_master_id FROM student_guilds")],
                         [(1, 5)])

    def test_student_without_guild_gets_the_users_guild(self):   # F2
        self.give_user_guilds(2)
        self.assertEqual(self.buttons("gildemeester"), [1, 2, 3])
        self.post(3, "gildemeester")
        self.assertEqual([tuple(r) for r in self.run_sql("SELECT student_id, guild_id, guild_master_id FROM student_guilds")],
                         [(3, 2, 5)])

    def test_no_button_without_exactly_one_own_guild(self):   # F2
        self.assertEqual(self.buttons("gildemeester"), [])           # no own guild
        self.give_user_guilds(1, 2)
        self.assertEqual(self.buttons("gildemeester"), [])           # two own guilds
        self.assertEqual(self.post(1, "gildemeester").status_code, 400)
        self.run_sql("INSERT INTO student_guilds (student_id, guild_id, guild_master_id) VALUES (2, 1, 9)")
        self.run_sql("INSERT INTO student_guilds (student_id, guild_id) VALUES (1, 1)")
        self.assertEqual(self.buttons("gildemeester"), [1])          # has a guild without guild master

    def test_no_button_without_user_name(self):   # F3
        self.run_sql("DELETE FROM settings WHERE key = 'portflow_user_name'")
        self.assertEqual(self.buttons("coach"), [])
        self.assertEqual(self.post(1, "coach").status_code, 400)
        self.assertIsNone(self.run_sql("SELECT coach_id FROM students WHERE id = 1")[0][0])

    def test_not_in_student_list(self):   # F5
        self.assertEqual(self.buttons("coach", "/studenten"), [])

    def test_without_javascript_back_to_the_table(self):
        response = self.client.post("/studenten/1/mij-als-coach", data={"next": "/?wie=alle"})
        self.assertEqual(response.headers["Location"], "/?wie=alle")


if __name__ == "__main__":
    unittest.main()
