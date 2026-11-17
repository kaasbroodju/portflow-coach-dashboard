"""Tests for spec 028: folding the filters away on Overzicht and Studenten. Invented names."""

import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

from dashboard import create_app


class FiltersFoldTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "data" / "test.sqlite3"
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        conn = sqlite3.connect(self.db_path)
        with conn:
            conn.execute("INSERT INTO squads (id, number, name, full_name) VALUES (1, '01', 'Verzonnen project', 'Verzonnen project (01)')")
            conn.execute("INSERT INTO students (name, semester, squad_id) VALUES ('Anna Appel', 3, 1)")
            conn.execute("INSERT INTO semesters (number) VALUES (3)")
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def html(self, path):
        return self.client.get(path).get_data(as_text=True)

    @staticmethod
    def compact(html):
        return bool(re.search(r'<main class="content filters-compact"', html))

    def button(self, html):
        return re.sub(r"\s+", " ", re.search(r'class="button button-secondary filters-toggle".*?<span>(.*?)</span>', html, re.S).group(1))

    def test_compact_by_default_on_both_pages(self):   # F5
        for path in ("/", "/studenten"):
            with self.subTest(path=path):
                html = self.html(path)
                self.assertTrue(self.compact(html))
                self.assertIn('aria-expanded="false"', html)

    def test_state_is_kept_per_page(self):   # F1, F5
        response = self.client.post("/filters/overview", data={"stand": "uitgebreid", "next": "/"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.compact(self.html("/")))
        self.assertTrue(self.compact(self.html("/studenten")))
        # a new app on the same database (a restart) keeps it
        client = create_app(self.db_path).test_client()
        self.assertFalse(self.compact(client.get("/").get_data(as_text=True)))
        self.assertEqual(self.client.post("/filters/overview", data={"stand": "compact"},
                                          headers={"X-Requested-With": "fetch"}).status_code, 204)
        self.assertTrue(self.compact(self.html("/")))
        self.assertEqual(self.client.post("/filters/elders", data={"stand": "compact"}).status_code, 404)

    def test_what_is_hidden_when_compact(self):   # F2: by the class on <main>; the elements stay in the page
        html = self.html("/studenten")
        self.assertTrue(self.compact(html))
        css = (Path(self.app.static_folder) / "app.css").read_text()
        for part in (".filters-compact .table-toolbar > :not(.toolbar-top)",
                     ".filters-compact .table-subbar", ".filters-compact .list-subbar",
                     ".filters-compact .management-bar", ".filters-compact .col-manage"):
            self.assertIn(part, css)
        self.assertRegex(html, r'(?s)<div class="toolbar-top">\s*<span class="table-search-wrap">.*?filters-toggle.*?</button>\s*</div>')   # F1
        self.assertIn('class="management-bar', html)

    def test_filters_keep_working_when_compact(self):   # F3
        self.client.post("/filters/overview", data={"stand": "compact"})
        html = self.html("/?f=1&semester=4")
        self.assertIn("0 van 1 studenten", html)

    def test_count_of_active_filters(self):   # F4
        self.assertEqual(self.button(self.html("/?f=1")), "Filters")
        self.assertEqual(self.button(self.html("/?f=1&semester=3&project=1")), "Filters · 2")
        self.assertEqual(self.button(self.html("/?f=1&wie=coach&aansporen=1")), "Filters · 2")
        self.assertEqual(self.button(self.html("/?f=1")), "Filters")


if __name__ == "__main__":
    unittest.main()
