"""Revalidate existing local sources and generate the reviewable next-30 SQL."""

import argparse
import json
from pathlib import Path

from scripts.prepare_cloud_trial import (
    displayed_mb_bound,
    render_trial,
    system_evidence,
    write_new_sql,
)
from scripts.prepare_next_batch import build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("sample", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--system-timestamp-us", type=int)
    parser.add_argument("--system-mb")
    parser.add_argument(
        "--database-mb",
        required=True,
        help="Database category from the SAME Disk panel observation",
    )
    args = parser.parse_args()
    try:
        root = Path(__file__).resolve().parents[1] / "data"
        if not args.output.resolve().is_relative_to(root.resolve()):
            raise ValueError("SQL must remain under ignored data/.")
        selection, batch, payload, report = build(args.source, args.sample)
        if report["status"] != "complete" or payload is None:
            raise ValueError("Local batch requires review.")
        prior_batch = json.loads(
            (args.sample / "staged-filings.json").read_text(encoding="utf-8")
        )
        # Re-extract the original three and compare its prepared payload before it
        # becomes the SQL baseline fingerprint; staging is never trusted alone.
        from scripts.extract_990 import extract_batch
        from scripts.load_supabase import prepare_batch
        from scripts.prepare_cloud_trial import SCOPE_VERSION

        original = json.loads(
            (args.sample / "selection.json").read_text(encoding="utf-8")
        )
        (manifest,) = (args.sample / "manifests").glob("*.json")
        verified = extract_batch(
            manifest,
            selected_filing_ids={
                r["object_id"] for r in original["selection"].values()
            },
        )
        if prepare_batch(prior_batch, SCOPE_VERSION) != prepare_batch(
            verified, SCOPE_VERSION
        ):
            raise ValueError("Original trial staging differs from its archive.")
        observed = bound = None
        if args.system_timestamp_us is not None or args.system_mb is not None:
            if args.system_timestamp_us is None or args.system_mb is None:
                raise ValueError("Both System inputs required.")
            observed, bound = system_evidence(args.system_timestamp_us, args.system_mb)
        sql, summary = render_trial(
            batch,
            selection,
            observed=observed,
            system_bound=bound,
            prior_batch=prior_batch,
            database_category_bound=displayed_mb_bound(args.database_mb),
        )
        write_new_sql(args.output, sql)
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
