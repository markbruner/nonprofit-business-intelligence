"""Prepare repeatable tax-2023 batches locally; injected loading has no connection setup."""

import argparse
import hashlib
import json
from pathlib import Path
import re

from scripts.check_2023_coverage import build_check
from scripts.load_supabase import MAX_INPUT_BYTES, load_batch, prepare_batch
from scripts.prepare_cloud_trial import PROJECT_REF
from scripts.validate_xml_sample import _publish_new

SCOPE_VERSION = "oh-ky-in-tax2023-sample-v1"
MAX_ROWS = 30
MAX_PAYLOAD_BYTES = 65536


class PipelineLoadError(RuntimeError):
    """Sanitized failure; inspect server state before any explicit resubmission."""


def encoded(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def staging_view(batch, rows):
    # Only called after checking the complete parent report. No findings waived.
    return {
        "parser_version": batch["parser_version"],
        "manifest_sha256": batch["manifest_sha256"],
        "filings": rows,
        "report": {
            "status": "complete",
            "issues": [],
            "rejected": 0,
            "unsupported": 0,
            "staged": len(rows),
        },
    }


def plan_batches(batch):
    """Validate all input first, then split deterministically under current limits."""
    payload = prepare_batch(batch, SCOPE_VERSION)
    if any(r["tax_year"] != 2023 for r in payload["filings"]):
        raise ValueError("This runner is scoped to explicit XML tax year 2023.")
    chunks = []
    pending = []
    for row in payload["filings"]:
        candidate = pending + [row]
        view = staging_view(batch, candidate)
        # Default whitespace/ASCII encoding conservatively estimates JSONB text;
        # the server independently enforces actual octet_length(payload::text).
        size = len(
            json.dumps(prepare_batch(view, SCOPE_VERSION), sort_keys=True).encode()
        )
        if len(candidate) > MAX_ROWS or size > MAX_PAYLOAD_BYTES:
            if not pending:
                raise ValueError("One filing exceeds the current payload limit.")
            chunks.append(staging_view(batch, pending))
            pending = [row]
            single = prepare_batch(staging_view(batch, pending), SCOPE_VERSION)
            if len(json.dumps(single, sort_keys=True).encode()) > MAX_PAYLOAD_BYTES:
                raise ValueError("One filing exceeds the current payload limit.")
        else:
            pending = candidate
    if pending:
        chunks.append(staging_view(batch, pending))
    return chunks


def write_package(batch, output, *, evidence=None):
    chunks = plan_batches(batch)
    output.mkdir(exist_ok=False)
    for name, value in (evidence or {}).items():
        if not re.fullmatch(r"[a-z-]+\.json", name):
            raise ValueError("Invalid evidence filename.")
        _publish_new(output / name, value)
    items = []
    for i, chunk in enumerate(chunks, 1):
        name = f"batch-{i:03d}"
        payload = prepare_batch(chunk, SCOPE_VERSION)
        _publish_new(output / f"{name}.json", chunk)
        items.append(
            {
                "id": name,
                "staging_sha256": digest(chunk),
                "payload_sha256": digest(payload),
                "filings": len(payload["filings"]),
            }
        )
    plan = {
        "version": 1,
        "project_ref": PROJECT_REF,
        "scope_version": SCOPE_VERSION,
        "max_rows": MAX_ROWS,
        "max_payload_bytes": MAX_PAYLOAD_BYTES,
        "tax_year": 2023,
        "batches": items,
        "evidence_sha256": {
            name: digest(value) for name, value in (evidence or {}).items()
        },
    }
    # Written last: a partial publication has no complete plan.
    _publish_new(output / "plan.json", plan)
    return plan


def read_json(path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("Input exceeds local size bound.")
    return json.loads(raw)


def execute_prepared(connection, package, batch_id, *, expected_plan_sha256):
    """One explicitly selected batch; caller supplies an idle non-autocommit connection.

    A separately reviewed caller must connect as the restricted loader, after the
    owner seeds approved scope/current capacity. No credential reads or automatic
    retry. The expected digest must come from the reviewed plan, not be recomputed
    from untrusted package contents at execution time. DB policy remains authority.
    """
    if not re.fullmatch(r"[0-9a-f]{64}", expected_plan_sha256):
        raise ValueError("A reviewed plan digest is required.")
    if not re.fullmatch(r"batch-[0-9]{3}", batch_id):
        raise ValueError("Invalid batch identifier.")
    package = Path(package)

    def package_json(name):
        path = (package / name).resolve()
        if not path.is_relative_to(package.resolve()):
            raise ValueError("Artifact path escapes package.")
        return read_json(path)

    plan = package_json("plan.json")
    if digest(plan) != expected_plan_sha256 or (
        plan.get("version"),
        plan.get("project_ref"),
        plan.get("scope_version"),
        plan.get("max_rows"),
        plan.get("max_payload_bytes"),
        plan.get("tax_year"),
    ) != (1, PROJECT_REF, SCOPE_VERSION, MAX_ROWS, MAX_PAYLOAD_BYTES, 2023):
        raise ValueError("Reviewed plan changed or is unsupported.")
    for name, expected in plan["evidence_sha256"].items():
        if (
            not re.fullmatch(r"[a-z-]+\.json", name)
            or digest(package_json(name)) != expected
        ):
            raise ValueError("Source evidence changed.")
    entries = [item for item in plan["batches"] if item["id"] == batch_id]
    if len(entries) != 1:
        raise ValueError("Batch is absent or ambiguous.")
    entry = entries[0]
    batch = package_json(f"{batch_id}.json")
    payload = prepare_batch(batch, SCOPE_VERSION)
    if (
        digest(batch) != entry["staging_sha256"]
        or digest(payload) != entry["payload_sha256"]
    ):
        raise ValueError("Prepared batch changed.")
    if (
        not 1 <= len(payload["filings"]) <= MAX_ROWS
        or len(payload["filings"]) != entry["filings"]
    ):
        raise ValueError("Batch count changed or exceeds limits.")
    if (
        any(r["tax_year"] != 2023 for r in payload["filings"])
        or len(json.dumps(payload, sort_keys=True).encode()) > MAX_PAYLOAD_BYTES
    ):
        raise ValueError("Prepared batch exceeds year/payload scope.")
    if getattr(connection, "autocommit", False) is not False:
        raise ValueError("An idle non-autocommit connection is required.")
    try:
        receipt = load_batch(connection, batch, SCOPE_VERSION)
        if receipt.get("filings") != entry["filings"] or not re.fullmatch(
            r"[0-9a-f]{64}", receipt.get("run_key", "")
        ):
            raise ValueError("Unexpected committed receipt.")
    except Exception:
        # Driver text may include DSNs or values. No retry, and no raw exception chain.
        raise PipelineLoadError(
            "database_call_failed_or_commit_uncertain_review_before_retry"
        ) from None
    return {
        "status": "complete",
        "batch_id": batch_id,
        "filings": entry["filings"],
        "run_key": receipt["run_key"],
        "plan_sha256": expected_plan_sha256,
    }


def prepare_2023(source, sample, output):
    source_hash, selected, discovery, report = build_check(source, sample)
    if report["status"] != "sample_coverage_verified":
        raise ValueError("Coverage/quality findings require review before preparation.")
    rows = [r for r in discovery["filings"] if r["tax_year"] == 2023]
    batch = staging_view(discovery, rows)
    plan = write_package(
        batch,
        output,
        evidence={
            "coverage-report.json": report,
            "source-selection.json": {
                "source_manifest_sha256": source_hash,
                "candidates": selected,
            },
            "staged-candidates.json": discovery,
        },
    )
    return {
        "status": "prepared_for_review",
        "tax_year": 2023,
        "filings": len(rows),
        "batches": len(plan["batches"]),
        "plan_sha256": digest(plan),
        "database_contacted": False,
        "cloud_import_approved": False,
    }


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
            raise ValueError("Choose a new package under ignored data/.")
        summary = prepare_2023(args.source, args.sample, args.output)
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
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
