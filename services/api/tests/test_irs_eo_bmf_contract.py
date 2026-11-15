import csv
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "config" / "schemas" / "irs_eo_bmf.yaml"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "irs" / "eo_bmf_synthetic.csv"


def load_schema() -> dict:
    # JSON is valid YAML 1.2 and keeps this contract test dependency-free.
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_row(row: dict[str, str], schema: dict) -> list[str]:
    errors = []
    for column in schema["columns"]:
        name = column["name"]
        if name not in row:
            errors.append(f"missing column: {name}")
            continue

        value = row[name]
        if not value:
            if name == "EIN":
                errors.append("EIN is required when a record is present")
            continue

        rules = column["validation"]
        pattern = rules.get("pattern")
        if pattern and not re.fullmatch(pattern, value):
            errors.append(f"invalid {name}: {value}")

        allowed_values = rules.get("allowed_values")
        if allowed_values and value not in allowed_values:
            errors.append(f"invalid {name}: {value}")
    return errors


class EoBmfContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_schema()
        cls.expected_header = [column["name"] for column in cls.schema["columns"]]
        with FIXTURE_PATH.open(newline="", encoding="utf-8") as fixture:
            reader = csv.DictReader(fixture)
            cls.fixture_header = reader.fieldnames
            cls.rows = list(reader)

    def test_fixture_header_matches_documented_source_columns(self) -> None:
        self.assertEqual(self.expected_header, self.fixture_header)

    def test_leading_zero_ein_is_preserved_and_valid(self) -> None:
        row = self.rows[0]
        self.assertEqual("001234567", row["EIN"])
        self.assertEqual([], validate_row(row, self.schema))

    def test_all_synthetic_records_are_valid(self) -> None:
        for row in self.rows:
            with self.subTest(ein=row["EIN"]):
                self.assertEqual([], validate_row(row, self.schema))

    def test_missing_required_ein_is_invalid(self) -> None:
        row = self.rows[0].copy()
        row["EIN"] = ""
        self.assertIn("EIN is required when a record is present", validate_row(row, self.schema))

    def test_missing_source_column_is_invalid(self) -> None:
        row = self.rows[0].copy()
        row.pop("TAX_PERIOD")
        self.assertIn("missing column: TAX_PERIOD", validate_row(row, self.schema))

    def test_invalid_code_is_rejected(self) -> None:
        row = self.rows[0].copy()
        row["AFFILIATION"] = "5"
        self.assertIn("invalid AFFILIATION: 5", validate_row(row, self.schema))

    def test_invalid_date_formats_are_rejected(self) -> None:
        row = self.rows[0].copy()
        row["RULING"] = "201513"
        row["TAX_PERIOD"] = "20241"
        errors = validate_row(row, self.schema)
        self.assertIn("invalid RULING: 201513", errors)
        self.assertIn("invalid TAX_PERIOD: 20241", errors)


if __name__ == "__main__":
    unittest.main()
