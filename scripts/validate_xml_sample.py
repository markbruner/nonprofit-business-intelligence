"""One explicitly scoped local IRS XML validation run; no database access."""

import argparse
from collections import Counter
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from scripts.download_irs import DownloadBudget, download_series_990_xml
from scripts.extract_990 import extract_batch
from scripts.load_supabase import prepare_batch

ARCHIVE = "2026_TEOS_XML_01A"


def select_candidates(source: Path) -> dict:
    """Select one candidate per state without exposing names or addresses."""
    source = Path(source)
    manifest_bytes = (source / "source-sample.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    expected = {"eo_oh.csv", "eo_ky.csv", "eo_in.csv", "index_2026.csv"}
    entries = manifest.get("files", [])
    if (
        manifest.get("status") != "complete"
        or len(entries) != 4
        or {e.get("path") for e in entries} != expected
    ):
        raise ValueError("Expected the completed four-file source snapshot.")
    for entry in entries:
        if entry.get("status") != "complete":
            raise ValueError("Incomplete source entry.")
        with (source / entry["path"]).open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != entry.get("sha256"):
                raise ValueError("Source snapshot checksum mismatch.")
    states = {}
    for state in ("oh", "ky", "in"):
        with (source / f"eo_{state}.csv").open(
            encoding="utf-8-sig", newline=""
        ) as stream:
            for row in csv.DictReader(stream, strict=True):
                if row["STATE"] != state.upper():
                    raise ValueError("Unexpected source state.")
                if row["EIN"] in states and states[row["EIN"]] != state.upper():
                    raise ValueError("Cross-state identity needs review.")
                states[row["EIN"]] = state.upper()
    selected = {}
    with (source / "index_2026.csv").open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream, strict=True):
            if (
                row["RETURN_TYPE"] != "990"
                or row["XML_BATCH_ID"] != ARCHIVE
                or row["EIN"] not in states
            ):
                continue
            state = states[row["EIN"]]
            candidate = {
                "ein": row["EIN"],
                "object_id": row["OBJECT_ID"],
                "tax_period": row["TAX_PERIOD"],
            }
            if state not in selected or (
                candidate["tax_period"],
                candidate["object_id"],
            ) > (selected[state]["tax_period"], selected[state]["object_id"]):
                selected[state] = candidate
    if set(selected) != {"OH", "KY", "IN"}:
        raise ValueError("No candidate for each approved state in the fixed archive.")
    if len({row["object_id"] for row in selected.values()}) != 3 or any(
        not re.fullmatch(r"[0-9]{1,30}", row["object_id"]) for row in selected.values()
    ):
        raise ValueError("Selected object identifiers need review.")
    return {
        "source_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "archive": ARCHIVE,
        "selection": selected,
    }


def _publish_new(path: Path, value: dict) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, suffix=".part", delete=False
        ) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, indent=2)
            stream.write("\n")
        if os.name == "nt":
            temporary.rename(path)  # Windows refuses an existing destination.
        else:
            os.link(temporary, path)  # Atomic, exclusive publication on POSIX.
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def validate_sample(source: Path, output: Path) -> dict:
    plan = select_candidates(source)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    _publish_new(output / "selection.json", plan)
    # This is an operational transfer bound, not the Supabase disk budget.
    budget = DownloadBudget(80_000_000)
    download_series_990_xml(
        [(2026, ARCHIVE)],
        output,
        max_bytes_per_file=80_000_000,
        max_attempts=1,
        budget=budget,
    )
    manifests = list((output / "manifests").glob("*.json"))
    if len(manifests) != 1:
        raise ValueError("Expected one download manifest.")
    expected = {row["object_id"]: row for row in plan["selection"].values()}
    batch = extract_batch(manifests[0], selected_filing_ids=set(expected))
    checks = []
    for row in batch["filings"]:
        indexed = expected[row["source_filing_id"]]
        checks.append(
            row["ein"] == indexed["ein"]
            and row["tax_period_end"].replace("-", "")[:6] == indexed["tax_period"]
        )
    in_year_scope = all(
        row["tax_year"] in (2023, 2024, 2025) for row in batch["filings"]
    )
    if not all(checks):
        batch["report"]["issues"].append(
            {
                "reason": "index_identity_or_period_mismatch",
                "count": len(checks) - sum(checks),
            }
        )
    if not in_year_scope:
        batch["report"]["issues"].append({"reason": "outside_approved_tax_years"})
    if batch["report"]["issues"]:
        batch["report"]["status"] = "needs_review"
    complete = (
        batch["report"]["status"] == "complete"
        and len(checks) == 3
        and all(checks)
        and in_year_scope
    )
    if complete:
        # Offline validation only: no connection, role configuration or DB writes.
        prepare_batch(batch, "oh-ky-in-2023-2025-sample")
    _publish_new(output / "staged-filings.json", batch)
    report = {
        "status": "complete" if complete else "needs_review",
        "archive_payload_bytes": budget.consumed,
        "selected": 3,
        "staged": len(batch["filings"]),
        "index_identity_and_period_checks_passed": sum(checks),
        "tax_year_counts": dict(
            Counter(str(row["tax_year"]) for row in batch["filings"])
        ),
        "all_selected_in_approved_tax_years": in_year_scope,
        "quality_reason_counts": dict(
            Counter(issue["reason"] for issue in batch["report"]["issues"])
        ),
        "xml_members_skipped": batch["report"]["xml_skipped_unselected"],
        "database_contacted": False,
        "complete_historical_coverage_verified": False,
    }
    _publish_new(output / "validation-report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Completed local CSV source snapshot")
    parser.add_argument("output", type=Path, help="NEW ignored local sample snapshot")
    args = parser.parse_args()
    try:
        report = validate_sample(args.source, args.output)
    except Exception as error:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error_type": type(error).__name__,
                    "database_contacted": False,
                }
            )
        )
        return 1
    print(json.dumps(report))  # Aggregate fields only; no identities or amounts.
    return 0 if report["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
