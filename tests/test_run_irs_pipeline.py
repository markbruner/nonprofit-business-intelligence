"""Synthetic pipeline tests. No credentials, network, or real database connection."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock

from scripts.run_irs_pipeline import (
    PipelineLoadError,
    digest,
    execute_prepared,
    plan_batches,
    write_package,
)
from tests.test_load_supabase import staged


def fixture(count=1):
    batch = staged()
    base = batch["filings"][0]
    batch["filings"] = []
    for i in range(count):
        row = deepcopy(base)
        row["tax_year"] = 2023
        row["ein"] = f"{i+1:09d}"
        row["source_filing_id"] = f"synthetic-{i:03d}"
        row["xml_sha256"] = hashlib.sha256(f"SYNTHETIC XML {i}".encode()).hexdigest()
        row["filing_key"] = hashlib.sha256(
            f"{row['source_filing_id']}\0{row['xml_sha256']}".encode()
        ).hexdigest()
        row["sources"][0]["member"] = row["source_filing_id"] + "_public.xml"
        batch["filings"].append(row)
    batch["report"]["staged"] = count
    return batch


class PipelineTests(unittest.TestCase):
    def package(self, batch=None, evidence=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        output = Path(temporary.name) / "package"
        plan = write_package(batch or fixture(), output, evidence=evidence)
        return output, plan

    def connection(self):
        connection = MagicMock()
        connection.autocommit = False
        connection.cursor.return_value.__enter__.return_value.fetchone.return_value = (
            {"status": "complete", "run_key": "a" * 64, "filings": 1},
        )
        return connection

    def test_chunks_are_deterministic_and_maximum_thirty(self):
        batch = fixture(31)
        output, first = self.package(batch)
        batch["filings"].reverse()
        _, second = self.package(batch)
        self.assertEqual(first, second)
        self.assertEqual([30, 1], [r["filings"] for r in first["batches"]])
        with self.assertRaises(FileExistsError):
            write_package(batch, output)

    def test_payload_size_splits_and_oversized_single_record_rejects(self):
        batch = fixture(2)
        source = dict(batch["filings"][0]["sources"][0])
        source.update(
            archive_path="x" * 1500,
            member="x" * 1500,
            source_url="https://example.invalid/" + "x" * 1500,
        )
        for row in batch["filings"]:
            row["sources"] = [dict(source) for _ in range(10)]
        self.assertEqual([1, 1], [len(c["filings"]) for c in plan_batches(batch)])
        batch["filings"][0]["sources"] *= 2
        with self.assertRaises(ValueError):
            plan_batches(batch)

    def test_quality_and_unknown_or_wrong_year_cannot_be_waived(self):
        for kind in ("quality", "unknown", "year"):
            batch = fixture()
            if kind == "quality":
                batch["report"]["issues"] = [{"reason": "synthetic_review"}]
            else:
                batch["filings"][0]["tax_year"] = None if kind == "unknown" else 2024
            with self.assertRaises(ValueError):
                plan_batches(batch)

    def test_explicit_resubmission_sends_identical_payload_without_client_retry(self):
        output, plan = self.package()
        connection = self.connection()
        first = execute_prepared(
            connection, output, "batch-001", expected_plan_sha256=digest(plan)
        )
        second = execute_prepared(
            connection, output, "batch-001", expected_plan_sha256=digest(plan)
        )
        self.assertEqual(first, second)
        cursor = connection.cursor.return_value.__enter__.return_value
        self.assertEqual(2, cursor.execute.call_count)
        self.assertEqual(
            cursor.execute.call_args_list[0], cursor.execute.call_args_list[1]
        )
        self.assertEqual(2, connection.commit.call_count)
        connection.rollback.assert_not_called()

    def test_changed_plan_batch_or_source_evidence_blocks_before_connection(self):
        for kind in ("plan", "batch", "evidence"):
            output, plan = self.package(
                evidence={"coverage-report.json": {"status": "synthetic"}}
            )
            name = {
                "plan": "plan.json",
                "batch": "batch-001.json",
                "evidence": "coverage-report.json",
            }[kind]
            value = json.loads((output / name).read_text())
            value["changed"] = True
            (output / name).write_text(json.dumps(value))
            connection = self.connection()
            with self.assertRaises(ValueError):
                execute_prepared(
                    connection, output, "batch-001", expected_plan_sha256=digest(plan)
                )
            connection.cursor.assert_not_called()

    def test_server_rejection_rolls_back_once_and_suppresses_driver_details(self):
        output, plan = self.package()
        connection = self.connection()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.execute.side_effect = RuntimeError("SYNTHETIC secret DSN and payload")
        with self.assertRaises(PipelineLoadError) as caught:
            execute_prepared(
                connection, output, "batch-001", expected_plan_sha256=digest(plan)
            )
        self.assertNotIn("secret", str(caught.exception))
        cursor.execute.assert_called_once()
        connection.rollback.assert_called_once()
        connection.commit.assert_not_called()

    def test_uncertain_commit_never_retries(self):
        output, plan = self.package()
        connection = self.connection()
        connection.commit.side_effect = RuntimeError("SYNTHETIC connection loss")
        with self.assertRaises(PipelineLoadError):
            execute_prepared(
                connection, output, "batch-001", expected_plan_sha256=digest(plan)
            )
        connection.commit.assert_called_once()
        connection.rollback.assert_called_once()
        connection.cursor.return_value.__enter__.return_value.execute.assert_called_once()

    def test_autocommit_and_path_traversal_block_before_connection(self):
        output, plan = self.package()
        connection = self.connection()
        connection.autocommit = True
        for name in ("batch-001", "../../outside"):
            with self.assertRaises(ValueError):
                execute_prepared(
                    connection, output, name, expected_plan_sha256=digest(plan)
                )
        connection.cursor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
