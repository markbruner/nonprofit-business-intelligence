"""Synthetic loader tests. No database, credentials or network access."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from scripts.load_supabase import load_batch, prepare_batch


def staged():
    xml_hash = "a" * 64
    key = hashlib.sha256(f"synthetic-001\0{xml_hash}".encode()).hexdigest()
    return {
        "parser_version": "form990-xml-provisional-v2",
        "manifest_sha256": "b" * 64,
        "report": {
            "status": "complete",
            "issues": [],
            "rejected": 0,
            "unsupported": 0,
            "staged": 1,
        },
        "filings": [
            {
                "filing_key": key,
                "source_filing_id": "synthetic-001",
                "xml_sha256": xml_hash,
                "ein": "001234567",
                "tax_period_end": "2025-06-30",
                "tax_year": 2024,
                "form_type": "990",
                "amended": None,
                "total_revenue": 0,
                "total_expenses": None,
                "sources": [
                    {
                        "archive_path": "synthetic.zip",
                        "archive_sha256": "c" * 64,
                        "source_url": "https://example.invalid/synthetic.zip",
                        "downloaded_at": "2026-11-21T12:00:00+00:00",
                        "member": "synthetic-001_public.xml",
                    }
                ],
            }
        ],
    }


class LoaderTests(unittest.TestCase):
    def test_zero_null_provenance_and_stable_payload(self):
        batch = staged()
        original = deepcopy(batch)
        payload = prepare_batch(batch, "synthetic-scope-v1")
        row = payload["filings"][0]
        self.assertEqual("001234567", row["ein"])
        self.assertEqual(0, row["total_revenue"])
        self.assertIsNone(row["total_expenses"])
        self.assertEqual(original, batch)
        batch["report"]["finished_at"] = "ignored run timestamp"
        self.assertEqual(payload, prepare_batch(batch, "synthetic-scope-v1"))

    def test_review_missing_and_unsupported_batches_rejected(self):
        changes = [
            ("status", "needs_review"),
            ("issues", [{"reason": "conflict"}]),
            ("rejected", 1),
            ("unsupported", 1),
            ("staged", 2),
        ]
        for field, value in changes:
            with self.subTest(field=field):
                batch = staged()
                batch["report"][field] = value
                with self.assertRaises(ValueError):
                    prepare_batch(batch, "synthetic-v1")
        for field in ("report", "manifest_sha256", "parser_version", "filings"):
            batch = staged()
            del batch[field]
            with self.assertRaises(ValueError):
                prepare_batch(batch, "synthetic-v1")

    def test_bad_types_keys_dates_and_amounts_rejected_before_connection(self):
        mutations = {
            "ein": 1234567,
            "filing_key": "d" * 64,
            "total_revenue": True,
            "total_expenses": 10**18,
            "tax_year": True,
            "tax_period_end": "2025-02-30",
            "amended": "false",
            "form_type": "990EZ",
            "source_filing_id": "x'); drop table x;--",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                batch = staged()
                batch["filings"][0][field] = value
                connection = MagicMock()
                with self.assertRaises(ValueError):
                    load_batch(connection, batch, "synthetic-v1")
                connection.cursor.assert_not_called()

    def test_duplicate_and_conflicting_period_rejected(self):
        for duplicate in (True, False):
            batch = staged()
            row = deepcopy(batch["filings"][0])
            if not duplicate:
                row["source_filing_id"] = "synthetic-002"
                row["filing_key"] = hashlib.sha256(
                    f"synthetic-002\0{row['xml_sha256']}".encode()
                ).hexdigest()
            batch["filings"].append(row)
            batch["report"]["staged"] = 2
            with self.assertRaisesRegex(ValueError, "conflicting"):
                prepare_batch(batch, "synthetic-v1")

    def test_provenance_limits_scope_and_payload_boundaries(self):
        for field, value in (
            ("downloaded_at", "2026-11-21"),
            ("archive_sha256", "bad"),
            ("source_url", "file:///secret"),
            ("member", "x" * 2049),
        ):
            batch = staged()
            batch["filings"][0]["sources"][0][field] = value
            with self.assertRaises(ValueError):
                prepare_batch(batch, "synthetic-v1")
        for scope in (None, "", "../../outside", "x" * 81):
            with self.assertRaises(ValueError):
                prepare_batch(staged(), scope)
        with patch("scripts.load_supabase.MAX_INPUT_BYTES", 10):
            with self.assertRaisesRegex(ValueError, "payload"):
                prepare_batch(staged(), "synthetic-v1")
        batch = staged()
        batch["filings"] = []
        with self.assertRaises(ValueError):
            prepare_batch(batch, "synthetic-v1")

    def test_parameterized_call_commits_only_after_receipt(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        receipt = {"status": "complete", "run_key": "d" * 64, "filings": 1}
        cursor.fetchone.return_value = (receipt,)
        self.assertEqual(receipt, load_batch(connection, staged(), "synthetic-v1"))
        sql, parameters = cursor.execute.call_args.args
        self.assertEqual("select nonprofit_ingest.load_990(%s::jsonb)", sql)
        self.assertEqual("001234567", json.loads(parameters[0])["filings"][0]["ein"])
        connection.commit.assert_called_once()
        connection.rollback.assert_not_called()

    def test_database_failures_and_unknown_receipts_roll_back_without_retry(self):
        for error in (
            "capacity_missing",
            "storage_budget_exceeded",
            "outside_approved_scope",
            "capacity_stale",
            "permission denied",
            "connection interrupted",
        ):
            connection = MagicMock()
            cursor = connection.cursor.return_value.__enter__.return_value
            cursor.execute.side_effect = RuntimeError(error)
            with self.assertRaises(RuntimeError):
                load_batch(connection, staged(), "synthetic-v1")
            cursor.execute.assert_called_once()
            connection.commit.assert_not_called()
            connection.rollback.assert_called_once()
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value.fetchone.return_value = (
            {"status": "running"},
        )
        with self.assertRaises(ValueError):
            load_batch(connection, staged(), "synthetic-v1")
        connection.rollback.assert_called_once()

    def test_offline_cli_reports_counts_without_row_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.json"
            path.write_text(json.dumps(staged()), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "scripts.load_supabase",
                    str(path),
                    "--scope-version",
                    "synthetic-v1",
                ],
                capture_output=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertFalse(json.loads(result.stdout)["database_contacted"])
            self.assertNotIn(b"001234567", result.stdout)
            path.write_text("invalid private-like content", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "scripts.load_supabase",
                    str(path),
                    "--scope-version",
                    "synthetic-v1",
                ],
                capture_output=True,
            )
            self.assertEqual(1, result.returncode)
            self.assertNotIn(b"private-like", result.stderr)


if __name__ == "__main__":
    unittest.main()
