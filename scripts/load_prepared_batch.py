"""User-run, hidden-password CLI to load one reviewed prepared batch via restricted loader role."""

import argparse
import getpass
import json
import os
from pathlib import Path
import sys
import warnings

from scripts.check_loader_connection import HOST, PROJECT_REF, ROLE
from scripts.run_irs_pipeline import execute_prepared


def loader_connection_parameters(ca_cert, password):
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
        passfile=os.devnull,
        sslcert="",
        sslkey="",
        gssencmode="disable",
        connect_timeout=15,
        prepare_threshold=None,
        autocommit=False,
        application_name="nbi-loader-batch-runner",
        options="-c statement_timeout=60000 -c lock_timeout=10000 -c idle_in_transaction_session_timeout=30000",
    )


def load_one_prepared_batch(
    ca_cert, password, package, batch_id, *, expected_plan_sha256, connector=None
):
    parameters = loader_connection_parameters(ca_cert, password)
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
        return execute_prepared(
            connection,
            package,
            batch_id,
            expected_plan_sha256=expected_plan_sha256,
        )
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ca-cert", required=True, type=Path)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--expected-plan-sha256", required=True)
    args = parser.parse_args()
    try:
        if not sys.stdin.isatty() or not sys.stderr.isatty():
            raise ValueError(
                "Run in your own interactive terminal; password echo fallback is forbidden."
            )
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            password = getpass.getpass("Loader password (hidden; not stored): ")
        receipt = load_one_prepared_batch(
            args.ca_cert,
            password,
            args.package,
            args.batch_id,
            expected_plan_sha256=args.expected_plan_sha256,
        )
    except Exception as error:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error_type": type(error).__name__,
                }
            )
        )
        return 1
    print(json.dumps(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
