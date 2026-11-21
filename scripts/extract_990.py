"""Stage Form 990 filings from a completed local XML download manifest."""

import argparse
from collections import defaultdict
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile
from zlib import error as ZlibError

PARSER_VERSION = "form990-xml-provisional-v1"
XML_NAMESPACE = "http://www.irs.gov/efile"
MAX_MEMBER_BYTES = 8 * 1024 * 1024
MAX_BATCH_XML_BYTES = 512 * 1024 * 1024


class FilingError(ValueError):
    """A stable reason code for a rejected filing."""


class FilingTreeBuilder(ET.TreeBuilder):
    def doctype(self, name, pubid, system):
        raise FilingError("xml_doctype")


def _parse_filing(payload: bytes) -> dict:
    root = ET.fromstring(payload, parser=ET.XMLParser(target=FilingTreeBuilder()))
    namespace = (
        f"{{{XML_NAMESPACE}}}" if root.tag == f"{{{XML_NAMESPACE}}}Return" else ""
    )
    if root.tag != f"{namespace}Return":
        raise FilingError("unexpected_xml_root")
    namespaces = {"": XML_NAMESPACE} if namespace else {}

    def value(path: str) -> str:
        return (root.findtext(path, namespaces=namespaces) or "").strip()

    def amount(name: str) -> int | None:
        raw = value(f"ReturnData/IRS990/{name}")
        if not raw:
            return None
        if not re.fullmatch(r"-?[0-9]{1,18}", raw):
            raise FilingError("invalid_amount")
        return int(raw)

    form = value("ReturnHeader/ReturnTypeCd")
    if not form:
        raise FilingError("missing_form_type")
    if form != "990":
        raise FilingError("unsupported_form")
    if root.find("ReturnData/IRS990", namespaces) is None:
        raise FilingError("missing_form_body")
    ein = value("ReturnHeader/Filer/EIN")
    if not re.fullmatch(r"[0-9]{9}", ein):
        raise FilingError("invalid_ein")
    period = value("ReturnHeader/TaxPeriodEndDt")
    try:
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", period):
            raise ValueError
        period = date.fromisoformat(period).isoformat()
    except ValueError as error:
        raise FilingError("invalid_tax_period_end") from error
    amended = value("ReturnHeader/AmendedReturnInd")
    tax_year = value("ReturnHeader/TaxYr")
    if tax_year and not re.fullmatch(r"[0-9]{4}", tax_year):
        raise FilingError("invalid_tax_year")
    amendment_values = {"": None, "0": False, "1": True, "false": False, "true": True}
    if amended not in amendment_values:
        raise FilingError("invalid_amendment_indicator")
    return {
        "ein": ein,
        "tax_period_end": period,
        "tax_year": int(tax_year) if tax_year else None,
        "form_type": form,
        "amended": amendment_values[amended],
        "total_revenue": amount("CYTotalRevenueAmt"),
        "total_expenses": amount("CYTotalExpensesAmt"),
    }


def _read_manifest(manifest_path: Path) -> tuple[str, list[dict]]:
    payload = manifest_path.read_bytes()
    manifest = json.loads(payload)
    if not isinstance(manifest, dict) or manifest.get("status") != "complete":
        raise ValueError("Expected a completed downloader manifest.")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("Expected a nonempty XML archive manifest.")
    for entry in files:
        if (
            not isinstance(entry, dict)
            or entry.get("status") != "complete"
            or not isinstance(entry.get("path"), str)
            or not entry["path"].lower().endswith(".zip")
            or not isinstance(entry.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])
            or not isinstance(entry.get("source_url"), str)
            or not entry["source_url"]
            or not isinstance(entry.get("downloaded_at"), str)
            or not entry["downloaded_at"]
        ):
            raise ValueError(
                "Manifest contains an invalid or incomplete archive entry."
            )
    return hashlib.sha256(payload).hexdigest(), files


def extract_batch(manifest_path: Path) -> dict:
    """Return staged filings and quality findings for one completed snapshot."""
    started_at = datetime.now(timezone.utc)
    manifest_path = Path(manifest_path)
    snapshot = manifest_path.parent.parent.resolve()
    manifest_sha256, archives = _read_manifest(manifest_path)
    filings = {}
    issues = []
    source_ids = defaultdict(list)
    periods = defaultdict(list)
    xml_seen = duplicates = rejected = unsupported = xml_bytes = 0

    for entry in archives:
        relative = Path(entry["path"])
        path = (snapshot / relative).resolve()
        if (
            relative.anchor
            or ".." in relative.parts
            or not path.is_relative_to(snapshot)
        ):
            raise ValueError("Archive path must stay inside the snapshot.")
        with path.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != entry["sha256"]:
                raise ValueError(
                    "Archive SHA-256 does not match the download manifest."
                )
            stream.seek(0)
            with ZipFile(stream) as archive:
                for member in archive.infolist():
                    if member.is_dir() or not member.filename.lower().endswith(".xml"):
                        continue
                    xml_seen += 1
                    source = {
                        "archive_path": entry["path"],
                        "archive_sha256": entry["sha256"],
                        "source_url": entry["source_url"],
                        "downloaded_at": entry["downloaded_at"],
                        "member": member.filename,
                    }
                    try:
                        if member.file_size > MAX_MEMBER_BYTES:
                            raise FilingError("member_too_large")
                        xml_bytes += member.file_size
                        if xml_bytes > MAX_BATCH_XML_BYTES:
                            raise ValueError("Batch exceeds the XML byte limit.")
                        payload = archive.read(member)
                        filing = _parse_filing(payload)
                    except (
                        FilingError,
                        ET.ParseError,
                        LookupError,
                        BadZipFile,
                        RuntimeError,
                        EOFError,
                        ZlibError,
                    ) as error:
                        if isinstance(error, FilingError):
                            reason = str(error)
                        elif isinstance(error, (ET.ParseError, LookupError)):
                            reason = "malformed_xml"
                        else:
                            reason = "unreadable_member"
                        issues.append({"reason": reason, "source": source})
                        if reason == "unsupported_form":
                            unsupported += 1
                        else:
                            rejected += 1
                        continue
                    filing_id = PurePosixPath(member.filename).stem.removesuffix(
                        "_public"
                    )
                    xml_sha256 = hashlib.sha256(payload).hexdigest()
                    key = hashlib.sha256(
                        f"{filing_id}\0{xml_sha256}".encode()
                    ).hexdigest()
                    if key in filings:
                        duplicates += 1
                        if source not in filings[key]["sources"]:
                            filings[key]["sources"].append(source)
                        continue
                    filings[key] = dict(
                        filing,
                        filing_key=key,
                        source_filing_id=filing_id,
                        xml_sha256=xml_sha256,
                        sources=[source],
                    )
                    source_ids[filing_id].append(key)
                    periods[(filing["ein"], filing["tax_period_end"])].append(key)

    for reason, groups in (
        ("conflicting_source_id", source_ids),
        ("multiple_returns_for_period", periods),
    ):
        issues.extend(
            {"reason": reason, "filing_keys": keys}
            for keys in groups.values()
            if len(keys) > 1
        )
    if not filings:
        issues.append({"reason": "no_supported_filings"})
    return {
        "parser_version": PARSER_VERSION,
        "manifest_sha256": manifest_sha256,
        "filings": list(filings.values()),
        "report": {
            "status": "needs_review" if issues else "complete",
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "archive_count": len(archives),
            "xml_seen": xml_seen,
            "staged": len(filings),
            "duplicates": duplicates,
            "rejected": rejected,
            "unsupported": unsupported,
            "issues": issues,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path, help="New JSON staging file")
    args = parser.parse_args()
    temporary = None
    try:
        if args.output.exists():
            raise ValueError("Choose a new staging output path.")
        batch = extract_batch(args.manifest)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=args.output.parent,
            suffix=".part",
            delete=False,
        ) as file:
            temporary = Path(file.name)
            json.dump(batch, file, indent=2)
            file.write("\n")
        # Windows rename refuses to replace an existing destination.
        if os.name == "nt":
            temporary.rename(args.output)
        else:
            args.output.hardlink_to(temporary)
    except (OSError, ValueError, BadZipFile) as error:
        parser.exit(1, f"Extraction failed: {error}\n")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return 2 if batch["report"]["status"] == "needs_review" else 0


if __name__ == "__main__":
    raise SystemExit(main())
