"""Tests for spec 034: the evidence timeline on the page of one student. A fake Portflow; invented data."""

import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from dashboard import create_app, evidence, overview

START, END = date(2026, 9, 1), date(2027, 1, 31)
NOW = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)


def item(evidence_id, created, kind="file", goals=(), name="Verslag"):
    return {"id": evidence_id + 1000, "position": 1, "evidence": {
        "id": evidence_id, "name": name, "latest_version_type": kind, "created_at": created,
        "latest_version_created_at": created, "versions_count": 1, "date": None,
        "goals": [{"id": i, "name": g, "nickname": "", "status": "open"} for i, g in enumerate(goals)], "sub_goals": []}}


class FakeApi:
    def __init__(self):
        self.collection_list = {101: (200, [{"id": 1, "name": "Semester 3"}, {"id": 2, "name": "Gilde"}])}
        self.evidence = {(101, 1): (200, [item(1, "2026-10-07T09:00:00Z", goals=("Plannen", "Samenwerken"))]),
                         (101, 2): (200, [item(2, "2026-10-07T15:00:00Z", kind="free_text", goals=("Plannen",)),
                                          item(3, "2026-10-20T09:00:00Z", kind="url", goals=("Beroepstaak SW-RE",)),
                                          item(1, "2026-10-07T09:00:00Z", goals=("Plannen", "Samenwerken"))])}

    def collections(self, token, portfolio_id):
        return self.collection_list.get(portfolio_id, (404, None))

    def collection_evidence(self, token, portfolio_id, collection_id):
        return self.evidence.get((portfolio_id, collection_id), (200, []))


class EvidenceCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        overview.save_semester_period(self.conn, START.isoformat(), END.isoformat())
        with self.conn:
            self.conn.execute("INSERT INTO students (id, name, semester) VALUES (1, 'Lotte Bakker', 3)")
            self.conn.execute("INSERT INTO student_portfolios (student_id, portfolio_id) VALUES (1, 101)")
        self.api = FakeApi()

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def fetch(self, token="token"):
        return evidence.fetch_for_student(self.conn, 1, token, api=self.api, now=lambda: NOW)

    def rows(self):
        return {r["code"]: r["dots"] for r in evidence.timeline(self.conn, 1, START, END)["rows"]}


class TestFetch(EvidenceCase):   # F1
    def test_stores_each_evidence_once_with_collections_and_skills(self):
        self.assertIsNone(self.fetch())
        stored = [tuple(r) for r in self.conn.execute(
            "SELECT evidence_id, kind, collections, skills FROM evidence_items ORDER BY evidence_id")]
        self.assertEqual(stored, [(1, "file", "Semester 3; Gilde", "PL,SW"), (2, "free_text", "Gilde", "PL"),
                                  (3, "url", "Gilde", "")])
        self.assertEqual(evidence.last_fetch(self.conn, 1)["collections"], 2)

    def test_a_new_fetch_replaces_the_old(self):
        self.fetch()
        self.api.evidence = {}
        self.fetch()
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM evidence_items").fetchone()[0], 0)

    def test_problems_keep_what_was_stored(self):
        self.fetch()
        self.assertIn("Niet verbonden", self.fetch(token=None))
        self.api.collection_list[101] = (401, None)
        self.assertIn("accepteert de verbinding niet", self.fetch())
        self.api.collection_list[101] = (500, None)
        self.assertIn("konden niet worden opgehaald", self.fetch())
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM evidence_items").fetchone()[0], 3)

    def test_student_without_portfolio(self):
        with self.conn:
            self.conn.execute("DELETE FROM student_portfolios")
        self.assertIn("niet gekoppeld", self.fetch())


class TestTimeline(EvidenceCase):   # F2-F4
    def test_dots_per_skill_with_count_and_other(self):   # F2 acceptance, F4
        self.fetch()
        rows = self.rows()
        self.assertEqual(list(rows), ["OC", "KO", "JKO", "KPM", "PL", "BD", "SW", "FO", "PH", "RE", "Overig"])
        self.assertEqual([(d["count"], d["kind"]) for d in rows["PL"]], [(2, "mixed")])   # file and text on 7 October
        self.assertEqual([(d["count"], d["kind"]) for d in rows["SW"]], [(1, "file")])
        self.assertEqual([(d["count"], d["kind"]) for d in rows["Overig"]], [(1, "url")])
        self.assertEqual(rows["OC"], [])
        self.assertIn("Verslag (bestand), toegevoegd 7-10-2026, collectie Semester 3; Gilde, PL, SW", rows["SW"][0]["tip"])

    def test_position_follows_the_weeks(self):
        self.fetch()
        dot = self.rows()["SW"][0]   # 7 October: day 37 of 22 weeks starting Monday 31 August
        self.assertAlmostEqual(dot["left"], round(100 * 37.5 / 154, 2))

    def test_outside_the_period_is_left_out(self):
        self.api.evidence = {(101, 1): (200, [item(9, "2026-08-20T09:00:00Z", goals=("Plannen",))])}
        self.fetch()
        self.assertEqual(evidence.timeline(self.conn, 1, START, END)["total"], 0)


class TestPage(EvidenceCase):   # F1, F5
    def setUp(self):
        super().setUp()
        self.app.extensions["portflow"]._token = "token"

    def test_page_shows_stored_and_asks_for_fresh(self):
        html = self.client.get("/studenten/1").get_data(as_text=True)
        self.assertIn('data-fetch="/studenten/1/bewijsstukken"', html)
        self.assertIn("De bewijsstukken worden opgehaald…", html)
        self.fetch()
        html = self.client.get("/studenten/1").get_data(as_text=True)
        self.assertIn('class="evidence-dot evidence-mixed has-count"', html)
        self.assertIn("Bijgewerkt", html)

    def test_fetch_route_without_connection_gives_message(self):   # F1
        response = self.client.post("/studenten/1/bewijsstukken", headers={"X-Requested-With": "fetch"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Niet verbonden met Portflow", response.get_data(as_text=True))
        self.assertEqual(self.client.post("/studenten/99/bewijsstukken").status_code, 404)

    def test_empty_states(self):   # F5
        with self.conn:
            self.conn.execute("INSERT INTO evidence_fetches (student_id, fetched_at, collections) VALUES (1, ?, 0)",
                              (NOW.isoformat(),))
        self.assertIn("geen collecties met je gedeeld", self.client.get("/studenten/1").get_data(as_text=True))
        with self.conn:
            self.conn.execute("UPDATE evidence_fetches SET collections = 2")
        self.assertIn("Nog geen bewijsstukken in deze semesterperiode.",
                      self.client.get("/studenten/1").get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
