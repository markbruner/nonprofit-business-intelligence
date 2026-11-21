"""Synthetic selection tests; no downloads or database access."""

import unittest

from scripts.prepare_next_batch import select_rows
from scripts.validate_xml_sample import ARCHIVE


def row(ein, source_id, period="202512"):
    return {
        "EIN": ein,
        "OBJECT_ID": source_id,
        "TAX_PERIOD": period,
        "RETURN_TYPE": "990",
        "XML_BATCH_ID": ARCHIVE,
    }


class NextBatchTests(unittest.TestCase):
    def setUp(self):
        self.states = {
            "000000001": "OH",
            "000000002": "KY",
            "000000003": "IN",
            "000000004": "OH",
        }
        self.rows = [
            row("000000001", "1"),
            row("000000002", "2"),
            row("000000003", "3"),
            row("000000004", "4"),
        ]

    def test_excludes_imported_eins_and_has_stable_state_quotas(self):
        result = select_rows(reversed(self.rows), self.states, {"000000004"}, 1)
        self.assertEqual(["1", "2", "3"], [r["object_id"] for r in result])

    def test_latest_per_ein_keeps_one_organization(self):
        result = select_rows(
            self.rows + [row("000000001", "9", "202412")], self.states, {"000000004"}, 1
        )
        self.assertEqual("1", result[0]["object_id"])

    def test_missing_state_and_malformed_identity_fail(self):
        with self.assertRaises(ValueError):
            select_rows(self.rows[:2], self.states, set(), 1)
        with self.assertRaises(ValueError):
            select_rows(
                self.rows + [row("000000001", "unsafe'", "202512")],
                self.states,
                set(),
                1,
            )
        with self.assertRaises(ValueError):
            select_rows(
                self.rows + [row("000000001", "9", "202513")], self.states, set(), 1
            )

    def test_conflicting_source_id_is_not_silently_selected(self):
        with self.assertRaises(ValueError):
            select_rows(self.rows + [row("000000002", "1")], self.states, set(), 1)

    def test_other_forms_and_archives_do_not_fill_quota(self):
        for field in ("RETURN_TYPE", "XML_BATCH_ID"):
            rows = [dict(r) for r in self.rows[:3]]
            rows[0][field] = "out-of-scope"
            with self.assertRaises(ValueError):
                select_rows(rows, self.states, set(), 1)


if __name__ == "__main__":
    unittest.main()
