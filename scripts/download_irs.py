"""Explicitly invoked IRS downloads; importing this module performs no I/O."""

from collections.abc import Callable
import csv
from dataclasses import dataclass
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
    url: str, destination: Path, *, validate: Callable[[Path], None] | None = None
) -> DownloadResult:
    """Download one file with at most three attempts and atomic publication.

    Existing destinations are replaced only after a nonempty download succeeds.
    Each request uses 10-second connect and 60-second read inactivity timeouts;
    these are not an overall download deadline. HTTP 429/500/502/503/504 and
    connection/read failures are retried after 0.5 and 1 second. Local I/O errors,
    empty bodies, validation failures, and other HTTP errors fail immediately.
    """
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    retry_statuses = {429, 500, 502, 503, 504}
    for attempt in range(3):
        temporary_path = None
        try:
            digest = hashlib.sha256()
            byte_count = 0
            with requests.get(url, stream=True, timeout=(10, 60)) as response:
                response.raise_for_status()
                with tempfile.NamedTemporaryFile(
                    dir=destination.parent,
                    prefix=f".{destination.name}.",
                    suffix=".part",
                    delete=False,
                ) as temporary:
                    temporary_path = Path(temporary.name)
                    for chunk in response.iter_content(chunk_size=8192):
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
            if not retryable or attempt == 2:
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
