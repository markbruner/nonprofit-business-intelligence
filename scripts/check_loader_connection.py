"""User-run, hidden-password, read-only dev loader probe; never import records."""

import argparse
import getpass
import json
import os
from pathlib import Path
import sys
import warnings

PROJECT_REF = "yxtslaaboriakfvpeedi"
HOST = "aws-1-us-east-2.pooler.supabase.com"
ROLE = "nb_loader_dev"
QUERY = (
    Path(__file__).resolve().parents[1]
    / "supabase/diagnostics/loader_connection_probe.sql"
)


def connection_parameters(ca_cert, password):
    certificate = Path(ca_cert).resolve(strict=True)
    if not certificate.is_file() or not isinstance(password, str) or not password:
        raise ValueError(
            "A certificate file and nonempty prompted password are required."
        )
    return dict(
        host=HOST,
        hostaddr="",
        port=5432,
        dbname="postgres",
        user=f"{ROLE}.{PROJECT_REF}",
        password=password,
        sslmode="verify-full",
        sslrootcert=str(certificate),
        service="",
        passfile=os.devnull,
        sslcert="",
        sslkey="",
        gssencmode="disable",
        connect_timeout=10,
        prepare_threshold=None,
        autocommit=False,
        application_name="nbi-loader-connection-check",
        options="-c default_transaction_read_only=on -c statement_timeout=10000 -c lock_timeout=5000 -c idle_in_transaction_session_timeout=15000",
    )


def validate_metadata(result):
    expected = {
        "database_name": "postgres",
        "connection_role": ROLE,
        "login_enabled": True,
        "password_valid": True,
        "connection_limit": 1,
        "read_only": True,
        "inherits_ingest": True,
        "can_execute": True,
        **{
            field: False
            for field in (
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
        },
    }
    if not isinstance(result, dict) or any(
        result.get(key) != value for key, value in expected.items()
    ):
        raise ValueError(
            "Restricted connection metadata did not match reviewed expectations."
        )
    return expected  # Never echo unexpected server-supplied strings.


def probe(ca_cert, password, *, connector=None):
    parameters = connection_parameters(ca_cert, password)
    if connector is None:
        from psycopg import connect

        connector = connect
    connection = connector(**parameters)
    try:
        if (
            connection.pgconn.ssl_in_use is not True
            or connection.pgconn.used_password is not True
            or connection.autocommit is not False
        ):
            raise ValueError("Verified TLS and transaction ownership are required.")
        with connection.cursor() as cursor:
            cursor.execute(QUERY.read_text(encoding="utf-8"))
            row = cursor.fetchone()
            result = validate_metadata(row[0] if row else None)
        return {
            "status": "restricted_connection_verified",
            "tls_in_use": True,
            "sslmode": "verify-full",
            "password_auth_used": True,
            "metadata": result,
            "records_imported": 0,
        }
    finally:
        try:
            connection.rollback()
        finally:
            connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ca-cert", required=True, type=Path)
    args = parser.parse_args()
    try:
        if not sys.stdin.isatty() or not sys.stderr.isatty():
            raise ValueError(
                "Run in your own interactive terminal; password echo fallback is forbidden."
            )
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            password = getpass.getpass("Loader password (hidden; not stored): ")
        result = probe(args.ca_cert, password)
    except Exception as error:
        # Driver exceptions can contain connection/credential details. Never print them.
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error_type": type(error).__name__,
                    "records_imported": 0,
                }
            )
        )
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
