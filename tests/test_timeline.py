"""Tests for spec 029: the timeline of evaluations on the page Evaluaties. All names are invented."""

import re
import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path

from dashboard import create_app, db, overview, timeline
from dashboard.skills import SKILLS

USER = "Marieke Ploeg"
# 1 September 2026 is a Tuesday: week 1 runs from Monday 31 August.
PERIOD = ("2026-09-01", "2027-01-31")


class TimelineCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        db.set_setting(self.db_path, "portflow_user_name", USER)
        conn = self.conn()
        overview.save_semester_period(conn, *PERIOD)
        with conn:
            conn.execute("INSERT INTO staff (id, name, is_coach) VALUES (9, ?, 1)", (USER,))
            conn.executemany("INSERT INTO students (id, name, semester, coach_id) VALUES (?, ?, 3, ?)",
                             [(1, "Lotte Bakker", 9), (2, "Sem de Wit", None)])
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def add(self, student, skill, kind, day, level=None, rid=None, status="scored", assessor="Joost Visser"):
        conn = self.conn()
        with conn:
            conn.execute("INSERT INTO evaluations (student_id, skill, kind, level, date, assessor, review_request_id, "
                         "review_request_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         (student, skill, kind, level, day, None if kind == "self" else assessor, rid, status))
        conn.close()

    def weeks(self, who="iedereen"):
        conn = self.conn()
        rows = overview.apply_filters(overview.student_rows(conn, date(2026, 11, 17)), {"wie": who}, USER)
        result = timeline.week_counts(rows, date(2026, 9, 1), date(2027, 1, 31))
        conn.close()
        return result

    def html(self, path="/evaluaties"):
        return self.client.get(path).get_data(as_text=True)


class TestWeeks(TimelineCase):
    def test_weeks_cover_the_period_from_monday(self):   # F1
        weeks = self.weeks()
        self.assertEqual(weeks[0]["monday"], date(2026, 8, 31))
        self.assertEqual(weeks[-1]["monday"], date(2027, 1, 25))
        self.assertEqual(len(weeks), 22)
        self.assertEqual(weeks[3]["sunday"], date(2026, 9, 27))

    def test_achieved_and_pending_in_one_week(self):   # F1 acceptance
        for skill in ("OC", "KO", "PL"):
            self.add(1, skill, "assessed", "2026-09-22", level="1")
        self.add(1, "SW", "self", "2026-09-23", rid=5, status="submitted")
        self.add(1, "RE", "self", "2026-09-24", rid=5, status="submitted")
        week = self.weeks()[3]
        self.assertEqual((week["achieved"], week["pending"], week["total"]), (3, 2, 5))

    def test_counts_in_week_of_handing_in(self):   # F3a
        self.add(1, "OC", "self", "2026-09-16", rid=7, status="scored")
        self.add(1, "OC", "assessed", "2026-10-01", level="2", rid=7)
        weeks = self.weeks()
        self.assertEqual(weeks[2]["achieved"], 1)   # week of 14 September
        self.assertEqual(sum(w["achieved"] for w in weeks), 1)

    def test_without_self_evaluation_the_assessment_date_counts(self):   # F3a
        self.add(1, "OC", "assessed", "2026-10-01", level="2", rid=8)
        self.assertEqual(self.weeks()[4]["achieved"], 1)

    def test_start_level_counts(self):   # F3
        self.add(1, "OC", "assessed", "2026-09-10", level="0")
        self.assertEqual(self.weeks()[1]["achieved"], 1)

    def test_outside_period_excluded_assessor_and_no_date_do_not_count(self):   # F3
        self.add(1, "OC", "assessed", "2026-08-20", level="1")
        self.add(1, "KO", "assessed", "2026-09-10", level="1", assessor="Kevin Brandsma")
        self.add(1, "PL", "assessed", "", level="1")
        conn = self.conn()
        with conn:
            conn.execute("INSERT INTO excluded_assessors (name_key, name) VALUES ('kevin brandsma', 'Kevin Brandsma')")
        conn.close()
        self.assertEqual(sum(w["total"] for w in self.weeks()), 0)

    def test_full_assessment_is_not_ten_pending(self):   # F3 acceptance
        for skill in SKILLS:
            self.add(1, skill, "self", "2026-12-01", rid=11, status="submitted")
        self.assertEqual(sum(w["pending"] for w in self.weeks()), 0)

    def test_only_newest_pending_per_skill(self):   # F3
        self.add(1, "OC", "self", "2026-09-10", rid=1, status="submitted")
        self.add(1, "OC", "self", "2026-10-10", rid=2, status="submitted")
        weeks = self.weeks()
        self.assertEqual(sum(w["pending"] for w in weeks), 1)
        self.assertEqual(weeks[5]["pending"], 1)

    def test_who_selects_the_students(self):   # F2 acceptance
        self.add(1, "OC", "assessed", "2026-09-10", level="1")
        self.add(2, "OC", "assessed", "2026-09-10", level="1")
        self.assertEqual(self.weeks("iedereen")[1]["achieved"], 2)
        self.assertEqual(self.weeks("coach")[1]["achieved"], 1)


class TestScale(unittest.TestCase):
    def test_round_top_and_heights(self):
        weeks = [{"achieved": 9, "pending": 17, "total": 26}, {"achieved": 3, "pending": 0, "total": 3}]
        result = timeline.scale(weeks)
        self.assertEqual(result["top"], 30)
        self.assertEqual([t["value"] for t in result["ticks"]], [0, 10, 20, 30])
        self.assertEqual(weeks[0]["achieved_pct"], 30.0)

    def test_small_numbers(self):
        result = timeline.scale([{"achieved": 2, "pending": 1, "total": 3}])
        self.assertEqual(result["top"], 3)
        self.assertEqual([t["value"] for t in result["ticks"]], [0, 1, 2, 3])

    def test_empty(self):
        self.assertEqual(timeline.scale([{"achieved": 0, "pending": 0, "total": 0}])["top"], 0)


class TestPage(TimelineCase):
    def test_empty_state(self):   # F5
        html = self.html()
        self.assertIn("Nog geen evaluaties in deze semesterperiode.", html)
        self.assertIn("1 september 2026 – 31 januari 2027", html)
        self.assertIn("#semesterperiode", html)

    def test_chart_with_total_tooltip_and_legend(self):   # F1, F4
        self.add(1, "OC", "assessed", "2026-09-22", level="1")
        self.add(1, "SW", "self", "2026-09-23", rid=5, status="submitted")
        html = self.html()
        self.assertEqual(html.count('class="timeline-week"'), 22)
        self.assertIn('<span class="timeline-total">2</span>', html)
        self.assertIn("W4, 21/9 – 27/9: 1 behaald, 1 ingediend", html)
        self.assertIn("ingediend (?)", html)

    def test_who_is_remembered_apart_from_overview(self):   # F2
        self.add(2, "OC", "assessed", "2026-09-10", level="1")
        self.assertIn('<span class="timeline-total">1</span>', self.html("/evaluaties?wie=iedereen"))
        html = self.html("/evaluaties?wie=coach")
        self.assertIn("Nog geen evaluaties", html)
        self.assertIn('value="coach" selected', html)
        # without a choice in the address the remembered one applies, also after a restart
        client = create_app(self.db_path).test_client()
        self.assertIn('value="coach" selected', client.get("/evaluaties").get_data(as_text=True))
        # Overzicht keeps its own choice
        self.assertNotIn('value="coach" selected', self.html("/"))
        # an unknown choice falls back to the standard
        self.assertIn(f'value="{overview.WHO_DEFAULT}" selected', self.html("/evaluaties?wie=onzin"))

    def test_who_options_as_on_overview(self):   # F2
        html = self.html()
        options = re.findall(r'<option value="([a-z]+)"', html.split('id="timeline-who"')[1].split("</form>")[0])
        self.assertEqual(options, [value for value, _ in overview.WHO])


class TestCompactTable(TimelineCase):   # F7-F11
    def setUp(self):
        super().setUp()
        conn = self.conn()
        with conn:
            conn.executemany("INSERT INTO squads (id, number, name, full_name) VALUES (?, ?, ?, ?)",
                             [(1, "02", "Condor", "02 Condor"), (2, "19", "Cuimed", "19 Cuimed")])
            conn.execute("INSERT INTO students (id, name, semester, squad_id, coach_id) VALUES (3, 'Bram Visser', 4, 1, 9)")
            conn.execute("INSERT INTO students (id, name, semester, squad_id) VALUES (4, 'Anna Appel', 3, 1)")
            conn.execute("UPDATE students SET squad_id = 2 WHERE id = 1")
            conn.execute("INSERT INTO custom_columns (code, name, type) VALUES ('XQ', 'Verzonnen kolom', 'text')")
        conn.close()

    def table(self, path="/evaluaties?wie=iedereen"):
        return self.html(path).split('class="student-table compact-table"')[1].split("</table>")[0]

    def test_ordered_by_project_then_name_without_project_last(self):   # F10
        table = self.table()
        names = re.findall(r'<th scope="row" class="col-student">\s*([^<]+?)\s*<', table)
        self.assertEqual(names, ["Anna Appel", "Bram Visser", "Lotte Bakker", "Sem de Wit"])
        self.assertEqual(table.count('<tbody class="compact-block">'), 3)
        self.assertNotIn("group-header", table)

    def test_columns_cells_and_read_only(self):   # F8, F9, F11
        self.add(3, "OC", "assessed", "2026-09-22", level="1")
        self.add(3, "KO", "self", "2026-09-23", rid=5, status="submitted")
        table = self.table()
        head = re.findall(r'<th scope="col"[^>]*>([^<]+)</th>', table.split("</thead>")[0])
        self.assertEqual(head, ["Student", *SKILLS, "Gilde", "Project", "Sem", "Rol", "Coach", "Gildemeester"])
        self.assertIn('class="level level-n1"', table)
        self.assertIn('<b class="pending">?</b>', table)
        self.assertIn("Niveau 1 · 22-09-2026 · Joost Visser", table)
        self.assertNotIn("XQ", table)            # no custom columns
        self.assertNotIn("data-sort=", table)    # not sortable
        self.assertNotIn("<form", table)         # nothing to edit or hide
        self.assertNotIn("avatar", table)

    def test_who_applies_to_table_and_count(self):   # F7
        html = self.html("/evaluaties?wie=coach")
        table = html.split('class="student-table compact-table"')[1].split("</table>")[0]
        self.assertIn("Bram Visser", table)
        self.assertIn("Lotte Bakker", table)
        self.assertNotIn("Anna Appel", table)
        self.assertIn('<p class="compact-count muted">2 studenten</p>', html)

    def test_no_students(self):   # F11
        conn = self.conn()
        with conn:
            conn.execute("DELETE FROM students")
        conn.close()
        self.assertIn("Geen studenten bij deze keuze.", self.html())

    def test_project_blocks(self):   # F10, directly
        rows = [{"name": "b", "squad_id": 1, "squad_sort": "02 A"}, {"name": "c", "squad_id": None, "squad_sort": ""},
                {"name": "a", "squad_id": 1, "squad_sort": "02 A"}, {"name": "d", "squad_id": 2, "squad_sort": "01 Z"}]
        self.assertEqual([[r["name"] for r in b] for b in timeline.project_blocks(rows)], [["d"], ["a", "b"], ["c"]])


if __name__ == "__main__":
    unittest.main()
