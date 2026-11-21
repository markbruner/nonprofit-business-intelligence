"""Synthetic review-artifact tests; no credentials, network or cloud records."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

from scripts.prepare_cloud_trial import (
    dollar_quote,
    render_trial,
    system_evidence,
    write_new_sql,
)


def fixture():
    rows = []
    selected = {}
    for i, state in enumerate(("OH", "KY", "IN"), 1):
        source_id = str(1000 + i)
        xml_hash = hashlib.sha256(f"SYNTHETIC XML {i}".encode()).hexdigest()
        ein = f"00000000{i}"
        rows.append(
            {
                "filing_key": hashlib.sha256(
                    f"{source_id}\0{xml_hash}".encode()
                ).hexdigest(),
                "source_filing_id": source_id,
                "xml_sha256": xml_hash,
                "ein": ein,
                "tax_period_end": "2025-12-31",
                "tax_year": 2025,
                "form_type": "990",
                "amended": None,
                "total_revenue": 0,
                "total_expenses": None,
                "sources": [
                    {
                        "archive_path": "2026/synthetic.zip",
                        "archive_sha256": "c" * 64,
                        "source_url": "https://example.invalid/synthetic.zip",
                        "downloaded_at": "2026-11-21T12:00:00+00:00",
                        "member": f"{source_id}_public.xml",
                    }
                ],
            }
        )
        selected[state] = {"object_id": source_id, "ein": ein, "tax_period": "202512"}
    return {
        "parser_version": "form990-xml-provisional-v2",
        "manifest_sha256": "b" * 64,
        "filings": rows,
        "report": {
            "status": "complete",
            "issues": [],
            "rejected": 0,
            "unsupported": 0,
            "staged": 3,
        },
    }, {"selection": selected}


class CloudTrialPreparationTests(unittest.TestCase):
    def test_review_template_blocks_missing_evidence_and_preserves_role_controls(self):
        batch, selection = fixture()
        sql, summary = render_trial(batch, selection)
        self.assertFalse(summary["database_contacted"])
        self.assertFalse(summary["system_evidence_supplied"])
        self.assertIn("fresh_system_evidence_required_review_template_only", sql)
        self.assertIn("null::timestamptz", sql)
        self.assertIn("set local role nb_loader_dev", sql)
        self.assertIn("with set false", sql)
        self.assertIn("with inherit false", sql)
        self.assertEqual(2, sql.count("nonprofit_ingest.load_990(payload)"))
        self.assertNotIn("password", sql.lower().replace("-- no passwords", ""))
        self.assertEqual(3, summary["filings"])

    def test_timestamp_units_and_conservative_rounding(self):
        observed, bound = system_evidence(1795271293373000, "167")
        self.assertEqual("2026-11-21T14:28:13.373000+00:00", observed.isoformat())
        self.assertEqual(168 * 1024**2, bound)
        for value in ("NaN", "Infinity", "-1", "0", "2000"):
            with self.assertRaises(ValueError):
                system_evidence(1795271293373000, value)

    def test_selection_and_year_mismatch_rejected(self):
        batch, selection = fixture()
        invalid = deepcopy(selection)
        invalid["selection"]["OH"]["ein"] = "000009999"
        with self.assertRaises(ValueError):
            render_trial(batch, invalid)
        batch["filings"][0]["tax_year"] = 2022
        with self.assertRaises(ValueError):
            render_trial(batch, selection)
        with self.assertRaises(ValueError):
            render_trial(*fixture(), owner="unsafe; role")

    def test_source_dollar_delimiters_remain_literal_data(self):
        text = "$nbi_trial$ $nbi_payload$ $nbi_preflight$"
        quoted = dollar_quote(text, "trial")
        delimiter = quoted[: quoted.index("$", 1) + 1]
        self.assertNotIn(delimiter, text)
        self.assertEqual(text, quoted[len(delimiter) : -len(delimiter)])
        batch, selection = fixture()
        batch["filings"][0]["sources"][0]["member"] = text
        sql, _ = render_trial(
            batch,
            selection,
            observed=datetime.now(timezone.utc),
            system_bound=168 * 1024**2,
        )
        self.assertIn("$nbi_trial_$", sql)

    def test_sql_publication_does_not_replace_existing_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.sql"
            write_new_sql(path, "-- synthetic review only\n")
            with self.assertRaises(FileExistsError):
                write_new_sql(path, "-- must not replace\n")
            self.assertEqual("-- synthetic review only\n", path.read_text())
            self.assertFalse(list(Path(directory).glob("*.part")))


def write_sql_fixtures(output: Path):
    output.mkdir(parents=True, exist_ok=False)
    now = datetime.now(timezone.utc)
    cases = {
        "success": (now, 168 * 1024**2),
        "stale": (now - timedelta(minutes=20), 168 * 1024**2),
        "missing": (None, None),
        "over_budget": (now, 1_800_000_000),
    }
    for name, (observed, bound) in cases.items():
        sql, _ = render_trial(
            *fixture(), observed=observed, system_bound=bound, owner="nbi_trial_owner"
        )
        with (output / f"{name}.sql").open("x", encoding="utf-8") as stream:
            stream.write(sql)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--write-sql-fixtures":
        write_sql_fixtures(Path(sys.argv[2]))
    else:
        unittest.main()
