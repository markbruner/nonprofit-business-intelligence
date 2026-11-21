"""Stage 30 additional full-990 candidates from existing local sources only."""

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re

from scripts.extract_990 import extract_batch
from scripts.load_supabase import prepare_batch
from scripts.validate_xml_sample import ARCHIVE, _publish_new, select_candidates

SCOPE_VERSION = "oh-ky-in-next-30-v1"


def select_rows(rows, states, excluded, per_state=10):
    """Choose latest indexed filing per new EIN, then deterministic state quotas."""
    if type(per_state) is not int or not 1 <= per_state <= 10:
        raise ValueError("Expected a quota of 1 to 10 per state.")
    candidates = {}
    identifiers = {}
    for row in rows:
        ein = row["EIN"]
        if (
            row["RETURN_TYPE"] != "990"
            or row["XML_BATCH_ID"] != ARCHIVE
            or ein not in states
            or ein in excluded
        ):
            continue
        source_id, period = row["OBJECT_ID"], row["TAX_PERIOD"]
        if (
            states[ein] not in ("OH", "KY", "IN")
            or not re.fullmatch(r"[0-9]{9}", ein)
            or not re.fullmatch(r"[0-9]{1,30}", source_id)
            or not re.fullmatch(r"[0-9]{4}(0[1-9]|1[0-2])", period)
        ):
            raise ValueError("Candidate index identity or period needs review.")
        identity = (ein, period)
        if source_id in identifiers and identifiers[source_id] != identity:
            raise ValueError("Conflicting index identity needs review.")
        identifiers[source_id] = identity
        item = dict(ein=ein, object_id=source_id, tax_period=period, state=states[ein])
        if ein not in candidates or (period, source_id) > (
            candidates[ein]["tax_period"],
            candidates[ein]["object_id"],
        ):
            candidates[ein] = item
    selected = []
    for state in ("OH", "KY", "IN"):
        regional = sorted(
            (r for r in candidates.values() if r["state"] == state),
            key=lambda r: (r["tax_period"], r["object_id"], r["ein"]),
            reverse=True,
        )
        if len(regional) < per_state:
            raise ValueError("Insufficient new candidates for each state.")
        selected.extend(regional[:per_state])
    return selected


def build(source: Path, sample: Path):
    # Reuse the existing snapshot checksum/state/identity validation contract.
    original = select_candidates(source)
    prior = json.loads((sample / "selection.json").read_text(encoding="utf-8"))
    if prior != original:
        raise ValueError("Original trial selection differs from verified sources.")
    states = {}
    for state in ("oh", "ky", "in"):
        with (source / f"eo_{state}.csv").open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f, strict=True):
                states[row["EIN"]] = state.upper()
    with (source / "index_2026.csv").open(encoding="utf-8-sig", newline="") as f:
        selected = select_rows(
            csv.DictReader(f, strict=True),
            states,
            {r["ein"] for r in prior["selection"].values()},
        )
    (manifest,) = (sample / "manifests").glob("*.json")
    batch = extract_batch(
        manifest, selected_filing_ids={r["object_id"] for r in selected}
    )
    indexed = {r["object_id"]: r for r in selected}
    mismatches = sum(
        r["ein"] != indexed[r["source_filing_id"]]["ein"]
        or r["tax_period_end"].replace("-", "")[:6]
        != indexed[r["source_filing_id"]]["tax_period"]
        for r in batch["filings"]
    )
    outside_years = sum(
        r["tax_year"] not in (2023, 2024, 2025) for r in batch["filings"]
    )
    complete = (
        batch["report"]["status"] == "complete"
        and len(batch["filings"]) == 30
        and not mismatches
        and not outside_years
    )
    payload = prepare_batch(batch, SCOPE_VERSION) if complete else None
    report = {
        "status": "complete" if complete else "needs_review",
        "selected": len(selected),
        "staged": len(batch["filings"]),
        "state_counts": dict(Counter(r["state"] for r in selected)),
        "tax_year_counts": dict(Counter(str(r["tax_year"]) for r in batch["filings"])),
        "index_mismatches": mismatches,
        "outside_approved_years": outside_years,
        "quality_reason_counts": dict(
            Counter(r["reason"] for r in batch["report"]["issues"])
        ),
        "payload_bytes": (
            None
            if payload is None
            else len(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            )
        ),
        "minimum_estimated_growth_bytes": 30 * 65536,
        "database_contacted": False,
        "downloads_performed": False,
        "cloud_import_approved": False,
    }
    selection = {
        "source_manifest_sha256": original["source_manifest_sha256"],
        "prior_selection_sha256": hashlib.sha256(
            (sample / "selection.json").read_bytes()
        ).hexdigest(),
        "archive": ARCHIVE,
        "scope_version": SCOPE_VERSION,
        "selection": selected,
    }
    return selection, batch, payload, report


def prepare(source: Path, sample: Path, output: Path):
    selection, batch, payload, report = build(source, sample)
    output.mkdir(exist_ok=False)
    _publish_new(output / "selection.json", selection)
    _publish_new(output / "staged-filings.json", batch)
    if payload is not None:
        _publish_new(output / "load-payload.json", payload)
    _publish_new(output / "validation-report.json", report)
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
            raise ValueError("Choose a NEW output directory under ignored data/.")
        report = prepare(args.source, args.sample, args.output)
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
    return 0 if report["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
