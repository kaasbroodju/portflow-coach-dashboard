"""Tests for spec 024: custom columns, choice lists and their use in the tables. Invented names."""

import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

from dashboard import create_app, db, excel_import
from dashboard.xlsx_reader import Sheet


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        self.sql("INSERT INTO students (id, name, semester) VALUES (1, 'Lotte Bakker', 3), (2, 'Sem de Wit', 4)")

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

    def item(self, code):
        return self.sql("SELECT id FROM choice_items WHERE code = ?", (code,))[0][0]

    def list_of(self, kind):
        return self.sql("SELECT id FROM choice_lists WHERE kind = ?", (kind,))[0][0]

    def new_column(self, code, name, kind):
        self.client.post("/kolommen/nieuw", data={"code": code, "naam": name, "beschrijving": "", "type": kind})
        return self.sql("SELECT id FROM custom_columns WHERE code = ?", (code,))[0][0]


class TestColumns(Case):
    def test_add_list_and_choice_list(self):   # K1, K2
        self.assertIn("Nog geen eigen kolommen.", self.html("/kolommen"))
        column = self.new_column("WP", "Werkplek", "choice")
        html = self.html("/kolommen")
        self.assertIn("Werkplek", html)
        self.assertIn("Keuzelijst", html)
        self.assertIn("Werkplek", self.html("/keuzelijsten"))
        self.assertEqual(self.sql("SELECT COUNT(*) FROM choice_lists WHERE column_id = ?", (column,))[0][0], 1)

    def test_checks(self):   # K2
        self.new_column("WP", "Werkplek", "text")
        for code, name, kind, message in [("", "X", "text", "Vul een code in."), ("wp", "Ander", "text", "Er is al een kolom"),
                                          ("OC", "X", "text", "is al een vaardigheid"), ("AB", "", "text", "Vul een naam in."),
                                          ("AB", "X", "datum", "Kies een type.")]:
            with self.subTest(code=code, name=name, kind=kind):
                html = self.client.post("/kolommen/nieuw", data={"code": code, "naam": name, "type": kind}).get_data(as_text=True)
                self.assertIn(message, html)

    def test_edit_keeps_type(self):   # K3
        column = self.new_column("WP", "Werkplek", "text")
        self.assertNotIn('name="type"', self.html(f"/kolommen/{column}/bewerken"))
        self.client.post(f"/kolommen/{column}/bewerken", data={"code": "PL2", "naam": "Plek", "type": "choice"})
        self.assertEqual(self.sql("SELECT code, name, type FROM custom_columns"), [("PL2", "Plek", "text")])

    def test_order(self):   # K4
        a, b = self.new_column("A1", "Eerste", "text"), self.new_column("B1", "Tweede", "text")
        self.client.post(f"/kolommen/{b}/omhoog")
        html = self.html("/", f="1")
        self.assertLess(html.index('data-sort="custom-%d"' % b), html.index('data-sort="custom-%d"' % a))

    def test_delete_with_values_and_list(self):   # K5
        column = self.new_column("WP", "Werkplek", "choice")
        lid = self.sql("SELECT id FROM choice_lists WHERE column_id = ?", (column,))[0][0]
        self.client.post(f"/keuzelijsten/{lid}/items", data={"code": "Thuis"})
        self.client.post(f"/studenten/1/kolom/{column}", data={"waarde": str(self.item("Thuis"))})
        self.assertIn("1 student heeft een waarde", self.html("/kolommen", verwijder=column))
        self.client.post(f"/kolommen/{column}/verwijderen")
        self.assertEqual(self.sql("SELECT COUNT(*) FROM custom_values")[0][0], 0)
        self.assertEqual(self.sql("SELECT COUNT(*) FROM choice_items WHERE code = 'Thuis'")[0][0], 0)


class TestChoiceLists(Case):
    def test_standard_lists(self):   # L1, L6
        html = self.html("/keuzelijsten")
        self.assertIn('id="invulling"', html)
        self.assertIn('id="rol"', html)
        self.assertIn("Stage (semester 5, 6 of 7)", html)
        self.assertIn("scrum master", html)

    def test_add_edit_and_unique_code(self):   # L2
        roles = self.list_of("squad_role")
        self.client.post(f"/keuzelijsten/{roles}/items", data={"code": "TL", "omschrijving": "teamleider"})
        self.assertIn("De code sm staat al", self.client.get(
            self.client.post(f"/keuzelijsten/{roles}/items", data={"code": "sm"}).headers["Location"]).get_data(as_text=True))
        sm = self.item("SM")
        self.sql("UPDATE students SET squad_role_id = ? WHERE id = 1", (sm,))
        self.client.post(f"/keuzelijsten/items/{sm}/bewerken", data={"code": "Scrum", "omschrijving": "scrum master"})
        self.assertIn('<span class="role-label">Scrum</span>', self.html("/", f="1", wie="alle"))

    def test_order_counts_in_filters_and_grouping(self):   # L3
        stage = self.item("Stage")
        for _ in range(2):
            self.client.post(f"/keuzelijsten/items/{stage}/omhoog")
        self.sql("UPDATE students SET track_id = ? WHERE id = 1", (self.item("Open projecten"),))
        self.sql("UPDATE students SET track_id = ? WHERE id = 2", (stage,))
        self.sql("INSERT INTO guilds (id, code, name) VALUES (1, 'AI', 'AI')")
        self.sql("INSERT INTO student_guilds (student_id, guild_id) VALUES (1, 1), (2, 1)")
        html = self.html("/", f="1", wie="alle", groep="track")
        self.assertLess(html.index('group-title">Stage<'), html.index('group-title">Open projecten<'))
        options = re.findall(r'<option value="\d+" >([^<]+)</option>', html.split('name="invulling"')[1].split("</select>")[0])
        self.assertEqual(options[0], "Stage (semester 5, 6 of 7)")

    def test_delete_in_use(self):   # L4
        minor = self.item("Minor")
        self.sql("UPDATE students SET track_id = ?", (minor,))
        self.assertIn("2 studenten hebben deze keuze", self.html("/keuzelijsten", verwijder=minor))
        self.client.post(f"/keuzelijsten/items/{minor}/verwijderen")
        self.assertEqual(self.sql("SELECT track_id FROM students"), [(None,), (None,)])

    def test_standard_button(self):   # L5
        tracks = self.list_of("track")
        self.client.post(f"/keuzelijsten/items/{self.item('Afstuderen')}/verwijderen")
        open_projects = self.item("Open projecten")
        self.client.post(f"/keuzelijsten/items/{open_projects}/bewerken", data={"code": "OP", "omschrijving": "Eigen"})
        self.client.post(f"/keuzelijsten/{tracks}/open-ict")
        codes = [r[0] for r in self.sql("SELECT code FROM choice_items WHERE list_id = ? ORDER BY position", (tracks,))]
        self.assertEqual(codes, ["OP", "Open innovatieproject", "Stage", "Minor", "Open projecten", "Afstuderen"])

    def test_migration_of_text_values(self):   # L6
        old = str(Path(self.tmp.name) / "old.sqlite3")
        db.init_db(old)
        conn = sqlite3.connect(old)
        with conn:
            conn.execute("DROP TABLE choice_items")
            conn.execute("DROP TABLE choice_lists")
            conn.execute("ALTER TABLE students DROP COLUMN track_id")
            conn.execute("ALTER TABLE students DROP COLUMN squad_role_id")
            conn.execute("ALTER TABLE students ADD COLUMN squad_role TEXT")
            conn.execute("ALTER TABLE students ADD COLUMN track TEXT")
            conn.execute("INSERT INTO students (name, track, squad_role) VALUES ('A', 'Stage', 'SM'), ('B', 'Werkplaats', NULL)")
        conn.close()
        db.init_db(old)
        conn = sqlite3.connect(old)
        try:
            rows = conn.execute("SELECT s.name, t.code, r.code FROM students s LEFT JOIN choice_items t ON t.id = s.track_id "
                                "LEFT JOIN choice_items r ON r.id = s.squad_role_id ORDER BY s.name").fetchall()
            columns = [r[1] for r in conn.execute("PRAGMA table_info(students)")]
        finally:
            conn.close()
        self.assertEqual(rows, [("A", "Stage", "SM"), ("B", "Werkplaats", None)])
        self.assertNotIn("track", columns)

    def test_reset_refills_standard(self):   # Data: Alles verwijderen
        self.client.post(f"/keuzelijsten/items/{self.item('PO')}/verwijderen")
        self.app.extensions["portflow"].profile_dir = Path(self.tmp.name) / "profile"
        self.client.post("/instellingen/alles-verwijderen", data={"bevestiging": "VERWIJDEREN"})
        self.assertEqual(self.sql("SELECT COUNT(*) FROM choice_items WHERE code = 'PO'")[0][0], 1)


class TestTables(Case):
    def setUp(self):
        super().setUp()
        self.column = self.new_column("WP", "Werkplek", "choice")
        lid = self.sql("SELECT id FROM choice_lists WHERE column_id = ?", (self.column,))[0][0]
        for code in ("Thuis", "Kantoor"):
            self.client.post(f"/keuzelijsten/{lid}/items", data={"code": code})
        self.thuis, self.kantoor = self.item("Thuis"), self.item("Kantoor")

    def test_cell_is_a_list(self):   # G1
        self.assertEqual(self.client.post(f"/studenten/1/kolom/{self.column}", data={"waarde": str(self.thuis)}).status_code, 302)
        for path in ("/", "/studenten"):
            html = self.html(path, f="1", wie="alle")
            self.assertIn(f'<option value="{self.thuis}" selected>Thuis</option>', html)
        self.client.post(f"/studenten/1/kolom/{self.column}", data={"waarde": "999"})
        self.assertEqual(self.sql("SELECT value FROM custom_values"), [(str(self.thuis),)])
        self.client.post(f"/studenten/1/kolom/{self.column}", data={"waarde": ""})
        self.assertEqual(self.sql("SELECT COUNT(*) FROM custom_values")[0][0], 0)

    def test_filter(self):   # G2
        self.client.post(f"/studenten/1/kolom/{self.column}", data={"waarde": str(self.thuis)})
        html = self.html("/", f="1", wie="alle", **{f"kolom{self.column}": str(self.thuis)})
        self.assertIn('data-sort-name="lotte bakker"', html)
        self.assertNotIn('data-sort-name="sem de wit"', html)
        self.assertIn("Alle werkplek", html)
        self.assertIn('data-sort-name="sem de wit"', self.html("/", f="1", wie="alle"))   # without the filter

    def test_grouping(self):   # G3
        self.client.post(f"/studenten/2/kolom/{self.column}", data={"waarde": str(self.kantoor)})
        self.sql("INSERT INTO guilds (id, code, name) VALUES (1, 'AI', 'AI')")
        self.sql("INSERT INTO student_guilds (student_id, guild_id) VALUES (1, 1), (2, 1)")
        html = self.html("/", f="1", wie="alle", groep=f"kolom{self.column}")
        self.assertIn("Groeperen: Werkplek", html)
        self.assertLess(html.index('group-title">Kantoor<'), html.index('group-title">Niet ingevuld<'))

    def test_pencils(self):   # G4
        html = self.html("/studenten")
        self.assertIn('href="/keuzelijsten#invulling"', html)
        self.assertIn('href="/keuzelijsten#rol"', html)
        self.assertIn(f'href="/keuzelijsten#kolom-{self.column}"', html)


class TestExcelImport(Case):
    def preview(self, rows):
        conn = db.connect(self.db_path)
        try:
            sheet = Sheet("Blad1", False, [["Naam", "Coach", "Invulling", "Rol"]] + rows)
            return conn, excel_import.build_preview(conn, sheet, 0, ["name", "coach", "track", "squad_role"])
        except Exception:
            conn.close()
            raise

    def test_lookup_on_code(self):   # E1
        conn, rows = self.preview([["Iris Bouma", "", "stage", "sm"], ["Bas Dekker", "", "Vakantie", ""]])
        try:
            self.assertEqual(rows[0].values["track"][0], self.item("Stage"))
            self.assertEqual(rows[0].values["squad_role"][0], self.item("SM"))
            self.assertIn("Invulling 'Vakantie' niet herkend", rows[1].warnings)
        finally:
            conn.close()

    def test_missing_minor_is_added(self):   # E1
        self.client.post(f"/keuzelijsten/items/{self.item('Minor')}/verwijderen")
        conn, rows = self.preview([["Iris Bouma", "Minor", "", ""]])
        try:
            self.assertEqual(self.sql("SELECT COUNT(*) FROM choice_items WHERE code = 'Minor'")[0][0], 0)   # not yet
            excel_import.apply(conn, rows, selected_new={rows[0].number}, accepted_changes=set(), default_coach_id=None)
        finally:
            conn.close()
        self.assertEqual(self.sql("SELECT t.code FROM students s JOIN choice_items t ON t.id = s.track_id "
                                  "WHERE s.name = 'Iris Bouma'"), [("Minor",)])


if __name__ == "__main__":
    unittest.main()
