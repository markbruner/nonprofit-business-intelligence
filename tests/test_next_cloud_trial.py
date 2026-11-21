"""Synthetic continuation tests and fixtures; no real IRS records or connections."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import sys
import unittest

from scripts.prepare_cloud_trial import render_trial
from tests.test_prepare_cloud_trial import fixture


def next_fixture():
    prior, _ = fixture()
    batch = deepcopy(prior)
    batch["manifest_sha256"] = "d" * 64
    batch["filings"] = []
    selected = []
    for i in range(30):
        row = deepcopy(prior["filings"][0])
        row["ein"] = f"{101+i:09d}"
        row["source_filing_id"] = str(2000 + i)
        row["xml_sha256"] = hashlib.sha256(
            f"SYNTHETIC next XML {i}".encode()
        ).hexdigest()
        row["filing_key"] = hashlib.sha256(
            f"{row['source_filing_id']}\0{row['xml_sha256']}".encode()
        ).hexdigest()
        row["sources"][0]["member"] = f"{row['source_filing_id']}_public.xml"
        batch["filings"].append(row)
        selected.append(
            dict(
                ein=row["ein"],
                object_id=row["source_filing_id"],
                tax_period="202512",
                state=("OH", "KY", "IN")[i // 10],
            )
        )
    batch["report"]["staged"] = 30
    return batch, {"selection": selected}, prior


class NextCloudTrialTests(unittest.TestCase):
    def test_populated_target_fingerprint_and_policy_are_explicit(self):
        batch, selection, prior = next_fixture()
        sql, summary = render_trial(batch, selection, prior_batch=prior)
        self.assertEqual(30, summary["filings"])
        self.assertIn("previous_trial_baseline_changed_review_required", sql)
        self.assertIn("where run_key=encode(sha256", sql)
        self.assertIn("set max_rows=30", sql)
        self.assertIn("fresh_system_evidence_required_review_template_only", sql)
        self.assertIn("on conflict (singleton) do update", sql)
        self.assertIn("organizations) <> 33", sql)
        self.assertIn("import_runs) <> 2", sql)

    def test_overlap_quota_and_year_errors_block_sql(self):
        for case in ("overlap", "quota", "year"):
            batch, selection, prior = next_fixture()
            if case == "overlap":
                batch["filings"][0]["ein"] = prior["filings"][0]["ein"]
            elif case == "quota":
                selection["selection"][0]["state"] = "KY"
            else:
                batch["filings"][0]["tax_year"] = 2022
            with self.assertRaises(ValueError):
                render_trial(batch, selection, prior_batch=prior)

    def test_larger_dashboard_database_category_is_accounted_for(self):
        batch, selection, prior = next_fixture()
        sql, _ = render_trial(
            batch, selection, prior_batch=prior, database_category_bound=27 * 1024**2
        )
        self.assertIn("greatest(28311552-pg_database_size(current_database()),0)", sql)
        with self.assertRaises(ValueError):
            render_trial(
                batch, selection, prior_batch=prior, database_category_bound=-1
            )


def write_fixtures(output):
    output.mkdir(exist_ok=False)
    now = datetime.now(timezone.utc)
    sql, _ = render_trial(
        *fixture(), observed=now, system_bound=169 * 1024**2, owner="nbi_trial_owner"
    )
    (output / "first.sql").write_text(sql, encoding="utf-8")
    for name, observed, bound in (
        ("success", now, 169 * 1024**2),
        ("stale", now - timedelta(minutes=20), 169 * 1024**2),
        ("missing", None, None),
        ("over_budget", now, 1800000000),
    ):
        batch, selection, prior = next_fixture()
        sql, _ = render_trial(
            batch,
            selection,
            prior_batch=prior,
            observed=observed,
            system_bound=bound,
            owner="nbi_trial_owner",
            database_category_bound=27 * 1024**2,
        )
        (output / f"{name}.sql").write_text(sql, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--write-sql-fixtures":
        write_fixtures(Path(sys.argv[2]))
    else:
        unittest.main()
