"""Synthetic tests for load_prepared_batch runner."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from scripts.check_loader_connection import HOST, PROJECT_REF
from scripts.load_prepared_batch import (
    load_one_prepared_batch,
    loader_connection_parameters,
    main,
)


class LoadPreparedBatchTests(unittest.TestCase):
    def certificate(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "synthetic.crt"
        path.write_text("SYNTHETIC CA ROOT")
        return path

    def test_connection_parameters_pins_endpoint_and_tls(self):
        params = loader_connection_parameters(self.certificate(), "SYNTHETIC PASSWORD")
        self.assertEqual(HOST, params["host"])
        self.assertEqual(f"nb_loader_dev.{PROJECT_REF}", params["user"])
        self.assertEqual("verify-full", params["sslmode"])
        self.assertEqual(5432, params["port"])
        self.assertFalse(params["autocommit"])
        self.assertNotIn("service", params)

    def test_load_one_prepared_batch_invokes_execute_prepared_and_closes(self):
        conn = MagicMock()
        conn.autocommit = False
        conn.pgconn.ssl_in_use = True
        conn.pgconn.used_password = True
        connector = MagicMock(return_value=conn)
        with patch("scripts.load_prepared_batch.execute_prepared") as execute:
            execute.return_value = {"status": "complete", "filings": 13}
            result = load_one_prepared_batch(
                self.certificate(),
                "SYNTHETIC PASSWORD",
                Path("data/synthetic"),
                "batch-001",
                expected_plan_sha256="a" * 64,
                connector=connector,
            )
            self.assertEqual("complete", result["status"])
            execute.assert_called_once_with(
                conn,
                Path("data/synthetic"),
                "batch-001",
                expected_plan_sha256="a" * 64,
            )
            conn.close.assert_called_once()

    def test_missing_tls_or_used_password_rejected(self):
        conn = MagicMock()
        conn.autocommit = False
        conn.pgconn.ssl_in_use = False
        conn.pgconn.used_password = True
        connector = MagicMock(return_value=conn)
        with self.assertRaises(ValueError):
            load_one_prepared_batch(
                self.certificate(),
                "SYNTHETIC PASSWORD",
                Path("data/synthetic"),
                "batch-001",
                expected_plan_sha256="a" * 64,
                connector=connector,
            )
        conn.close.assert_called_once()

    def test_noninteractive_mode_refuses_to_prompt(self):
        with patch(
            "sys.argv",
            [
                "load_batch",
                "--ca-cert",
                str(self.certificate()),
                "--package",
                "data/synthetic",
                "--batch-id",
                "batch-001",
                "--expected-plan-sha256",
                "a" * 64,
            ],
        ), patch("sys.stdin.isatty", return_value=False), redirect_stdout(
            io.StringIO()
        ):
            self.assertEqual(1, main())

    def test_failure_is_sanitized_and_never_leaks_dsn(self):
        output = io.StringIO()
        with patch(
            "sys.argv",
            [
                "load_batch",
                "--ca-cert",
                str(self.certificate()),
                "--package",
                "data/synthetic",
                "--batch-id",
                "batch-001",
                "--expected-plan-sha256",
                "a" * 64,
            ],
        ), patch("sys.stdin.isatty", return_value=True), patch(
            "sys.stderr.isatty", return_value=True
        ), patch(
            "scripts.load_prepared_batch.getpass.getpass",
            return_value="SYNTHETIC PASSWORD",
        ), patch(
            "scripts.load_prepared_batch.load_one_prepared_batch",
            side_effect=RuntimeError("SYNTHETIC sensitive connection string"),
        ), redirect_stdout(
            output
        ):
            self.assertEqual(1, main())
        self.assertNotIn("sensitive", output.getvalue())
        self.assertEqual("RuntimeError", json.loads(output.getvalue())["error_type"])


if __name__ == "__main__":
    unittest.main()
