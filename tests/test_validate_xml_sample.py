"""Synthetic local sample-runner tests: no HTTP, credentials, or database."""

import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from scripts.validate_xml_sample import ARCHIVE, select_candidates, validate_sample


class XmlSampleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.rows = []
        for n, state in enumerate(("OH", "KY", "IN"), 1):
            ein = f"00123456{n}"
            with (self.source / f"eo_{state.lower()}.csv").open(
                "w", newline="", encoding="utf-8"
            ) as stream:
                writer = csv.writer(stream)
                writer.writerow(["EIN", "STATE"])
                writer.writerow([ein, state])
            self.rows.append(
                {
                    "EIN": ein,
                    "RETURN_TYPE": "990",
                    "XML_BATCH_ID": ARCHIVE,
                    "OBJECT_ID": str(1000 + n),
                    "TAX_PERIOD": "202512",
                }
            )
        with (self.source / "index_2026.csv").open(
            "w", newline="", encoding="utf-8"
        ) as stream:
            writer = csv.DictWriter(stream, fieldnames=list(self.rows[0]))
            writer.writeheader()
            writer.writerows(self.rows)
        files = [
            {
                "path": p.name,
                "status": "complete",
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
            for p in self.source.glob("*.csv")
        ]
        (self.source / "source-sample.json").write_text(
            json.dumps({"status": "complete", "files": files}), encoding="utf-8"
        )

    def fake_download(self, batches, output, **options):
        self.assertEqual([(2026, ARCHIVE)], batches)
        self.assertEqual(1, options["max_attempts"])
        archive_path = output / "2026" / f"{ARCHIVE}.zip"
        archive_path.parent.mkdir()
        with ZipFile(archive_path, "w") as archive:
            for row in self.rows:
                archive.writestr(
                    row["OBJECT_ID"] + "_public.xml",
                    f"""<Return xmlns="http://www.irs.gov/efile">
                <ReturnHeader><Filer><EIN>{row['EIN']}</EIN></Filer><ReturnTypeCd>990</ReturnTypeCd>
                <TaxPeriodEndDt>2025-12-31</TaxPeriodEndDt><TaxYr>2025</TaxYr></ReturnHeader>
                <ReturnData><IRS990><CYTotalRevenueAmt>0</CYTotalRevenueAmt>
                <CYTotalExpensesAmt>0</CYTotalExpensesAmt></IRS990></ReturnData></Return>""",
                )
            archive.writestr("9999_public.xml", "invalid unrelated XML")
        options["budget"].consumed = archive_path.stat().st_size
        (output / "manifests").mkdir()
        (output / "manifests" / "synthetic.json").write_text(
            json.dumps(
                {
                    "status": "complete",
                    "files": [
                        {
                            "status": "complete",
                            "path": f"2026/{ARCHIVE}.zip",
                            "sha256": hashlib.sha256(
                                archive_path.read_bytes()
                            ).hexdigest(),
                            "source_url": "https://example.invalid/synthetic.zip",
                            "downloaded_at": "2026-11-21T12:00:00+00:00",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def test_deterministic_selection_and_source_integrity(self):
        plan = select_candidates(self.source)
        self.assertEqual({"OH", "KY", "IN"}, set(plan["selection"]))
        self.assertEqual(plan, select_candidates(self.source))
        (self.source / "eo_oh.csv").write_text("tampered", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "checksum"):
            select_candidates(self.source)

    def test_sample_reuses_downloader_skips_unselected_and_validates_loader_offline(
        self,
    ):
        with patch(
            "scripts.validate_xml_sample.download_series_990_xml",
            side_effect=self.fake_download,
        ):
            report = validate_sample(self.source, self.root / "output")
            self.assertEqual("complete", report["status"])
            self.assertEqual(3, report["index_identity_and_period_checks_passed"])
            self.assertEqual({"2025": 3}, report["tax_year_counts"])
            self.assertEqual(1, report["xml_members_skipped"])
            self.assertFalse(report["database_contacted"])
            with self.assertRaises(FileExistsError):
                validate_sample(self.source, self.root / "output")

    def test_index_mismatch_marks_staging_for_review(self):
        original = self.fake_download

        def mismatched(batches, output, **options):
            self.rows[0]["EIN"] = "009999999"  # fictional mismatch, no real source rows
            original(batches, output, **options)

        with patch(
            "scripts.validate_xml_sample.download_series_990_xml",
            side_effect=mismatched,
        ):
            report = validate_sample(self.source, self.root / "mismatch")
        self.assertEqual("needs_review", report["status"])
        batch = json.loads((self.root / "mismatch" / "staged-filings.json").read_text())
        self.assertEqual("needs_review", batch["report"]["status"])


if __name__ == "__main__":
    unittest.main()
