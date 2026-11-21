"""Check actual tax-2023 coverage in the existing January archive; local only."""

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from scripts.extract_990 import FilingTreeBuilder, XML_NAMESPACE, extract_batch
from scripts.load_supabase import prepare_batch
from scripts.validate_xml_sample import ARCHIVE, _publish_new, select_candidates


def candidate_rows(rows, states):
    """Period end is only a discovery hint, including fiscal years ending in 2024."""
    selected = {}
    for row in rows:
        if (
            row["RETURN_TYPE"] != "990"
            or row["XML_BATCH_ID"] != ARCHIVE
            or row["EIN"] not in states
            or row["TAX_PERIOD"][:4] not in ("2023", "2024")
        ):
            continue
        if (
            not re.fullmatch(r"[0-9]{9}", row["EIN"])
            or not re.fullmatch(r"[0-9]{1,30}", row["OBJECT_ID"])
            or not re.fullmatch(r"[0-9]{4}(0[1-9]|1[0-2])", row["TAX_PERIOD"])
            or states[row["EIN"]] not in ("OH", "KY", "IN")
        ):
            raise ValueError("Index candidate needs review.")
        item = dict(
            ein=row["EIN"], tax_period=row["TAX_PERIOD"], state=states[row["EIN"]]
        )
        key = row["OBJECT_ID"]
        if key in selected and selected[key] != item:
            raise ValueError("Conflicting source identity.")
        selected[key] = item
    if not 1 <= len(selected) <= 500:
        raise ValueError("Expected one to 500 explicit local candidates.")
    return selected


def direct_values(payload):
    """Compare seven staged fields with direct source paths, without logging facts."""
    root = ET.fromstring(payload, parser=ET.XMLParser(target=FilingTreeBuilder()))
    ns = {"i": XML_NAMESPACE} if root.tag.startswith("{" + XML_NAMESPACE + "}") else {}
    prefix = "i:" if ns else ""

    def value(path):
        return (
            root.findtext(
                "/".join(prefix + part for part in path.split("/")), namespaces=ns
            )
            or ""
        ).strip()

    def number(path):
        text = value(path)
        return int(text) if text else None

    version = root.get("returnVersion", "unknown")
    if not re.fullmatch(r"20[0-9]{2}v[0-9]+\.[0-9]+", version):
        version = "unknown"
    return {
        "ein": value("ReturnHeader/Filer/EIN"),
        "tax_year": number("ReturnHeader/TaxYr"),
        "tax_period_end": value("ReturnHeader/TaxPeriodEndDt"),
        "total_revenue": number("ReturnData/IRS990/CYTotalRevenueAmt"),
        "total_expenses": number("ReturnData/IRS990/CYTotalExpensesAmt"),
        "form_type": value("ReturnHeader/ReturnTypeCd"),
        "amended": {"": None, "X": True}[value("ReturnData/IRS990/AmendedReturnInd")],
    }, version


def inspect_batch(manifest, selected):
    batch = extract_batch(manifest, selected_filing_ids=set(selected))
    state_counts, versions, missing = Counter(), Counter(), Counter()
    checks = mismatches = index_mismatches = 0
    target = []
    for row in batch["filings"]:
        indexed = selected[row["source_filing_id"]]
        if (
            row["ein"] != indexed["ein"]
            or row["tax_period_end"].replace("-", "")[:6] != indexed["tax_period"]
        ):
            index_mismatches += 1
        if row["tax_year"] != 2023:
            continue
        target.append(row)
        state_counts[indexed["state"]] += 1
        source = row["sources"][0]
        # extract_batch already verified the manifest, archive path, SHA and sizes.
        archive_path = manifest.parent.parent / source["archive_path"]
        with ZipFile(archive_path) as archive:
            values, version = direct_values(archive.read(source["member"]))
        versions[version] += 1
        for field, value in values.items():
            checks += 1
            mismatches += value != row[field]
            if field != "amended" and (value is None or value == ""):
                missing[field] += 1
    missing_states = sorted({"OH", "KY", "IN"} - set(state_counts))
    complete = (
        not (missing_states or mismatches or index_mismatches)
        and batch["report"]["status"] == "complete"
    )
    target_payload = None
    if complete:
        # Preserve original discovery staging; only validate an explicit tax-2023
        # view after the entire candidate batch passed its quality checks.
        target_payload = prepare_batch(
            {
                **batch,
                "filings": target,
                "report": {**batch["report"], "staged": len(target)},
            },
            "oh-ky-in-tax2023-sample-v1",
        )
    report = {
        "status": "sample_coverage_verified" if complete else "needs_review",
        "archive": ARCHIVE,
        "selected_candidates": len(selected),
        "staged_candidates": len(batch["filings"]),
        "candidate_tax_year_counts": dict(
            Counter(str(r["tax_year"]) for r in batch["filings"])
        ),
        "tax_2023_filings": len(target),
        "tax_2023_state_counts": dict(state_counts),
        "tax_2023_schema_versions": dict(versions),
        "tax_2023_period_end_year_counts": dict(
            Counter(r["tax_period_end"][:4] for r in target)
        ),
        "missing_state_samples": missing_states,
        "direct_field_checks": checks,
        "direct_field_mismatches": mismatches,
        "missing_core_fields": dict(missing),
        "index_mismatches": index_mismatches,
        "quality_reason_counts": dict(
            Counter(i["reason"] for i in batch["report"]["issues"])
        ),
        "tax_2023_amended_true": sum(r["amended"] is True for r in target),
        "tax_2023_amended_unknown": sum(r["amended"] is None for r in target),
        "xml_members_skipped": batch["report"]["xml_skipped_unselected"],
        "database_contacted": False,
        "downloads_performed": False,
        "complete_historical_coverage_verified": False,
        "ready_to_upload": False,
        "offline_loader_contract_passed": target_payload is not None,
        "offline_target_payload_bytes": (
            None
            if target_payload is None
            else len(
                json.dumps(
                    target_payload, sort_keys=True, separators=(",", ":")
                ).encode()
            )
        ),
    }
    return batch, report


def build_check(source, sample):
    verified = select_candidates(source)  # Existing source hash/state checks.
    states = {}
    for state in ("oh", "ky", "in"):
        with (source / f"eo_{state}.csv").open(
            encoding="utf-8-sig", newline=""
        ) as stream:
            for row in csv.DictReader(stream, strict=True):
                states[row["EIN"]] = state.upper()
    with (source / "index_2026.csv").open(encoding="utf-8-sig", newline="") as stream:
        selected = candidate_rows(csv.DictReader(stream, strict=True), states)
    (manifest,) = (sample / "manifests").glob("*.json")
    batch, report = inspect_batch(manifest, selected)
    return verified["source_manifest_sha256"], selected, batch, report


def check(source, sample, output):
    source_hash, selected, batch, report = build_check(source, sample)
    output.mkdir(exist_ok=False)
    _publish_new(
        output / "selection.json",
        {
            "source_manifest_sha256": source_hash,
            "candidates": selected,
        },
    )
    _publish_new(output / "staged-candidates.json", batch)
    _publish_new(output / "coverage-report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("sample", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        root = Path(__file__).resolve().parents[1] / "data"
        if (
            not args.output.resolve().is_relative_to(root.resolve())
            or args.output.exists()
        ):
            raise ValueError("Choose a new output directory under ignored data/.")
        report = check(args.source, args.sample, args.output)
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
    print(json.dumps(report))
    return 0 if report["status"] == "sample_coverage_verified" else 2


if __name__ == "__main__":
    raise SystemExit(main())
