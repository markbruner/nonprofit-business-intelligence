"""Offline preparation and injected-connection loading of Form 990 staging.

No connection creation, environment/credential reads, or I/O at import time.
The database owns the approved scope and storage policy; callers cannot raise it.
"""

import argparse
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_ROWS = 500
PARSER_VERSION = "form990-xml-provisional-v2"
FACT_FIELDS = {
    "filing_key",
    "source_filing_id",
    "xml_sha256",
    "ein",
    "tax_period_end",
    "tax_year",
    "form_type",
    "amended",
    "total_revenue",
    "total_expenses",
}


def _hash(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("Expected a SHA-256 identifier.")


def prepare_batch(batch: dict, scope_version: str) -> dict:
    """Validate extractor output; produce a bounded, deterministic load payload.

    Scope membership, storage policy and fresh measurements are enforced by SQL.
    Findings cannot be waived through this function. Split oversized extraction
    batches upstream; never silently discard rows or quality findings.
    """
    if not isinstance(scope_version, str) or not re.fullmatch(
        r"[A-Za-z0-9_-]{1,80}", scope_version
    ):
        raise ValueError("An explicit scope version is required.")
    if not isinstance(batch, dict) or batch.get("parser_version") != PARSER_VERSION:
        raise ValueError("Unsupported parser version.")
    _hash(batch.get("manifest_sha256"))
    report = batch.get("report")
    if (
        not isinstance(report, dict)
        or report.get("status") != "complete"
        or report.get("issues") != []
        or report.get("rejected") != 0
        or report.get("unsupported") != 0
    ):
        raise ValueError("Only batches without review findings may load.")
    rows = batch.get("filings")
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_ROWS:
        raise ValueError("Expected 1 to 500 filings; split larger batches upstream.")
    if type(report.get("staged")) is not int or report["staged"] != len(rows):
        raise ValueError("Staged count does not match filings.")
    normalized = []
    keys = set()
    periods = set()
    source_ids = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != FACT_FIELDS | {"sources"}:
            raise ValueError("Unexpected filing fields.")
        _hash(row["filing_key"])
        _hash(row["xml_sha256"])
        source_id = row["source_filing_id"]
        if not isinstance(source_id, str) or not re.fullmatch(
            r"[A-Za-z0-9_-]{1,100}", source_id
        ):
            raise ValueError("Invalid source filing ID.")
        expected_key = hashlib.sha256(
            f"{source_id}\0{row['xml_sha256']}".encode()
        ).hexdigest()
        if row["filing_key"] != expected_key:
            raise ValueError("Filing key does not match its source identity.")
        if not isinstance(row["ein"], str) or not re.fullmatch(r"[0-9]{9}", row["ein"]):
            raise ValueError("EIN must retain nine digits.")
        period = row["tax_period_end"]
        if not isinstance(period, str) or not re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}", period
        ):
            raise ValueError("Invalid tax period.")
        date.fromisoformat(period)
        if row["form_type"] != "990":
            raise ValueError("Only full Form 990 is supported.")
        if row["tax_year"] is not None and (
            type(row["tax_year"]) is not int or not 1000 <= row["tax_year"] <= 9999
        ):
            raise ValueError("Invalid tax year.")
        if row["amended"] is not None and type(row["amended"]) is not bool:
            raise ValueError("Invalid amendment indicator.")
        for field in ("total_revenue", "total_expenses"):
            amount = row[field]
            if amount is not None and (
                type(amount) is not int or abs(amount) >= 10**18
            ):
                raise ValueError("Amounts must be whole dollars or null.")
        if (
            row["filing_key"] in keys
            or source_id in source_ids
            or (row["ein"], period) in periods
        ):
            raise ValueError("Duplicate or conflicting filings need review.")
        keys.add(row["filing_key"])
        source_ids.add(source_id)
        periods.add((row["ein"], period))
        sources = row["sources"]
        if not isinstance(sources, list) or not 1 <= len(sources) <= 20:
            raise ValueError("Expected bounded filing provenance.")
        for source in sources:
            if not isinstance(source, dict) or set(source) != {
                "archive_path",
                "archive_sha256",
                "source_url",
                "downloaded_at",
                "member",
            }:
                raise ValueError("Invalid source provenance.")
            _hash(source["archive_sha256"])
            for field in ("archive_path", "source_url", "downloaded_at", "member"):
                if (
                    not isinstance(source[field], str)
                    or not 1 <= len(source[field]) <= 2048
                ):
                    raise ValueError("Missing or oversized provenance.")
            # These are references, never fetched or executed by the loader.
            if not source["source_url"].startswith("https://"):
                raise ValueError("Source reference must use HTTPS.")
            if datetime.fromisoformat(source["downloaded_at"]).tzinfo is None:
                raise ValueError("Source timestamp must include a timezone.")
        normalized.append(dict(row))
    payload = {
        "parser_version": PARSER_VERSION,
        "manifest_sha256": batch["manifest_sha256"],
        "scope_version": scope_version,
        "filings": sorted(normalized, key=lambda row: row["filing_key"]),
    }
    serialized = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    if len(serialized.encode()) > MAX_INPUT_BYTES:
        raise ValueError("Batch exceeds the 2 MiB payload limit.")
    # Independent from extractor run timestamps; facts and provenance are retained.
    return json.loads(serialized)


def load_batch(connection, batch: dict, scope_version: str) -> dict:
    """Use an explicitly provided idle DB-API connection and own its transaction.

    A future approved caller supplies a restricted login granted nb_ingest.
    Do not pass a connection with unrelated pending work: failure rolls it back.
    No automatic retry; an identical completed payload returns the prior receipt.
    """
    payload = prepare_batch(batch, scope_version)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "select nonprofit_ingest.load_990(%s::jsonb)",
                (json.dumps(payload, sort_keys=True, separators=(",", ":")),),
            )
            receipt = cursor.fetchone()[0]
            if isinstance(receipt, str):
                receipt = json.loads(receipt)
            if not isinstance(receipt, dict) or receipt.get("status") != "complete":
                raise ValueError("Database did not return a completed receipt.")
        connection.commit()
        return receipt
    except Exception:
        connection.rollback()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a staging file offline; no database connection."
    )
    parser.add_argument("staging", type=Path)
    parser.add_argument("--scope-version", required=True)
    args = parser.parse_args()
    try:
        with args.staging.open("rb") as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("Staging file exceeds 2 MiB; split upstream.")
        payload = prepare_batch(json.loads(raw), args.scope_version)
    except (OSError, ValueError, TypeError) as error:
        # Do not print exception/source contents, paths, DSNs or row data.
        parser.exit(1, f"Offline validation failed ({type(error).__name__}).\n")
    print(
        json.dumps(
            {
                "status": "validated_offline",
                "filings": len(payload["filings"]),
                "database_contacted": False,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
