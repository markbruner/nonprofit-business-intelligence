"""Exercise the extractor with local, fictional filing archives."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from scripts.extract_990 import extract_batch


def filing(revenue="0", expenses="", form="990", amended=""):
    return f"""<Return xmlns="http://www.irs.gov/efile">
      <ReturnHeader>
        <Filer><EIN>001234567</EIN></Filer>
        <ReturnTypeCd>{form}</ReturnTypeCd>
        <TaxPeriodEndDt>2025-06-30</TaxPeriodEndDt>
        <TaxYr>2024</TaxYr>
        <AmendedReturnInd>{amended}</AmendedReturnInd>
      </ReturnHeader>
      <ReturnData><IRS990>
        <CYTotalRevenueAmt>{revenue}</CYTotalRevenueAmt>
        <CYTotalExpensesAmt>{expenses}</CYTotalExpensesAmt>
      </IRS990></ReturnData>
    </Return>"""


class Extract990Tests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.manifest = self.root / "manifests" / "run.json"
        self.manifest.parent.mkdir()
        self.entries = []

    def write_archive(self, filename, members):
        path = self.root / filename
        with ZipFile(path, "w") as archive:
            for name, contents in members:
                archive.writestr(name, contents)
        self.entries.append(
            {
                "status": "complete",
                "path": filename,
                "source_url": f"https://example.invalid/{filename}",
                "downloaded_at": "2026-11-17T12:30:00+00:00",
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
        self.write_manifest()
        return path

    def write_manifest(self, status="complete"):
        self.manifest.write_text(
            json.dumps({"status": status, "files": self.entries}), encoding="utf-8"
        )

    def test_namespaced_return_preserves_zero_null_and_tax_year(self):
        self.write_archive("one.zip", [("123_public.xml", filing())])
        result = extract_batch(self.manifest)
        (row,) = result["filings"]
        self.assertEqual("001234567", row["ein"])
        self.assertEqual("2025-06-30", row["tax_period_end"])
        self.assertEqual(2024, row["tax_year"])
        self.assertEqual("123", row["source_filing_id"])
        self.assertEqual(0, row["total_revenue"])
        self.assertIsNone(row["total_expenses"])
        self.assertIsNone(row["amended"])
        self.assertEqual("complete", result["report"]["status"])
        self.assertEqual(self.entries[0]["sha256"], row["sources"][0]["archive_sha256"])
        self.assertEqual(
            row["filing_key"], extract_batch(self.manifest)["filings"][0]["filing_key"]
        )

    def test_duplicates_and_conflicts_retain_provenance(self):
        original = filing(revenue="100", expenses="80")
        self.write_archive("first.zip", [("123_public.xml", original)])
        self.write_archive(
            "second.zip",
            [
                ("123_public.xml", original),
                ("other/123_public.xml", filing(revenue="90")),
                ("456_public.xml", filing(revenue="120", amended="1")),
            ],
        )
        batch = extract_batch(self.manifest)
        self.assertEqual(3, len(batch["filings"]))
        self.assertEqual(1, batch["report"]["duplicates"])
        self.assertEqual(2, len(batch["filings"][0]["sources"]))
        self.assertIs(batch["filings"][2]["amended"], True)
        self.assertEqual(
            {"multiple_returns_for_period", "conflicting_source_id"},
            {issue["reason"] for issue in batch["report"]["issues"]},
        )

    def test_invalid_xml_and_unsupported_forms_are_reported(self):
        self.write_archive(
            "bad.zip",
            [
                ("malformed.xml", "<Return>"),
                ("unsupported.xml", filing(form="990EZ")),
                ("entity.xml", "<!DOCTYPE Return><Return/>"),
                ("missing-ein.xml", filing().replace("001234567", "")),
                ("invalid-dollar.xml", filing(revenue="1.5")),
            ],
        )
        result = extract_batch(self.manifest)
        self.assertEqual([], result["filings"])
        self.assertEqual(4, result["report"]["rejected"])
        self.assertEqual(1, result["report"]["unsupported"])
        self.assertEqual("needs_review", result["report"]["status"])
        self.assertEqual(
            {
                "malformed_xml",
                "unsupported_form",
                "xml_doctype",
                "invalid_ein",
                "invalid_amount",
                "no_supported_filings",
            },
            {issue["reason"] for issue in result["report"]["issues"]},
        )

    def test_enforces_xml_member_limit(self):
        self.write_archive("one.zip", [("123_public.xml", filing())])
        with patch("scripts.extract_990.MAX_MEMBER_BYTES", 10):
            report = extract_batch(self.manifest)["report"]
        self.assertEqual("member_too_large", report["issues"][0]["reason"])

    def test_rejects_incomplete_mismatched_or_escaping_archive(self):
        archive = self.write_archive("one.zip", [("123_public.xml", filing())])
        self.write_manifest(status="failed")
        with self.assertRaisesRegex(ValueError, "completed"):
            extract_batch(self.manifest)
        self.write_manifest()
        archive.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            extract_batch(self.manifest)
        self.entries[0]["path"] = "../one.zip"
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "inside the snapshot"):
            extract_batch(self.manifest)

    def test_cli_keeps_prior_output_and_reports_review(self):
        self.write_archive("one.zip", [("malformed.xml", "<Return>")])
        output = self.root / "batch.json"
        command = [
            sys.executable,
            "-B",
            "-m",
            "scripts.extract_990",
            str(self.manifest),
            str(output),
        ]
        result = subprocess.run(command, capture_output=True)
        self.assertEqual(2, result.returncode, result.stderr)
        previous = output.read_bytes()
        self.assertEqual("needs_review", json.loads(previous)["report"]["status"])
        result = subprocess.run(command, capture_output=True)
        self.assertEqual(1, result.returncode)
        self.assertEqual(previous, output.read_bytes())
        self.assertFalse(list(self.root.glob("*.part")))
