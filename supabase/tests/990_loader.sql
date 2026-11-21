-- NOT RUN in the authoring environment. Requires the approved up migration.
-- Run only on a disposable local Supabase database as its migration owner:
-- psql ... -v ON_ERROR_STOP=1 -f supabase/tests/990_loader.sql
-- All synthetic records/configuration roll back, including on assertion failure.
begin;
set local statement_timeout = '30s';

create function pg_temp.expect_failure(payload jsonb, expected text) returns void
language plpgsql as $$
begin
    perform nonprofit_ingest.load_990(payload);
    raise exception 'expected_failure_not_raised';
exception when others then
    if sqlerrm <> expected then raise; end if;
end $$;

-- Fixtures are intentionally fictional; schema must be empty for this suite.
do $$ begin
    if has_function_privilege('anon', 'nonprofit_ingest.load_990(jsonb)', 'execute')
       or has_function_privilege('authenticated', 'nonprofit_ingest.load_990(jsonb)', 'execute')
       or has_function_privilege('service_role', 'nonprofit_ingest.load_990(jsonb)', 'execute')
       or not has_function_privilege('nb_ingest', 'nonprofit_ingest.load_990(jsonb)', 'execute') then
        raise exception 'function_acl_incorrect';
    end if;
    if exists (select 1 from nonprofit_ingest.storage_policy)
       or exists (select 1 from nonprofit_ingest.capacity_measurement)
       or exists (select 1 from nonprofit_ingest.import_runs) then
        raise exception 'disposable_empty_database_required';
    end if;
end $$;
select set_config('test.loader_payload', jsonb_build_object(
    'parser_version','form990-xml-provisional-v2', 'manifest_sha256',repeat('b',64),
    'scope_version','synthetic-v1', 'filings',jsonb_build_array(jsonb_build_object(
        'filing_key',encode(sha256(convert_to('synthetic-001','UTF8') || decode('00','hex') || convert_to(repeat('a',64),'UTF8')),'hex'),
        'source_filing_id','synthetic-001','xml_sha256',repeat('a',64),'ein','001234567',
        'tax_period_end','2025-06-30','tax_year',2024,'form_type','990','amended',null,
        'total_revenue',0,'total_expenses',null,'sources',jsonb_build_array(jsonb_build_object(
            'archive_path','synthetic.zip','archive_sha256',repeat('c',64),
            'source_url','https://example.invalid/synthetic.zip',
            'downloaded_at','2026-11-21T12:00:00+00:00','member','synthetic-001_public.xml'))
    )))::text, true);
set local role nb_ingest;
select pg_temp.expect_failure(current_setting('test.loader_payload')::jsonb,'storage_policy_missing');
reset role;

insert into nonprofit_ingest.storage_policy values (
    true,'synthetic-local',8589934592,7516192768,104857600,300,500,array[2023,2024,2025],2097152,4,65536,
    now(),'SYNTHETIC TEST ONLY; not approved operating values');
set local role nb_ingest;
select pg_temp.expect_failure(current_setting('test.loader_payload')::jsonb,'capacity_missing');
reset role;
insert into nonprofit_ingest.capacity_measurement values (
    true,'synthetic-local',now() - interval '1 day',pg_database_size(current_database()),0,8589934592);
set local role nb_ingest;
select pg_temp.expect_failure(current_setting('test.loader_payload')::jsonb,'capacity_stale_mismatched_or_over_allowance');
reset role;
update nonprofit_ingest.capacity_measurement set measured_at = now(), other_disk_bytes = 8589934592;
set local role nb_ingest;
select pg_temp.expect_failure(current_setting('test.loader_payload')::jsonb,'storage_budget_exceeded');
reset role;
update nonprofit_ingest.capacity_measurement set other_disk_bytes = 0;
set local role nb_ingest;
select pg_temp.expect_failure(current_setting('test.loader_payload')::jsonb,'outside_approved_scope');
reset role;
insert into nonprofit_ingest.approved_eins values ('synthetic-v1','001234567','synthetic county fixture');

-- The ingestion role has only the function interface, never direct table access.
set local role nb_ingest;
do $$ begin
    begin
        insert into nonprofit_ingest.organizations(ein) values ('009999999');
        raise exception 'direct_write_was_allowed';
    exception when insufficient_privilege then null;
    end;
    begin
        update nonprofit_ingest.storage_policy set stop_bytes = included_bytes - 1;
        raise exception 'budget_change_was_allowed';
    exception when insufficient_privilege then null;
    end;
end $$;
select nonprofit_ingest.load_990(current_setting('test.loader_payload')::jsonb);
select nonprofit_ingest.load_990(current_setting('test.loader_payload')::jsonb);
reset role;
do $$ begin
    if (select count(*) from nonprofit_ingest.organizations) <> 1
       or (select count(*) from nonprofit_ingest.organization_filings) <> 1
       or (select count(*) from nonprofit_ingest.import_runs) <> 1
       or (select count(*) from nonprofit_ingest.import_run_filings) <> 1 then
        raise exception 'rerun_not_idempotent';
    end if;
    if not exists (select 1 from nonprofit_ingest.organization_filings f
        join nonprofit_ingest.organizations o using (organization_id)
        where o.ein = '001234567' and f.total_revenue = 0 and f.total_expenses is null) then
        raise exception 'zero_null_or_ein_changed';
    end if;
end $$;
set local role anon;
do $$ begin
    begin
        perform nonprofit_ingest.load_990(current_setting('test.loader_payload')::jsonb);
        raise exception 'anonymous_execution_was_allowed';
    exception when insufficient_privilege then null;
    end;
    begin
        perform * from nonprofit_ingest.organization_filings;
        raise exception 'anonymous_read_was_allowed';
    exception when insufficient_privilege then null;
    end;
end $$;
reset role;
-- Cross-run changes must be reviewed; no prior financial fact is overwritten.
set local role nb_ingest;
select pg_temp.expect_failure(
    jsonb_set(current_setting('test.loader_payload')::jsonb,
        '{filings,0,tax_year}', '2022'::jsonb), 'outside_approved_tax_years');
select pg_temp.expect_failure(
    jsonb_set(current_setting('test.loader_payload')::jsonb,
        '{filings,0,tax_year}', 'null'::jsonb), 'outside_approved_tax_years');
select pg_temp.expect_failure(
    jsonb_set(current_setting('test.loader_payload')::jsonb,
        '{filings,0,total_revenue}', '42'::jsonb),
    'existing_filing_conflict_needs_review');
select pg_temp.expect_failure(
    jsonb_set(current_setting('test.loader_payload')::jsonb,
        '{filings,0,total_revenue}', '"0"'::jsonb),
    'invalid_filing_types');
select pg_temp.expect_failure(
    jsonb_set(current_setting('test.loader_payload')::jsonb,
        '{filings,0,filing_key}', to_jsonb(repeat('d',64))),
    'filing_key_mismatch');
reset role;
-- Test a genuinely new batch at exact threshold equality. The snapshot DB size
-- is deliberately larger than live DB bytes for a deterministic conservative gate.
update nonprofit_ingest.capacity_measurement set database_bytes = 1073741824;
update nonprofit_ingest.storage_policy set stop_bytes =
    1073741824 + reserve_bytes + greatest(
        octet_length(current_setting('test.loader_payload')::jsonb::text)::bigint * growth_multiplier,
        minimum_bytes_per_filing);
set local role nb_ingest;
select pg_temp.expect_failure(
    jsonb_set(current_setting('test.loader_payload')::jsonb,
        '{manifest_sha256}', to_jsonb(repeat('d',64))), 'storage_budget_exceeded');
reset role;
update nonprofit_ingest.storage_policy set stop_bytes = 7516192768;
update nonprofit_ingest.capacity_measurement set provisioned_bytes = 8589934593;
set local role nb_ingest;
select pg_temp.expect_failure(current_setting('test.loader_payload')::jsonb,
    'capacity_stale_mismatched_or_over_allowance');
reset role;
update nonprofit_ingest.capacity_measurement set provisioned_bytes = 8589934592, project_ref = 'wrong-target';
set local role nb_ingest;
select pg_temp.expect_failure(current_setting('test.loader_payload')::jsonb,
    'capacity_stale_mismatched_or_over_allowance');
reset role;
update nonprofit_ingest.capacity_measurement set project_ref = 'synthetic-local', measured_at = now() + interval '1 hour';
set local role nb_ingest;
select pg_temp.expect_failure(current_setting('test.loader_payload')::jsonb,
    'capacity_stale_mismatched_or_over_allowance');
reset role;
update nonprofit_ingest.capacity_measurement set measured_at = now();
-- Induce failure AFTER import_run/organization/filing inserts to verify atomicity.
create function pg_temp.reject_provenance() returns trigger language plpgsql as $$
begin raise exception 'synthetic_write_failure'; end $$;
create trigger synthetic_write_failure before insert on nonprofit_ingest.import_run_filings
    for each row execute function pg_temp.reject_provenance();
set local role nb_ingest;
select pg_temp.expect_failure(
    jsonb_set(current_setting('test.loader_payload')::jsonb,
        '{manifest_sha256}', to_jsonb(repeat('e',64))), 'synthetic_write_failure');
reset role;
do $$ begin
    if (select count(*) from nonprofit_ingest.import_runs) <> 1
       or (select count(*) from nonprofit_ingest.import_run_filings) <> 1 then
        raise exception 'partial_run_survived_failure';
    end if;
end $$;
drop trigger synthetic_write_failure on nonprofit_ingest.import_run_filings;
-- Same failed payload succeeds after recovery; no duplicate source filing.
set local role nb_ingest;
select nonprofit_ingest.load_990(jsonb_set(current_setting('test.loader_payload')::jsonb,
    '{manifest_sha256}', to_jsonb(repeat('e',64))));
reset role;
do $$ begin
    if (select count(*) from nonprofit_ingest.import_runs) <> 2
       or (select count(*) from nonprofit_ingest.organization_filings) <> 1
       or (select count(*) from nonprofit_ingest.import_run_filings) <> 2 then
        raise exception 'recovery_or_provenance_link_failed';
    end if;
end $$;
set local role authenticated;
do $$ begin
    begin
        perform nonprofit_ingest.load_990(current_setting('test.loader_payload')::jsonb);
        raise exception 'authenticated_execution_was_allowed';
    exception when insufficient_privilege then null;
    end;
end $$;
reset role;
rollback;
