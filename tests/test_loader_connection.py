"""Synthetic read-only probe tests: no real password or external connection."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from scripts.check_loader_connection import (
    HOST,
    PROJECT_REF,
    connection_parameters,
    main,
    probe,
    validate_metadata,
)


def metadata():
    result = {
        "database_name": "postgres",
        "connection_role": "nb_loader_dev",
        "login_enabled": True,
        "password_valid": True,
        "connection_limit": 1,
        "read_only": True,
        "inherits_ingest": True,
        "can_execute": True,
    }
    result.update(
        {
            name: False
            for name in (
                "superuser",
                "bypass_rls",
                "can_create_database",
                "can_create_roles",
                "replication",
                "can_set_ingest",
                "executor_member",
                "owner_member",
                "can_create_schema",
                "can_create_in_ingest",
                "can_create_in_public",
                "direct_table_access",
                "unexpected_membership",
            )
        }
    )
    return result


class LoaderConnectionTests(unittest.TestCase):
    def certificate(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "synthetic.crt"
        path.write_text("SYNTHETIC NOT A TRUST ROOT")
        return path

    def connection(self):
        conn = MagicMock()
        conn.autocommit = False
        conn.pgconn.ssl_in_use = True
        conn.pgconn.used_password = True
        conn.cursor.return_value.__enter__.return_value.fetchone.return_value = (
            metadata(),
        )
        return conn

    def test_connection_is_pinned_and_has_no_insecure_tls_fallback(self):
        params = connection_parameters(self.certificate(), "SYNTHETIC PASSWORD")
        self.assertEqual(HOST, params["host"])
        self.assertEqual(f"nb_loader_dev.{PROJECT_REF}", params["user"])
        self.assertEqual("verify-full", params["sslmode"])
        self.assertEqual(5432, params["port"])
        self.assertIsNone(params["prepare_threshold"])
        self.assertIn("default_transaction_read_only=on", params["options"])

    def test_missing_certificate_prevents_connection(self):
        connector = MagicMock()
        path = self.certificate().parent / "missing.crt"
        with self.assertRaises(FileNotFoundError):
            probe(path, "SYNTHETIC PASSWORD", connector=connector)
        connector.assert_not_called()

    def test_metadata_only_probe_rolls_back_and_closes_without_commit(self):
        conn = self.connection()
        result = probe(
            self.certificate(),
            "SYNTHETIC PASSWORD",
            connector=MagicMock(return_value=conn),
        )
        self.assertEqual(0, result["records_imported"])
        self.assertEqual("restricted_connection_verified", result["status"])
        conn.commit.assert_not_called()
        conn.rollback.assert_called_once()
        conn.close.assert_called_once()
        query = conn.cursor.return_value.__enter__.return_value.execute.call_args.args[
            0
        ]
        self.assertNotIn("load_990(%", query)

    def test_missing_tls_blocks_query_and_closes(self):
        conn = self.connection()
        conn.pgconn.ssl_in_use = False
        with self.assertRaises(ValueError):
            probe(
                self.certificate(),
                "SYNTHETIC PASSWORD",
                connector=MagicMock(return_value=conn),
            )
        conn.cursor.assert_not_called()
        conn.close.assert_called_once()

    def test_unexpected_identity_expired_password_or_extra_privilege_rejected(self):
        for field, value in (
            ("connection_role", "postgres"),
            ("password_valid", False),
            ("direct_table_access", True),
            ("unexpected_membership", True),
            ("read_only", False),
            ("can_execute", False),
        ):
            item = metadata()
            item[field] = value
            with self.assertRaises(ValueError):
                validate_metadata(item)

    def test_noninteractive_mode_never_prompts_or_connects(self):
        with patch("sys.argv", ["probe", "--ca-cert", str(self.certificate())]), patch(
            "sys.stdin.isatty", return_value=False
        ), patch("scripts.check_loader_connection.getpass.getpass") as prompt, patch(
            "scripts.check_loader_connection.probe"
        ) as run, redirect_stdout(
            io.StringIO()
        ):
            self.assertEqual(1, main())
        prompt.assert_not_called()
        run.assert_not_called()

    def test_cli_suppresses_driver_text_and_never_retries(self):
        output = io.StringIO()
        with patch("sys.argv", ["probe", "--ca-cert", str(self.certificate())]), patch(
            "sys.stdin.isatty", return_value=True
        ), patch("sys.stderr.isatty", return_value=True), patch(
            "scripts.check_loader_connection.getpass.getpass",
            return_value="SYNTHETIC PASSWORD",
        ), patch(
            "scripts.check_loader_connection.probe",
            side_effect=RuntimeError("SYNTHETIC sensitive DSN"),
        ) as run, redirect_stdout(
            output
        ):
            self.assertEqual(1, main())
        self.assertNotIn("sensitive", output.getvalue())
        self.assertEqual("RuntimeError", json.loads(output.getvalue())["error_type"])
        run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
