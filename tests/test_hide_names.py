"""Tests for spec 033: Namen verbergen. All names are invented."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from dashboard import create_app, db, hide_names, overview

NAMES = ("Lotte Bakker", "Sem de Wit", "Noor van 't Hof", "Zoë Jansen")


class HideNamesCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        conn = sqlite3.connect(self.db_path)
        overview.save_semester_period(conn, "2026-09-01", "2027-01-31")
        with conn:
            conn.execute("INSERT INTO squads (id, number, name, full_name) VALUES (1, '02', 'Condor', '02 Condor')")
            for i, name in enumerate(NAMES, start=1):
                conn.execute("INSERT INTO students (id, name, semester, squad_id) VALUES (?, ?, 3, 1)", (i, name))
            conn.execute("INSERT INTO evaluations (student_id, skill, kind, level, date, review_request_id, "
                         "review_request_title, review_request_status) VALUES (1, 'SW', 'self', '1', '2026-11-03', 5, "
                         "'Samenwerken - Lotte Bakker - 3-11-2026', 'submitted')")
            conn.execute("INSERT INTO received_requests (review_request_id, title, student_name, student_portflow_id, "
                         "status, created_at) VALUES (5, 'Samenwerken - Lotte Bakker - 3-11-2026', 'Lotte Bakker', NULL, "
                         "'not_started', '2026-11-03T10:00:00Z'), (6, 'Plannen', 'Daan Onbekend', 77, 'not_started', "
                         "'2026-11-04T10:00:00Z')")
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def html(self, path):
        return self.client.get(path).get_data(as_text=True)

    def switch(self, on):
        return self.client.post("/namen-verbergen", data={"aan": "1" if on else "0", "next": "/evaluaties"})


class TestSwitch(HideNamesCase):
    def test_off_by_default_and_in_the_menu(self):   # F1, F6
        html = self.html("/")
        self.assertIn('role="switch" aria-checked="false"', html)
        self.assertIn("Namen verbergen", html)
        self.assertIn("Lotte Bakker", html)
        self.assertNotIn("hide-names-banner", html)

    def test_on_hides_every_student_name_on_the_main_pages(self):   # F2, F4 acceptance
        response = self.switch(True)
        self.assertEqual(response.headers["Location"], "/evaluaties")
        for path in ("/", "/evaluaties?wie=iedereen", "/studenten", "/studenten/1", "/projecten", "/studenten/1/bewerken"):
            with self.subTest(path=path):
                html = self.html(path)
                for name in NAMES + ("Daan Onbekend",):
                    self.assertNotIn(name.casefold(), html.casefold(), name)
                    self.assertNotIn(name.replace("'", "&#39;").casefold(), html.casefold())
                self.assertIn("Namen zijn verborgen", html)   # F5
        self.assertIn("Student 1", self.html("/"))
        self.assertIn("Samenwerken - Student 1 - 3-11-2026", self.html("/evaluaties"))   # in titles of requests too
        self.assertIn("Student 5", self.html("/evaluaties"))   # a sender who is not followed

    def test_avatars_show_the_number(self):   # F3
        self.switch(True)
        self.assertIn('<span class="avatar avatar-small">2</span>', self.html("/"))
        self.assertIn('title="Student 3">3</span>', self.html("/projecten"))

    def test_switch_off_again_and_not_after_restart(self):   # F5, F6
        self.switch(True)
        self.switch(False)
        self.assertIn("Lotte Bakker", self.html("/"))
        self.switch(True)
        restarted = create_app(self.db_path).test_client()
        self.assertIn("Lotte Bakker", restarted.get("/").get_data(as_text=True))

    def test_saving_while_hidden_keeps_the_real_name(self):   # F7
        self.switch(True)
        response = self.client.post("/studenten/2/bewerken", data={"name": "Student 2", "notes": "demo"})
        self.assertEqual(response.status_code, 302)   # saved
        conn = sqlite3.connect(self.db_path)
        self.assertEqual(conn.execute("SELECT name, notes FROM students WHERE id = 2").fetchone(), ("Sem de Wit", "demo"))
        conn.close()

    def test_own_name_and_staff_stay_visible(self):   # outside the scope
        conn = sqlite3.connect(self.db_path)
        with conn:
            conn.execute("INSERT INTO settings (key, value) VALUES ('portflow_user_name', 'Marieke Ploeg')")
            conn.execute("INSERT INTO staff (name, is_coach) VALUES ('Joost Visser', 1)")
            conn.execute("INSERT INTO received_requests (review_request_id, title, student_name, status, created_at) "
                         "VALUES (9, 'Test', 'Marieke Ploeg', 'not_started', '2026-11-05T10:00:00Z'), "
                         "(10, 'Test', 'Joost Visser', 'not_started', '2026-11-05T10:00:00Z')")
        numbers = hide_names.numbers(conn)
        conn.close()
        self.assertNotIn("Marieke Ploeg", numbers)
        self.assertNotIn("Joost Visser", numbers)
        conn = sqlite3.connect(self.db_path)
        with conn:   # a student who is also on the staff list (an assessor) is still hidden
            conn.execute("INSERT INTO staff (name, is_coach) VALUES ('Sem de Wit', 0)")
        self.assertEqual(hide_names.numbers(conn)["Sem de Wit"], "Student 2")
        conn.close()
        self.switch(True)
        self.assertIn("Marieke Ploeg", self.html("/"))

    def test_numbers_are_fixed_per_student(self):   # F2
        conn = sqlite3.connect(self.db_path)
        numbers = hide_names.numbers(conn)
        conn.close()
        self.assertEqual(numbers["Lotte Bakker"], "Student 1")
        self.assertEqual(numbers["Zoë Jansen"], "Student 4")
        self.assertEqual(numbers["Daan Onbekend"], "Student 5")

    def test_whole_words_only(self):   # F2
        self.assertEqual(hide_names.anonymize("Bas leest de Basis; bas.", {"Bas": "Student 7"}),
                         "Student 7 leest de Basis; Student 7.")

    def test_json_and_escaped_forms(self):   # F2
        text = '{"failed": ["Zo\\u00eb Jansen"]} <a title="Noor van &#39;t Hof">noor van &#39;t hof</a>'
        result = hide_names.anonymize(text, {"Zoë Jansen": "Student 4", "Noor van 't Hof": "Student 3"})
        self.assertEqual(result, '{"failed": ["Student 4"]} <a title="Student 3">Student 3</a>')


if __name__ == "__main__":
    unittest.main()
