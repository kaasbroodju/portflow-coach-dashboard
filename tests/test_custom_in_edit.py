"""Tests for spec 026: the custom columns in Student bewerken and Student toevoegen. Invented names."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from dashboard import create_app


class CustomInEditCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        self.sql("INSERT INTO students (id, name) VALUES (1, 'Lotte Bakker')")
        self.pct = self.column("AW", "Aanwezigheid", "percentage")
        self.note = self.column("NT", "Notitie", "text")
        self.place = self.column("WP", "Werkplek", "choice")
        lid = self.sql("SELECT id FROM choice_lists WHERE column_id = ?", (self.place,))[0][0]
        self.client.post(f"/keuzelijsten/{lid}/items", data={"code": "Thuis", "omschrijving": "Werkt thuis"})
        self.thuis = self.sql("SELECT id FROM choice_items WHERE code = 'Thuis'")[0][0]

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

    def column(self, code, name, kind):
        self.client.post("/kolommen/nieuw", data={"code": code, "naam": name, "beschrijving": "", "type": kind})
        return self.sql("SELECT id FROM custom_columns WHERE code = ?", (code,))[0][0]

    def values(self, student_id=1):
        return dict(self.sql("SELECT column_id, value FROM custom_values WHERE student_id = ?", (student_id,)))

    def save(self, **custom):
        data = {"name": custom.pop("name", "Lotte Bakker")}
        data.update({f"kolom-{k[1:]}": v for k, v in custom.items()})
        return self.client.post("/studenten/1/bewerken", data=data)

    def test_block_in_order_with_current_values(self):   # F1, F2
        self.sql("INSERT INTO custom_values (student_id, column_id, value) VALUES (1, ?, '75')", (self.pct,))
        html = self.client.get("/studenten/1/bewerken").get_data(as_text=True)
        self.assertIn("<legend>Eigen kolommen</legend>", html)
        self.assertLess(html.index("Aanwezigheid"), html.index("Werkplek"))
        self.assertLess(html.index("Eigen kolommen"), html.index("Notities"))
        self.assertIn(f'name="kolom-{self.pct}" value="75"', html)
        self.assertIn(f'<option value="{self.thuis}" >Thuis · Werkt thuis</option>', html)

    def test_no_block_without_columns(self):   # F1
        for column in (self.pct, self.note, self.place):
            self.client.post(f"/kolommen/{column}/verwijderen")
        self.assertNotIn("Eigen kolommen", self.client.get("/studenten/1/bewerken").get_data(as_text=True))

    def test_save_and_clear(self):   # F3
        self.assertEqual(self.save(**{f"k{self.pct}": "80", f"k{self.note}": "Let op", f"k{self.place}": str(self.thuis)}).status_code, 302)
        self.assertEqual(self.values(), {self.pct: "80", self.note: "Let op", self.place: str(self.thuis)})
        self.assertIn('value="80"', self.client.get("/", query_string={"f": "1", "wie": "alle"}).get_data(as_text=True))
        self.save(**{f"k{self.pct}": "", f"k{self.note}": "", f"k{self.place}": ""})
        self.assertEqual(self.values(), {})

    def test_invalid_saves_nothing(self):   # F4
        for raw, message in [("120", "vul een heel getal van 0 tot en met 100 in"), ]:
            response = self.save(name="Lotte de Boer", **{f"k{self.pct}": raw})
            html = response.get_data(as_text=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(message, html)
            self.assertIn(f'name="kolom-{self.pct}" value="{raw}"', html)
        self.assertIn("kies een waarde uit de lijst", self.save(**{f"k{self.place}": "999"}).get_data(as_text=True))
        self.assertEqual(self.sql("SELECT name FROM students WHERE id = 1"), [("Lotte Bakker",)])
        self.assertEqual(self.values(), {})

    def test_missing_field_is_left_alone(self):   # F3: a column not in the form
        self.sql("INSERT INTO custom_values (student_id, column_id, value) VALUES (1, ?, 'Blijft')", (self.note,))
        self.save(**{f"k{self.pct}": "50"})
        self.assertEqual(self.values(), {self.pct: "50", self.note: "Blijft"})

    def test_add_by_hand(self):   # F5
        html = self.client.get("/studenten/toevoegen/handmatig").get_data(as_text=True)
        self.assertIn("<legend>Eigen kolommen</legend>", html)
        self.client.post("/studenten/toevoegen/handmatig", data={"name": "Iris Bouma", f"kolom-{self.pct}": "60"})
        new = self.sql("SELECT id FROM students WHERE name = 'Iris Bouma'")[0][0]
        self.assertEqual(self.values(new), {self.pct: "60"})


if __name__ == "__main__":
    unittest.main()
