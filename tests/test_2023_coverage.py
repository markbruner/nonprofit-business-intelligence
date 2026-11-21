"""Fictional 2023 coverage fixtures; no network, identities or financial facts."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from scripts.check_2023_coverage import candidate_rows, direct_values, inspect_batch
from scripts.validate_xml_sample import ARCHIVE


def xml(ein="000000001", year="2023", end="2024-06-30"):
    return f"""<Return xmlns="http://www.irs.gov/efile" returnVersion="2023v5.1">
    <ReturnHeader><Filer><EIN>{ein}</EIN></Filer><ReturnTypeCd>990</ReturnTypeCd>
    <TaxYr>{year}</TaxYr><TaxPeriodEndDt>{end}</TaxPeriodEndDt></ReturnHeader>
    <ReturnData><IRS990><CYTotalRevenueAmt>0</CYTotalRevenueAmt>
    <CYTotalExpensesAmt></CYTotalExpensesAmt></IRS990></ReturnData></Return>"""


class Coverage2023Tests(unittest.TestCase):
    def fixture(self, years=("2023", "2023", "2023")):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "manifests").mkdir()
        selected = {}
        archive_path = root / "synthetic.zip"
        with ZipFile(archive_path, "w") as archive:
            for i, (state, year) in enumerate(zip(("OH", "KY", "IN"), years), 1):
                ein = f"{i:09d}"
                archive.writestr(f"{i}_public.xml", xml(ein, year))
                selected[str(i)] = dict(ein=ein, tax_period="202406", state=state)
            archive.writestr("999_public.xml", "malformed unrelated XML")
        manifest = root / "manifests" / "synthetic.json"
        manifest.write_text(
            json.dumps(
                {
                    "status": "complete",
                    "files": [
                        {
                            "status": "complete",
                            "path": "synthetic.zip",
                            "source_url": "https://example.invalid/synthetic.zip",
                            "downloaded_at": "2026-11-21T12:00:00+00:00",
                            "sha256": hashlib.sha256(
                                archive_path.read_bytes()
                            ).hexdigest(),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return manifest, selected

    def test_fiscal_2023_is_counted_from_tax_year_and_fields_preserve_null_zero(self):
        manifest, selected = self.fixture()
        _, report = inspect_batch(manifest, selected)
        self.assertEqual("sample_coverage_verified", report["status"])
        self.assertEqual({"OH": 1, "KY": 1, "IN": 1}, report["tax_2023_state_counts"])
        self.assertEqual(21, report["direct_field_checks"])
        self.assertEqual(0, report["direct_field_mismatches"])
        self.assertEqual({"total_expenses": 3}, report["missing_core_fields"])
        self.assertEqual(1, report["xml_members_skipped"])
        self.assertTrue(report["offline_loader_contract_passed"])
        values, _ = direct_values(xml().encode())
        self.assertEqual(0, values["total_revenue"])
        self.assertIsNone(values["total_expenses"])
        self.assertIsNone(values["amended"])
        amended = xml().replace(
            "<IRS990>", "<IRS990><AmendedReturnInd>X</AmendedReturnInd>"
        )
        self.assertIs(direct_values(amended.encode())[0]["amended"], True)

    def test_index_candidate_year_is_not_tax_year_and_missing_state_is_reported(self):
        manifest, selected = self.fixture(("2023", "2022", "2024"))
        _, report = inspect_batch(manifest, selected)
        self.assertEqual(1, report["tax_2023_filings"])
        self.assertEqual(["IN", "KY"], report["missing_state_samples"])
        self.assertFalse(report["complete_historical_coverage_verified"])
        self.assertFalse(report["ready_to_upload"])
        self.assertFalse(report["offline_loader_contract_passed"])

    def test_index_mismatch_blocks_coverage_claim(self):
        manifest, selected = self.fixture()
        selected["1"]["ein"] = "000000099"
        _, report = inspect_batch(manifest, selected)
        self.assertEqual("needs_review", report["status"])
        self.assertEqual(1, report["index_mismatches"])

    def test_candidate_scope_conflicts_and_bounds(self):
        def row(source_id, period="202406", ein="000000001"):
            return dict(
                EIN=ein,
                OBJECT_ID=source_id,
                TAX_PERIOD=period,
                RETURN_TYPE="990",
                XML_BATCH_ID=ARCHIVE,
            )

        states = {"000000001": "OH", "000000002": "KY"}
        result = candidate_rows(
            [row("1"), row("2", "202312"), row("3", "202512")], states
        )
        self.assertEqual({"1", "2"}, set(result))
        for rows in (
            [row("1"), row("1", ein="000000002")],
            [row("unsafe'")],
            [row("1", "202413")],
            [row("1", "202512")],
        ):
            with self.assertRaises(ValueError):
                candidate_rows(rows, states)

    def test_changed_archive_is_rejected_before_coverage(self):
        manifest, selected = self.fixture()
        with (manifest.parent.parent / "synthetic.zip").open("ab") as stream:
            stream.write(b"changed")
        with self.assertRaises(ValueError):
            inspect_batch(manifest, selected)


if __name__ == "__main__":
    unittest.main()
