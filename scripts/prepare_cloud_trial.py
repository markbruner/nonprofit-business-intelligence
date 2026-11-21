"""Prepare a local SQL review artifact; never connect to a database or read secrets."""

import argparse
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
import hashlib
import json
from pathlib import Path
import re

from scripts.extract_990 import extract_batch
from scripts.load_supabase import prepare_batch

PROJECT_REF = "yxtslaaboriakfvpeedi"
SCOPE_VERSION = "oh-ky-in-first-three-v1"


def dollar_quote(text: str, label: str) -> str:
    """Choose a delimiter absent from untrusted content, including outer DO bodies."""
    delimiter = f"$nbi_{label}$"
    while delimiter in text:
        delimiter = delimiter[:-1] + "_$"
    return delimiter + text + delimiter


def system_evidence(timestamp_us: int, displayed_mb: str) -> tuple[datetime, int]:
    amount = Decimal(displayed_mb)
    if not amount.is_finite() or amount <= 0 or amount >= 1900:
        raise ValueError("System usage must be a positive bounded MB reading.")
    observed = datetime.fromtimestamp(timestamp_us // 1_000_000, timezone.utc).replace(
        microsecond=timestamp_us % 1_000_000
    )
    # Conservative upper bound for either decimal MB or binary MiB plus rounding.
    bound = (int(amount.to_integral_value(rounding=ROUND_CEILING)) + 1) * 1024**2
    return observed, bound


def render_trial(
    batch: dict,
    selection: dict,
    *,
    observed: datetime | None = None,
    system_bound: int | None = None,
    owner: str = "postgres",
) -> tuple[str, dict]:
    """Build one all-or-nothing trial. Missing evidence produces a blocked review template."""
    if not re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", owner):
        raise ValueError("Invalid owner role identifier.")
    payload = prepare_batch(batch, SCOPE_VERSION)
    if len(payload["filings"]) != 3 or len({r["ein"] for r in payload["filings"]}) != 3:
        raise ValueError("Trial requires exactly three distinct organizations/filings.")
    selected = selection.get("selection", {})
    if set(selected) != {"OH", "KY", "IN"}:
        raise ValueError("Expected the three-state local selection.")
    expected = {r["object_id"]: r for r in selected.values()}
    for row in payload["filings"]:
        original = expected.get(row["source_filing_id"])
        if (
            original is None
            or row["ein"] != original["ein"]
            or row["tax_period_end"].replace("-", "")[:6] != original["tax_period"]
            or row["tax_year"] not in (2023, 2024, 2025)
        ):
            raise ValueError("Staging does not match the reviewed local sample.")
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(raw.encode()) > 65536:
        raise ValueError("Payload exceeds the approved 64 KiB trial limit.")
    if (observed is None) != (system_bound is None):
        raise ValueError("System timestamp and upper bound must be supplied together.")
    if observed is not None and (
        observed.tzinfo is None
        or type(system_bound) is not int
        or not 0 < system_bound < 2_000_000_000
    ):
        raise ValueError("Invalid capacity evidence.")
    timestamp_sql = (
        "null::timestamptz"
        if observed is None
        else dollar_quote(observed.isoformat(), "time") + "::timestamptz"
    )
    system_sql = (
        "null::bigint" if system_bound is None else str(system_bound) + "::bigint"
    )
    payload_sql = dollar_quote(raw, "payload") + "::jsonb"
    # Only validated numeric EINs and a hexadecimal digest enter these literals.
    evidence = "reviewed-local-three:" + payload["manifest_sha256"]
    scope_values = ",\n    ".join(
        f"('{SCOPE_VERSION}', '{r['ein']}', '{evidence}')" for r in payload["filings"]
    )
    preflight = f"""
declare m record; p nonprofit_ingest.storage_policy%rowtype;
        observed timestamptz := {timestamp_sql};
begin
    if current_user <> '{owner}' or not exists (
        select 1 from pg_roles where rolname=current_user and (rolsuper or rolbypassrls)) then
        raise exception 'reviewed_configuration_owner_required';
    end if;
    if observed is null or {system_sql} is null then
        raise exception 'fresh_system_evidence_required_review_template_only';
    end if;
    select * into p from nonprofit_ingest.storage_policy where singleton;
    if not found or p.project_ref <> '{PROJECT_REF}' or p.max_rows <> 3
        or p.stop_bytes <> 1500000000 or p.reserve_bytes <> 268435456
        or p.max_measurement_age_seconds <> 900 or p.max_payload_bytes <> 65536
        or p.included_bytes <> 8000000000 or p.growth_multiplier <> 4
        or p.minimum_bytes_per_filing <> 65536
        or p.approved_tax_years <> array[2023,2024,2025] then
        raise exception 'approved_policy_changed_review_required';
    end if;
    if observed > clock_timestamp()
        or observed < clock_timestamp()-make_interval(secs => p.max_measurement_age_seconds) then
        raise exception 'system_evidence_stale_or_future';
    end if;
    if not exists (select 1 from pg_roles where rolname='nb_loader_dev'
        and not rolcanlogin and not rolsuper and not rolbypassrls
        and not rolcreaterole and not rolcreatedb and not rolreplication) then
        raise exception 'disabled_restricted_loader_required';
    end if;
    select bool_or(a.admin_option) as admin_ok,
           bool_or(a.set_option or a.inherit_option) as elevated
    into m from pg_auth_members a
      join pg_roles r on r.oid=a.roleid join pg_roles u on u.oid=a.member
    where r.rolname='nb_loader_dev' and u.rolname=current_user;
    if m.admin_ok is distinct from true or m.elevated is distinct from false then
        raise exception 'owner_membership_state_unexpected';
    end if;
    if exists(select 1 from nonprofit_ingest.organizations)
        or exists(select 1 from nonprofit_ingest.organization_filings)
        or exists(select 1 from nonprofit_ingest.import_runs)
        or exists(select 1 from nonprofit_ingest.import_run_filings)
        or exists(select 1 from nonprofit_ingest.approved_eins)
        or exists(select 1 from nonprofit_ingest.capacity_measurement) then
        raise exception 'first_trial_target_not_empty_review_before_retry';
    end if;
end
"""
    trial = f"""
declare first_receipt jsonb; repeat_receipt jsonb; payload jsonb := {payload_sql};
begin
    if current_user <> 'nb_loader_dev' then raise exception 'restricted_caller_required'; end if;
    first_receipt := nonprofit_ingest.load_990(payload);
    repeat_receipt := nonprofit_ingest.load_990(payload);
    if first_receipt->>'status' is distinct from 'complete'
       or first_receipt is distinct from repeat_receipt then
        raise exception 'trial_or_idempotency_failed';
    end if;
end
"""
    postflight = """
begin
    if (select count(*) from nonprofit_ingest.organizations) <> 3
        or (select count(*) from nonprofit_ingest.organization_filings) <> 3
        or (select count(*) from nonprofit_ingest.import_runs) <> 1
        or (select count(*) from nonprofit_ingest.import_run_filings) <> 3 then
        raise exception 'trial_counts_failed';
    end if;
    if exists (select 1 from pg_auth_members a
        join pg_roles r on r.oid=a.roleid join pg_roles u on u.oid=a.member
        where r.rolname='nb_loader_dev' and u.rolname=current_user
          and (a.set_option or a.inherit_option)) then
        raise exception 'owner_membership_not_restored';
    end if;
end
"""
    sql = f"""-- LOCAL REVIEW ARTIFACT: contains the three PUBLIC IRS sample records.
-- DO NOT RUN IN SUPABASE WITHOUT EXPLICIT FIRST-DATA-TRIAL APPROVAL.
-- Confirm dedicated dev target {PROJECT_REF}; SQL Editor may retain query text.
-- No passwords, LOGIN activation or Python connection. Run the WHOLE transaction.
-- Metadata missing/stale or any failure rolls back ALL trial writes and grants.
begin;
set local statement_timeout = '120s';
set local lock_timeout = '10s';
do {dollar_quote(preflight, 'preflight')};
insert into nonprofit_ingest.approved_eins(scope_version,ein,evidence_reference) values
    {scope_values};
insert into nonprofit_ingest.capacity_measurement
    (singleton,project_ref,measured_at,database_bytes,other_disk_bytes,provisioned_bytes)
select true,'{PROJECT_REF}',{timestamp_sql},pg_database_size(current_database()),
       (select sum(size)::bigint from pg_ls_waldir())+{system_sql},2000000000;
grant nb_loader_dev to current_user with set true;
set local role nb_loader_dev;
do {dollar_quote(trial, 'trial')};
set local role "{owner}";
grant nb_loader_dev to current_user with set false;
grant nb_loader_dev to current_user with inherit false;
do {dollar_quote(postflight, 'postflight')};
commit;
select 'complete' as trial_status,
       (select count(*) from nonprofit_ingest.organizations) as organizations,
       (select count(*) from nonprofit_ingest.organization_filings) as filings,
       (select count(*) from nonprofit_ingest.import_runs) as import_runs,
       (select count(*) from nonprofit_ingest.import_run_filings) as provenance_links,
       (select rolcanlogin from pg_roles where rolname='nb_loader_dev') as login_enabled,
       pg_database_size(current_database()) as database_bytes_after;
"""
    return sql, {
        "status": "prepared_for_review",
        "filings": 3,
        "fresh_system_evidence_supplied": observed is not None,
        "payload_bytes": len(raw.encode()),
        "database_contacted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sample", type=Path)
    parser.add_argument(
        "output", type=Path, help="NEW SQL file under ignored repo data/"
    )
    parser.add_argument("--system-timestamp-us", type=int)
    parser.add_argument("--system-mb")
    args = parser.parse_args()
    try:
        data_root = Path(__file__).resolve().parents[1] / "data"
        if not args.output.resolve().is_relative_to(data_root.resolve()):
            raise ValueError("Real-data review SQL must stay under ignored data/.")
        batch = json.loads(
            (args.sample / "staged-filings.json").read_text(encoding="utf-8")
        )
        selection = json.loads(
            (args.sample / "selection.json").read_text(encoding="utf-8")
        )
        (manifest,) = (args.sample / "manifests").glob("*.json")
        selected_ids = {r["object_id"] for r in selection["selection"].values()}
        verified = extract_batch(manifest, selected_filing_ids=selected_ids)
        if prepare_batch(batch, SCOPE_VERSION) != prepare_batch(
            verified, SCOPE_VERSION
        ):
            raise ValueError("Staging differs from the checksummed local archive.")
        observed = bound = None
        if args.system_timestamp_us is not None or args.system_mb is not None:
            if args.system_timestamp_us is None or args.system_mb is None:
                raise ValueError("Both System inputs are required.")
            observed, bound = system_evidence(args.system_timestamp_us, args.system_mb)
        sql, summary = render_trial(
            batch, selection, observed=observed, system_bound=bound
        )
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(sql)
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
