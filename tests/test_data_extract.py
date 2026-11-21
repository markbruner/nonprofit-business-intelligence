"""Downloader tests use synthetic bytes and block real HTTP at the call boundary."""

import hashlib
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from zipfile import ZipFile

import requests

from scripts.download_irs import (
    DownloadBudget,
    build_eo_url,
    download_eo_files,
    download_file,
    download_series_990_index,
    download_series_990_xml,
    download_source_sample,
    EO_REQUIRED_COLUMNS,
)

BODY = b"EIN,NAME\n001234567,SYNTHETIC TEST ORGANIZATION\n"


def response(status=200, chunks=None):
    result = MagicMock()
    result.__enter__.return_value = result
    result.status_code = status
    result.headers = {}
    if status >= 400:
        result.raise_for_status.side_effect = requests.HTTPError(response=result)
    result.iter_content.return_value = iter([BODY] if chunks is None else chunks)
    return result


def bounded_response(body, headers=None, status=200):
    result = response(status=status)
    result.headers = headers or {}
    stream = BytesIO(body)
    result.raw.read.side_effect = lambda amount, decode_content=False: stream.read(
        amount
    )
    return result


class BoundedDownloadTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.http = patch("scripts.download_irs.requests.get").start()
        self.addCleanup(patch.stopall)

    def test_exact_declared_limit_and_identity_request(self):
        self.http.return_value = bounded_response(b"12345", {"Content-Length": "5"})
        budget = DownloadBudget(5)
        result = download_file(
            "https://example.invalid/synthetic",
            self.root / "file",
            max_bytes=5,
            max_attempts=1,
            budget=budget,
        )
        self.assertEqual(5, result.byte_count)
        self.assertEqual(5, budget.consumed)
        self.assertFalse(self.http.call_args.kwargs["allow_redirects"])
        self.assertEqual(
            {"Accept-Encoding": "identity"}, self.http.call_args.kwargs["headers"]
        )

    def test_unknown_length_stops_at_cap_without_overread_or_replacement(self):
        path = self.root / "file"
        path.write_bytes(b"previous")
        reply = bounded_response(b"123456789")
        self.http.return_value = reply
        budget = DownloadBudget(5)
        with self.assertRaisesRegex(ValueError, "budget exhausted"):
            download_file(
                "https://example.invalid/synthetic",
                path,
                max_bytes=5,
                max_attempts=1,
                budget=budget,
            )
        self.assertEqual(5, budget.consumed)
        reply.raw.read.assert_called_once_with(5, decode_content=False)
        self.assertEqual(b"previous", path.read_bytes())
        self.assertFalse(list(self.root.glob("*.part")))

    def test_shared_budget_includes_failed_file_bytes(self):
        self.http.side_effect = [
            bounded_response(b"12345", {"Content-Length": "5"}),
            bounded_response(b"123456"),
        ]
        budget = DownloadBudget(8)
        download_file(
            "https://example.invalid/one",
            self.root / "one",
            max_bytes=10,
            max_attempts=1,
            budget=budget,
        )
        with self.assertRaises(ValueError):
            download_file(
                "https://example.invalid/two",
                self.root / "two",
                max_bytes=10,
                max_attempts=1,
                budget=budget,
            )
        self.assertEqual(8, budget.consumed)
        self.assertFalse((self.root / "two").exists())
        self.assertEqual(b"12345", (self.root / "one").read_bytes())

    def test_redirect_compression_and_oversize_headers_rejected_before_read(self):
        for status, headers in (
            (302, {}),
            (200, {"Content-Encoding": "gzip"}),
            (200, {"Content-Length": "50"}),
            (200, {"Content-Length": "invalid"}),
        ):
            with self.subTest(status=status, headers=headers):
                reply = bounded_response(b"123", headers, status)
                self.http.return_value = reply
                with self.assertRaises(ValueError):
                    download_file(
                        "https://example.invalid/synthetic",
                        self.root / "file",
                        max_bytes=10,
                        max_attempts=1,
                    )
                reply.raw.read.assert_not_called()
        self.assertFalse((self.root / "file").exists())

    def test_one_attempt_and_invalid_options_never_retry(self):
        self.http.return_value = bounded_response(b"", status=503)
        with self.assertRaises(requests.HTTPError):
            download_file(
                "https://example.invalid/synthetic",
                self.root / "file",
                max_bytes=10,
                max_attempts=1,
            )
        self.http.assert_called_once()
        self.http.reset_mock()
        for kwargs in (
            {"max_bytes": 0},
            {"max_attempts": 0},
            {"budget": DownloadBudget(10)},
        ):
            with self.assertRaises(ValueError):
                download_file(
                    "https://example.invalid/synthetic", self.root / "file", **kwargs
                )
        self.http.assert_not_called()

    def test_short_body_and_validation_failure_preserve_prior_file(self):
        path = self.root / "file"
        path.write_bytes(b"previous")
        self.http.return_value = bounded_response(b"12", {"Content-Length": "5"})
        with self.assertRaisesRegex(ValueError, "declared length"):
            download_file(
                "https://example.invalid/synthetic", path, max_bytes=10, max_attempts=1
            )
        self.http.return_value = bounded_response(b"12")
        with self.assertRaises(ValueError):
            download_file(
                "https://example.invalid/synthetic",
                path,
                max_bytes=10,
                max_attempts=1,
                validate=MagicMock(side_effect=ValueError("synthetic header")),
            )
        self.assertEqual(b"previous", path.read_bytes())

    def test_fixed_source_sample_aggregate_report_and_no_overwrite(self):
        headers = sorted(EO_REQUIRED_COLUMNS)
        bodies = []
        for state in ("OH", "KY", "IN"):
            row = dict.fromkeys(headers, "")
            row.update(EIN="001234567", STATE=state, NAME="SYNTHETIC TEST ONLY")
            bodies.append(
                (
                    ",".join(headers) + "\n" + ",".join(row[h] for h in headers) + "\n"
                ).encode()
            )
        bodies.append(
            b"EIN,TAX_PERIOD,OBJECT_ID,RETURN_TYPE\n001234567,202512,synthetic,990\n"
        )
        self.http.side_effect = [bounded_response(body) for body in bodies]
        snapshot = self.root / "new"
        report = download_source_sample(snapshot)
        self.assertEqual("complete", report["status"])
        self.assertEqual(sum(map(len, bodies)), report["payload_bytes_consumed"])
        self.assertEqual(1, report["summary"]["candidate_eins"])
        self.assertEqual(1, report["summary"]["matching_full_990_rows"])
        self.assertFalse(report["summary"]["tax_year_coverage_verified"])
        self.assertNotIn("SYNTHETIC TEST ONLY", json.dumps(report))
        self.assertEqual(4, self.http.call_count)
        with self.assertRaises(FileExistsError):
            download_source_sample(snapshot)
        self.assertEqual(4, self.http.call_count)

    def test_invalid_header_stops_plan_and_records_partial_budget(self):
        self.http.return_value = bounded_response(b"invalid header\n")
        snapshot = self.root / "bad"
        with self.assertRaisesRegex(ValueError, "EO CSV"):
            download_source_sample(snapshot)
        manifest = json.loads((snapshot / "source-sample.json").read_text())
        self.assertEqual("failed", manifest["status"])
        self.assertEqual(len(b"invalid header\n"), manifest["payload_bytes_consumed"])
        self.assertEqual(
            ["failed", "pending", "pending", "pending"],
            [entry["status"] for entry in manifest["files"]],
        )
        self.assertFalse((snapshot / "eo_oh.csv").exists())
        self.http.assert_called_once()

    def test_xml_wrapper_forwards_bounds_and_records_consumed_budget(self):
        memory = BytesIO()
        with ZipFile(memory, "w") as archive:
            archive.writestr("synthetic.xml", "<Return />")
        body = memory.getvalue()
        self.http.return_value = bounded_response(
            body, {"Content-Length": str(len(body))}
        )
        budget = DownloadBudget(len(body))
        output = self.root / "xml"
        download_series_990_xml(
            [(2026, "synthetic")],
            output,
            max_bytes_per_file=len(body),
            max_attempts=1,
            budget=budget,
        )
        (manifest_path,) = (output / "manifests").glob("*.json")
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual("complete", manifest["status"])
        self.assertEqual(len(body), manifest["payload_bytes_consumed"])
        self.assertEqual(1, manifest["max_attempts"])
        self.assertEqual(len(body), manifest["max_bytes_per_file"])


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.destination = self.directory / "eo_oh.csv"
        self.url = build_eo_url("ohio")
        self.get = patch("scripts.download_irs.requests.get").start()
        self.addCleanup(patch.stopall)
        self.sleep = patch("scripts.download_irs.time.sleep").start()

    def assert_no_partial_files(self):
        self.assertEqual([], list(self.directory.glob(".*.part")))

    def test_state_names_codes_and_whitespace(self):
        for state in ("ohio", " OH ", "Ohio"):
            self.assertEqual(self.url, build_eo_url(state))
        for state in ("New York", "new-york", " NY "):
            self.assertTrue(build_eo_url(state).endswith("eo_ny.csv"))
        self.assertTrue(build_eo_url("District of Columbia").endswith("eo_dc.csv"))

    def test_all_states_validated_before_network_or_directory_creation(self):
        output_dir = self.directory / "not-created"
        with self.assertRaises(ValueError):
            download_eo_files(["ohio", "invalid"], output_dir)
        self.get.assert_not_called()
        self.assertFalse(output_dir.exists())

    def test_empty_batch_does_no_io(self):
        self.assertEqual([], download_eo_files([], self.directory / "absent"))
        self.get.assert_not_called()
        self.assertFalse((self.directory / "absent").exists())

    def test_distinct_states_urls_and_filenames_and_duplicate_aliases(self):
        self.get.side_effect = [response(), response()]
        results = download_eo_files(["ohio", "kentucky", "OH"], self.directory)
        self.assertEqual(
            ["eo_oh.csv", "eo_ky.csv"], [r.local_path.name for r in results]
        )
        self.assertEqual(
            [build_eo_url("ohio"), build_eo_url("kentucky")],
            [call.args[0] for call in self.get.call_args_list],
        )
        for result in results:
            self.assertEqual(BODY, result.local_path.read_bytes())

    def test_success_returns_bytes_checksum_and_utc_timestamp(self):
        self.get.return_value = response(chunks=[b"", BODY[:5], BODY[5:]])
        result = download_file(self.url, self.destination)
        self.assertEqual(BODY, self.destination.read_bytes())
        self.assertEqual(self.url, result.source_url)
        self.assertEqual(self.destination, result.local_path)
        self.assertEqual(len(BODY), result.byte_count)
        self.assertEqual(hashlib.sha256(BODY).hexdigest(), result.sha256)
        self.assertEqual(0, result.downloaded_at.utcoffset().total_seconds())
        self.get.assert_called_once_with(self.url, stream=True, timeout=(10, 60))
        self.assert_no_partial_files()

    def test_missing_parent_directory_is_created(self):
        self.get.return_value = response()
        result = download_file(self.url, self.directory / "raw" / "eo_oh.csv")
        self.assertEqual(BODY, result.local_path.read_bytes())

    def test_404_fails_without_retry_or_replacing_destination(self):
        self.destination.write_bytes(b"previous")
        self.get.return_value = response(status=404)
        with self.assertRaises(requests.HTTPError):
            download_file(self.url, self.destination)
        self.get.assert_called_once()
        self.sleep.assert_not_called()
        self.assertEqual(b"previous", self.destination.read_bytes())
        self.assert_no_partial_files()

    def test_transient_http_statuses_are_retried(self):
        for status in (429, 500, 502, 503, 504):
            with self.subTest(status=status):
                self.get.reset_mock()
                self.get.side_effect = [response(status=status), response()]
                download_file(self.url, self.destination)
                self.assertEqual(2, self.get.call_count)

    def test_timeout_and_connection_failure_retry_then_succeed(self):
        self.get.side_effect = [
            requests.Timeout(),
            requests.ConnectionError(),
            response(),
        ]
        download_file(self.url, self.destination)
        self.assertEqual(3, self.get.call_count)
        self.assertEqual([0.5, 1.0], [c.args[0] for c in self.sleep.call_args_list])
        self.assertEqual(BODY, self.destination.read_bytes())

    def test_retry_limit_preserves_existing_file(self):
        self.destination.write_bytes(b"previous")
        self.get.side_effect = requests.Timeout("synthetic timeout")
        with self.assertRaises(requests.Timeout):
            download_file(self.url, self.destination)
        self.assertEqual(3, self.get.call_count)
        self.assertEqual(2, self.sleep.call_count)
        self.assertEqual(b"previous", self.destination.read_bytes())
        self.assert_no_partial_files()

    def test_interrupted_stream_preserves_previous_bytes_during_retry(self):
        self.destination.write_bytes(b"previous")

        def interrupted():
            yield b"partial"
            self.assertEqual(b"previous", self.destination.read_bytes())
            raise requests.exceptions.ChunkedEncodingError("synthetic interruption")

        self.get.side_effect = [response(chunks=interrupted()) for _ in range(3)]
        with self.assertRaises(requests.exceptions.ChunkedEncodingError):
            download_file(self.url, self.destination)
        self.assertEqual(3, self.get.call_count)
        self.assertEqual(b"previous", self.destination.read_bytes())
        self.assert_no_partial_files()

    def test_empty_body_is_rejected_without_retry_or_publication(self):
        self.get.return_value = response(chunks=[])
        with self.assertRaisesRegex(ValueError, "Empty download"):
            download_file(self.url, self.destination)
        self.assertFalse(self.destination.exists())
        self.get.assert_called_once()
        self.assert_no_partial_files()

    def test_successful_rerun_replaces_destination(self):
        self.destination.write_bytes(b"previous")
        self.get.return_value = response()
        download_file(self.url, self.destination)
        self.assertEqual(BODY, self.destination.read_bytes())
        self.assert_no_partial_files()

    def test_publication_failure_preserves_existing_file_and_cleans_up(self):
        self.destination.write_bytes(b"previous")
        self.get.return_value = response()
        with patch("scripts.download_irs.Path.replace", side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                download_file(self.url, self.destination)
        self.get.assert_called_once()
        self.assertEqual(b"previous", self.destination.read_bytes())
        self.assert_no_partial_files()

    def test_batch_stops_on_failure_and_retains_completed_files(self):
        self.get.side_effect = [response(), response(status=404)]
        with self.assertRaises(requests.HTTPError) as caught:
            download_eo_files(["ohio", "kentucky", "indiana"], self.directory)
        self.assertEqual(2, self.get.call_count)
        self.assertEqual(BODY, self.destination.read_bytes())
        self.assertFalse((self.directory / "eo_ky.csv").exists())
        self.assertFalse((self.directory / "eo_in.csv").exists())
        self.assertIn("1 earlier file(s) completed", caught.exception.__notes__[0])


class Form990Tests(unittest.TestCase):
    INDEX = b"EIN,TAX_PERIOD,OBJECT_ID\n001234567,202412,fake\n"

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.snapshot = Path(temporary.name) / "snapshot"
        http = patch("scripts.download_irs.requests.get")
        self.get = http.start()
        self.addCleanup(http.stop)

    def manifest(self):
        (path,) = (self.snapshot / "manifests").glob("*.json")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_invalid_batch_or_collision_never_starts_a_run(self):
        for batches in [
            [(2025, "archive"), (2026,)],
            [(2025, "archive"), (2026, "../archive")],
            [(2025, "archive"), (2026, "NUL")],
            [(2025, "archive"), (2025, "Archive")],
        ]:
            with self.subTest(batches=batches), self.assertRaises(ValueError):
                download_series_990_xml(batches, self.snapshot)
        with self.assertRaises(ValueError):
            download_series_990_index([2025, "2026"], self.snapshot)
        self.assertEqual([], download_series_990_index([], self.snapshot))
        self.get.assert_not_called()
        self.assertFalse(self.snapshot.exists())

    def test_duplicate_index_year_downloaded_once(self):
        self.get.return_value = response(chunks=[self.INDEX])
        (result,) = download_series_990_index([2026, 2026], self.snapshot)
        self.get.assert_called_once()
        self.assertTrue(self.get.call_args.args[0].endswith("/2026/index_2026.csv"))
        self.assertEqual(self.snapshot / "2026" / "index_2026.csv", result.local_path)
        self.assertEqual(self.INDEX, result.local_path.read_bytes())
        manifest = self.manifest()
        self.assertEqual("complete", manifest["status"])
        self.assertIn("finished_at", manifest)
        (file,) = manifest["files"]
        self.assertEqual("complete", file["status"])
        self.assertEqual(result.source_url, file["source_url"])
        self.assertEqual(result.downloaded_at.isoformat(), file["downloaded_at"])
        self.assertEqual(len(self.INDEX), file["byte_count"])
        self.assertEqual(hashlib.sha256(self.INDEX).hexdigest(), file["sha256"])

    def test_archive_names_are_scoped_by_year_and_pairs_deduplicated(self):
        archive_bytes = BytesIO()
        with ZipFile(archive_bytes, "w") as archive:
            archive.writestr("synthetic.xml", "<Return />")
        payload = archive_bytes.getvalue()
        self.get.side_effect = [response(chunks=[payload]) for _ in range(2)]
        results = download_series_990_xml(
            [(2025, "archive"), (2026, "archive"), (2025, "archive")], self.snapshot
        )
        self.assertEqual(
            [self.snapshot / str(year) / "archive.zip" for year in (2025, 2026)],
            [result.local_path for result in results],
        )
        self.assertEqual(2, self.get.call_count)
        self.assertTrue(
            all(result.local_path.read_bytes() == payload for result in results)
        )

    def test_invalid_index_preserves_prior_file_and_records_partial_batch(self):
        prior = self.snapshot / "2026" / "index_2026.csv"
        prior.parent.mkdir(parents=True)
        prior.write_bytes(self.INDEX)
        self.get.side_effect = [
            response(chunks=[self.INDEX]),
            response(chunks=[b"<html>error</html>"]),
        ]
        with self.assertRaisesRegex(ValueError, "header"):
            download_series_990_index([2025, 2026, 2027], self.snapshot)
        self.assertEqual(2, self.get.call_count)
        self.assertEqual(self.INDEX, prior.read_bytes())
        self.assertFalse(list(self.snapshot.rglob("*.part")))
        manifest = self.manifest()
        self.assertEqual("failed", manifest["status"])
        self.assertEqual(
            ["complete", "failed", "pending"],
            [file["status"] for file in manifest["files"]],
        )
        self.assertEqual("ValueError", manifest["files"][1]["error_type"])
        self.assertEqual(
            self.INDEX, (self.snapshot / manifest["files"][0]["path"]).read_bytes()
        )

    def test_invalid_zip_preserves_prior_file(self):
        prior = self.snapshot / "2026" / "archive.zip"
        prior.parent.mkdir(parents=True)
        prior.write_bytes(b"previous")
        self.get.return_value = response(chunks=[b"not a ZIP"])
        with self.assertRaisesRegex(ValueError, "ZIP"):
            download_series_990_xml([(2026, "archive")], self.snapshot)
        self.assertEqual(b"previous", prior.read_bytes())
        self.assertEqual("failed", self.manifest()["status"])


if __name__ == "__main__":
    unittest.main()
