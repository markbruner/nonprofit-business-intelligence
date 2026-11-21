"""Explicitly invoked IRS downloads; importing this module performs no I/O."""

from collections.abc import Callable
import argparse
import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import tempfile
import time
from uuid import uuid4
from zipfile import BadZipFile, ZipFile
from zlib import error as ZlibError

import requests

EO_URL = "https://www.irs.gov/pub/irs-soi/eo_{state}.csv"
SERIES_990_INDEX_URL = (
    "https://apps.irs.gov/pub/epostcard/990/xml/{year}/index_{year}.csv"
)
SERIES_990_XML_URL = (
    "https://apps.irs.gov/pub/epostcard/990/xml/{year}/{xml_batch_id}.zip"
)
INDEX_REQUIRED_COLUMNS = {"EIN", "TAX_PERIOD", "OBJECT_ID"}
EO_REQUIRED_COLUMNS = {
    "EIN",
    "NAME",
    "STREET",
    "CITY",
    "STATE",
    "ZIP",
    "NTEE_CD",
    "SUBSECTION",
    "STATUS",
    "TAX_PERIOD",
    "REVENUE_AMT",
}


@dataclass
class DownloadBudget:
    """Response-payload bytes consumed across all files/attempts, not wire overhead."""

    limit: int
    consumed: int = 0

    def __post_init__(self):
        if type(self.limit) is not int or self.limit <= 0 or self.consumed != 0:
            raise ValueError("Expected a fresh positive download budget.")


def _bounded_chunks(response, max_bytes: int, budget: DownloadBudget):
    """Read identity payload without ever requesting bytes beyond either cap."""
    if response.status_code != 200:
        raise ValueError("Bounded downloads require HTTP 200 without redirects.")
    if response.headers.get("Content-Encoding", "identity").lower() not in (
        "",
        "identity",
    ):
        raise ValueError("Compressed responses are not allowed for bounded downloads.")
    raw_length = response.headers.get("Content-Length")
    expected = None
    if raw_length is not None:
        if not re.fullmatch(r"[0-9]+", raw_length):
            raise ValueError("Invalid response length.")
        expected = int(raw_length)
        if expected > min(max_bytes, budget.limit - budget.consumed):
            raise ValueError("Declared response exceeds download budget.")
    received = 0
    while expected is None or received < expected:
        remaining = min(max_bytes - received, budget.limit - budget.consumed)
        if remaining <= 0:
            # Unknown-length responses at the exact cap fail closed: do not read
            # an extra byte merely to discover whether the server has more data.
            raise ValueError("Download budget exhausted before confirmed EOF.")
        amount = min(8192, remaining)
        if expected is not None:
            amount = min(amount, expected - received)
        chunk = response.raw.read(amount, decode_content=False)
        if not chunk:
            if expected is not None and received != expected:
                raise ValueError("Response ended before its declared length.")
            return
        budget.consumed += len(chunk)
        received += len(chunk)
        if len(chunk) > amount:
            raise ValueError("Response reader exceeded requested byte limit.")
        yield chunk


eo_states = {
    "alabama": "al",
    "alaska": "ak",
    "arizona": "az",
    "arkansas": "ar",
    "california": "ca",
    "colorado": "co",
    "connecticut": "ct",
    "delaware": "de",
    "district-of-columbia": "dc",
    "florida": "fl",
    "georgia": "ga",
    "hawaii": "hi",
    "idaho": "id",
    "illinois": "il",
    "indiana": "in",
    "iowa": "ia",
    "kansas": "ks",
    "kentucky": "ky",
    "louisiana": "la",
    "maine": "me",
    "maryland": "md",
    "massachusetts": "ma",
    "michigan": "mi",
    "minnesota": "mn",
    "mississippi": "ms",
    "missouri": "mo",
    "montana": "mt",
    "nebraska": "ne",
    "nevada": "nv",
    "new-hampshire": "nh",
    "new-jersey": "nj",
    "new-mexico": "nm",
    "new-york": "ny",
    "north-carolina": "nc",
    "north-dakota": "nd",
    "ohio": "oh",
    "oklahoma": "ok",
    "oregon": "or",
    "pennsylvania": "pa",
    "rhode-island": "ri",
    "south-carolina": "sc",
    "south-dakota": "sd",
    "tennessee": "tn",
    "texas": "tx",
    "utah": "ut",
    "vermont": "vt",
    "virginia": "va",
    "washington": "wa",
    "west-virginia": "wv",
    "wisconsin": "wi",
    "wyoming": "wy",
}


@dataclass(frozen=True)
class DownloadResult:
    """Metadata for completed bytes, not proof of source-schema validity."""

    source_url: str
    local_path: Path
    downloaded_at: datetime
    byte_count: int
    sha256: str
    response_headers: dict[str, str] = field(default_factory=dict)


def build_eo_url(state: str) -> str:
    """Accept a state name or postal abbreviation, ignoring case/spacing."""
    normalized = "-".join(state.strip().lower().replace("-", " ").split())
    abbreviation = eo_states.get(normalized)
    if abbreviation is None and normalized in eo_states.values():
        abbreviation = normalized
    if abbreviation is None:
        raise ValueError(f"State '{state}' is not a supported state name or code.")
    return EO_URL.format(state=abbreviation)


def _validate_year(year: int) -> None:
    if type(year) is not int or not 1000 <= year <= 9999:
        raise ValueError("Index and archive years must be four-digit integers.")


def build_series_990_index_url(year: int) -> str:
    """Build the URL for the 990 XML index for a given year."""
    _validate_year(year)
    return SERIES_990_INDEX_URL.format(year=year)


def build_series_990_xml_url(year: int, xml_batch_id: str) -> str:
    """Build the URL for a specific 990 XML file."""
    _validate_year(year)
    if (
        not isinstance(xml_batch_id, str)
        or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", xml_batch_id)
        or re.fullmatch(r"CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9]", xml_batch_id.upper())
    ):
        raise ValueError(
            "Expected a safe IRS archive basename without the .zip suffix."
        )
    return SERIES_990_XML_URL.format(year=year, xml_batch_id=xml_batch_id)


def download_file(
    url: str,
    destination: Path,
    *,
    validate: Callable[[Path], None] | None = None,
    max_bytes: int | None = None,
    max_attempts: int = 3,
    budget: DownloadBudget | None = None,
) -> DownloadResult:
    """Download one file with at most three attempts and atomic publication.

    Existing destinations are replaced only after a nonempty download succeeds.
    Each request uses 10-second connect and 60-second read inactivity timeouts;
    these are not an overall download deadline. HTTP 429/500/502/503/504 and
    connection/read failures are retried after 0.5 and 1 second. Local I/O errors,
    empty bodies, validation failures, and other HTTP errors fail immediately.
    """
    if type(max_attempts) is not int or not 1 <= max_attempts <= 3:
        raise ValueError("Expected one to three attempts.")
    if max_bytes is not None and (type(max_bytes) is not int or max_bytes <= 0):
        raise ValueError("Expected a positive per-file byte limit.")
    if budget is not None and max_bytes is None:
        raise ValueError("A shared budget also requires a per-file limit.")
    if max_bytes is not None and budget is None:
        budget = DownloadBudget(max_bytes)
    if budget is not None and budget.consumed >= budget.limit:
        raise ValueError("Download budget is already exhausted.")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    retry_statuses = {429, 500, 502, 503, 504}
    for attempt in range(max_attempts):
        temporary_path = None
        try:
            digest = hashlib.sha256()
            byte_count = 0
            request_options = {"stream": True, "timeout": (10, 60)}
            if max_bytes is not None:
                request_options.update(
                    allow_redirects=False, headers={"Accept-Encoding": "identity"}
                )
            with requests.get(url, **request_options) as response:
                response.raise_for_status()
                with tempfile.NamedTemporaryFile(
                    dir=destination.parent,
                    prefix=f".{destination.name}.",
                    suffix=".part",
                    delete=False,
                ) as temporary:
                    temporary_path = Path(temporary.name)
                    chunks = (
                        response.iter_content(chunk_size=8192)
                        if max_bytes is None
                        else _bounded_chunks(response, max_bytes, budget)
                    )
                    for chunk in chunks:
                        if chunk:
                            temporary.write(chunk)
                            digest.update(chunk)
                            byte_count += len(chunk)
            if byte_count == 0:
                raise ValueError(f"Empty download from {url}")
            if validate is not None:
                validate(temporary_path)
            result = DownloadResult(
                source_url=url,
                local_path=destination,
                downloaded_at=datetime.now(timezone.utc),
                byte_count=byte_count,
                sha256=digest.hexdigest(),
                response_headers={
                    name: response.headers[name]
                    for name in (
                        "Content-Type",
                        "Content-Length",
                        "Content-Encoding",
                        "ETag",
                        "Last-Modified",
                    )
                    if name in response.headers
                },
            )
            temporary_path.replace(destination)
            return result
        except requests.RequestException as error:
            status = error.response.status_code if error.response is not None else None
            retryable = (
                isinstance(error, requests.HTTPError) and status in retry_statuses
            ) or isinstance(
                error,
                (
                    requests.ConnectionError,
                    requests.Timeout,
                    requests.exceptions.ChunkedEncodingError,
                ),
            )
            if not retryable or attempt == max_attempts - 1:
                raise
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        time.sleep(0.5 * (2**attempt))
    raise AssertionError("Unreachable: download attempts exhausted")


def download_eo_files(states: list[str], output_dir: Path) -> list[DownloadResult]:
    """Validate the whole batch, then download each distinct state sequentially.

    Empty input does no I/O. Aliases/duplicates are downloaded once in input
    order. A failure stops the batch and annotates the exception; previously
    completed files remain. No Supabase writes or automatic scheduling occur.
    """
    urls = list(dict.fromkeys(build_eo_url(state) for state in states))
    results = []
    for url in urls:
        destination = Path(output_dir) / url.rsplit("/", 1)[-1]
        try:
            results.append(download_file(url, destination))
        except (requests.RequestException, OSError, ValueError) as error:
            error.add_note(
                f"Batch stopped at {url}; {len(results)} earlier file(s) completed. "
                "Completed files remain in the output directory."
            )
            raise
    return results


def _validate_index(path: Path) -> None:
    try:
        with path.open(encoding="utf-8-sig", newline="") as file:
            header = next(csv.reader(file, strict=True), [])
    except (UnicodeError, csv.Error) as error:
        raise ValueError("Could not read the Form 990 index CSV header.") from error
    if not INDEX_REQUIRED_COLUMNS.issubset(header) or len(set(header)) != len(header):
        raise ValueError("Form 990 index CSV has missing or duplicate header columns.")


def _validate_xml_archive(path: Path) -> None:
    try:
        with ZipFile(path) as archive:
            for item in archive.infolist():
                if item.filename.lower().endswith(".xml") and item.file_size > 0:
                    with archive.open(item) as member:
                        if member.read(1):
                            return
    except (BadZipFile, RuntimeError, EOFError, ZlibError) as error:
        raise ValueError(
            "Could not read the Form 990 ZIP or its XML member."
        ) from error
    raise ValueError("Form 990 ZIP has no nonempty XML members.")


def _write_manifest(path: Path, manifest: dict) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, suffix=".part", delete=False
        ) as file:
            temporary = Path(file.name)
            json.dump(manifest, file, indent=2)
            file.write("\n")
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _download_990_batch(
    plan: list[tuple[str, Path]],
    output_dir: Path,
    validate: Callable[[Path], None],
) -> list[DownloadResult]:
    if not plan:
        return []
    root = output_dir.resolve()
    resolved = [path.resolve() for _, path in plan]
    manifest_dir = output_dir / "manifests"
    if any(
        not path.is_relative_to(root) for path in [*resolved, manifest_dir.resolve()]
    ):
        raise ValueError(
            "Form 990 destinations must stay inside the snapshot directory."
        )
    destinations = {str(path).casefold() for path in resolved}
    if len(destinations) != len(plan):
        raise ValueError("Form 990 batch contains colliding destinations.")

    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"form990-{uuid4().hex}.json"
    files = [
        {
            "source_url": url,
            "path": destination.relative_to(output_dir).as_posix(),
            "status": "pending",
        }
        for url, destination in plan
    ]
    manifest = {
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "files": files,
    }
    _write_manifest(manifest_path, manifest)

    results = []
    for (url, destination), entry in zip(plan, files, strict=True):
        try:
            result = download_file(url, destination, validate=validate)
        except (requests.RequestException, OSError, ValueError) as error:
            entry.update(status="failed", error_type=type(error).__name__)
            if isinstance(error, requests.HTTPError) and error.response is not None:
                entry["http_status"] = error.response.status_code
            manifest.update(
                status="failed", finished_at=datetime.now(timezone.utc).isoformat()
            )
            error.add_note(f"Batch stopped after {len(results)} completed file(s).")
            try:
                _write_manifest(manifest_path, manifest)
            except OSError:
                error.add_note(f"Could not record failure in {manifest_path}")
            else:
                error.add_note(f"See run manifest at {manifest_path}")
            raise
        results.append(result)
        entry.update(
            status="complete",
            downloaded_at=result.downloaded_at.isoformat(),
            byte_count=result.byte_count,
            sha256=result.sha256,
        )
        if len(results) == len(plan):
            manifest.update(
                status="complete", finished_at=datetime.now(timezone.utc).isoformat()
            )
        try:
            _write_manifest(manifest_path, manifest)
        except OSError as error:
            error.add_note(
                f"Published {destination}, but could not update {manifest_path}. "
                "Batch stopped. Reconcile the file with the manifest."
            )
            raise
    return results


def download_series_990_index(
    years: list[int], output_dir: Path
) -> list[DownloadResult]:
    """Download distinct yearly indexes into a caller-selected snapshot."""
    output_dir = Path(output_dir)
    plan = [
        (build_series_990_index_url(year), output_dir / str(year) / f"index_{year}.csv")
        for year in years
    ]
    return _download_990_batch(list(dict.fromkeys(plan)), output_dir, _validate_index)


def download_series_990_xml(
    batches: list[tuple[int, str]], output_dir: Path
) -> list[DownloadResult]:
    """Download distinct (year, archive basename) pairs into a snapshot."""
    output_dir = Path(output_dir)
    plan = [
        (
            build_series_990_xml_url(year, batch_id),
            output_dir / str(year) / f"{batch_id}.zip",
        )
        for year, batch_id in batches
    ]
    return _download_990_batch(
        list(dict.fromkeys(plan)), output_dir, _validate_xml_archive
    )


def _validate_eo(path: Path) -> None:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        header = next(csv.reader(stream, strict=True), [])
    if not EO_REQUIRED_COLUMNS.issubset(header) or len(set(header)) != len(header):
        raise ValueError("EO CSV has missing or duplicate header columns.")


def summarize_source_sample(snapshot: Path) -> dict:
    """Stream the approved CSVs; return aggregate quality counts, never raw rows."""
    candidates = set()
    report = {
        "states": {},
        "index_rows": 0,
        "matching_full_990_rows": 0,
        "matching_eins": 0,
        "invalid_rows": 0,
        "tax_year_coverage_verified": False,
    }
    for state in ("oh", "ky", "in"):
        count = invalid = duplicate = 0
        seen = set()
        path = Path(snapshot) / f"eo_{state}.csv"
        _validate_eo(path)
        with path.open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream, strict=True):
                count += 1
                ein = row.get("EIN", "")
                if (
                    None in row
                    or not isinstance(ein, str)
                    or not re.fullmatch(r"[0-9]{9}", ein)
                    or row.get("STATE") != state.upper()
                ):
                    invalid += 1
                    continue
                if ein in seen:
                    duplicate += 1
                seen.add(ein)
                candidates.add(ein)
        if count == 0:
            raise ValueError("EO source has no data rows.")
        report["states"][state.upper()] = {
            "rows": count,
            "invalid_rows": invalid,
            "duplicate_eins": duplicate,
        }
        report["invalid_rows"] += invalid
    index = Path(snapshot) / "index_2026.csv"
    _validate_index(index)
    matched = set()
    with index.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        if "RETURN_TYPE" not in reader.fieldnames:
            raise ValueError("Index is missing RETURN_TYPE for full-990 selection.")
        for row in reader:
            report["index_rows"] += 1
            ein = row.get("EIN", "")
            if (
                None in row
                or not isinstance(ein, str)
                or not re.fullmatch(r"[0-9]{9}", ein)
                or not re.fullmatch(r"[0-9]{6}", row.get("TAX_PERIOD") or "")
                or not row.get("OBJECT_ID")
                or not row.get("RETURN_TYPE")
            ):
                report["invalid_rows"] += 1
                continue
            if ein in candidates and row["RETURN_TYPE"] == "990":
                report["matching_full_990_rows"] += 1
                matched.add(ein)
    if report["index_rows"] == 0:
        raise ValueError("Index has no data rows.")
    report.update(candidate_eins=len(candidates), matching_eins=len(matched))
    return report


def download_source_sample(snapshot: Path) -> dict:
    """Execute the fixed, owner-approved four-CSV plan once into a NEW snapshot.

    Caps count identity response payload, including failed/partial files. Network
    headers and transport overhead are excluded. Existing files are never replaced.
    """
    snapshot = Path(snapshot)
    snapshot.mkdir(parents=True, exist_ok=False)
    budget = DownloadBudget(175_000_000)
    plan = [
        (build_eo_url(state), f"eo_{state}.csv", 25_000_000, _validate_eo)
        for state in ("oh", "ky", "in")
    ]
    plan.append(
        (
            build_series_990_index_url(2026),
            "index_2026.csv",
            100_000_000,
            _validate_index,
        )
    )
    manifest = {
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "payload_budget": budget.limit,
        "files": [
            {
                "source_url": url,
                "path": filename,
                "max_bytes": limit,
                "status": "pending",
            }
            for url, filename, limit, _ in plan
        ],
    }
    manifest_path = snapshot / "source-sample.json"
    _write_manifest(manifest_path, manifest)
    try:
        for (url, filename, limit, validator), entry in zip(
            plan, manifest["files"], strict=True
        ):
            entry["status"] = "downloading"
            _write_manifest(manifest_path, manifest)
            result = download_file(
                url,
                snapshot / filename,
                validate=validator,
                max_bytes=limit,
                max_attempts=1,
                budget=budget,
            )
            entry.update(
                status="complete",
                byte_count=result.byte_count,
                sha256=result.sha256,
                downloaded_at=result.downloaded_at.isoformat(),
                response_headers=result.response_headers,
            )
            manifest["payload_bytes_consumed"] = budget.consumed
            _write_manifest(manifest_path, manifest)
        manifest["summary"] = summarize_source_sample(snapshot)
        manifest["status"] = (
            "needs_review" if manifest["summary"]["invalid_rows"] else "complete"
        )
    except Exception as error:
        manifest.update(status="failed", error_type=type(error).__name__)
        for entry in manifest["files"]:
            if entry["status"] == "downloading":
                entry["status"] = "failed"
        raise
    finally:
        manifest.update(
            payload_bytes_consumed=budget.consumed,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        _write_manifest(manifest_path, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the explicitly approved four-CSV local source sample."
    )
    parser.add_argument(
        "--source-sample",
        type=Path,
        required=True,
        help="NEW ignored local snapshot directory",
    )
    args = parser.parse_args()
    try:
        manifest = download_source_sample(args.source_sample)
    except Exception as error:
        print(json.dumps({"status": "failed", "error_type": type(error).__name__}))
        return 1
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "payload_bytes_consumed": manifest["payload_bytes_consumed"],
                "summary": manifest["summary"],
            }
        )
    )
    return 2 if manifest["status"] == "needs_review" else 0


if __name__ == "__main__":
    raise SystemExit(main())
