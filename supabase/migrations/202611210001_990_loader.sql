-- DRAFT: local preparation only. Apply only after target/roles/recovery approval.
-- Intentionally seeds NO policy, capacity measurement, scope, login or credentials.
begin;

create role nb_ingest nologin nosuperuser nobypassrls;
create role nb_import_executor nologin nosuperuser nobypassrls;
create schema nonprofit_ingest;
revoke all on schema nonprofit_ingest from public, anon, authenticated, service_role;
grant usage on schema nonprofit_ingest to nb_ingest, nb_import_executor;

create table nonprofit_ingest.storage_policy (
    singleton boolean primary key default true check (singleton),
    project_ref text not null,
    included_bytes bigint not null check (included_bytes > 0),
    stop_bytes bigint not null check (stop_bytes > 0 and stop_bytes < included_bytes),
    reserve_bytes bigint not null check (reserve_bytes > 0),
    max_measurement_age_seconds integer not null check (max_measurement_age_seconds between 1 and 3600),
    max_rows integer not null check (max_rows between 1 and 500),
    approved_tax_years integer[] not null check (
        cardinality(approved_tax_years) between 1 and 10
        and array_position(approved_tax_years, null) is null
        and 1000 <= all(approved_tax_years) and 9999 >= all(approved_tax_years)),
    max_payload_bytes integer not null check (max_payload_bytes between 1 and 2097152),
    growth_multiplier integer not null check (growth_multiplier >= 2),
    minimum_bytes_per_filing bigint not null check (minimum_bytes_per_filing > 0),
    approved_at timestamptz not null,
    approval_reference text not null
);
create table nonprofit_ingest.capacity_measurement (
    singleton boolean primary key default true check (singleton),
    project_ref text not null,
    measured_at timestamptz not null,
    database_bytes bigint not null check (database_bytes >= 0),
    other_disk_bytes bigint not null check (other_disk_bytes >= 0),
    provisioned_bytes bigint not null check (provisioned_bytes > 0)
);
create table nonprofit_ingest.approved_eins (
    scope_version text not null,
    ein text not null check (ein ~ '^[0-9]{9}$'),
    evidence_reference text not null,
    primary key (scope_version, ein)
);
create table nonprofit_ingest.organizations (
    organization_id bigint generated always as identity primary key,
    ein text not null unique check (ein ~ '^[0-9]{9}$'),
    created_at timestamptz not null default now()
);
-- EIN is a constrained business key; relationships use the stable internal ID.
-- Names/addresses/aliases and curated financial selection await their own tasks.
create table nonprofit_ingest.import_runs (
    run_key text primary key check (run_key ~ '^[0-9a-f]{64}$'),
    manifest_sha256 text not null check (manifest_sha256 ~ '^[0-9a-f]{64}$'),
    parser_version text not null,
    scope_version text not null,
    completed_at timestamptz not null default now(),
    row_count integer not null,
    database_bytes_before bigint not null,
    projected_bytes bigint not null,
    provisioned_bytes bigint not null,
    measurement_time timestamptz not null,
    receipt jsonb not null
);
create table nonprofit_ingest.organization_filings (
    filing_key text primary key check (filing_key ~ '^[0-9a-f]{64}$'),
    organization_id bigint not null references nonprofit_ingest.organizations(organization_id),
    source_filing_id text not null check (source_filing_id ~ '^[A-Za-z0-9_-]{1,100}$'),
    xml_sha256 text not null check (xml_sha256 ~ '^[0-9a-f]{64}$'),
    tax_period_end date not null,
    tax_year integer check (tax_year between 1000 and 9999),
    form_type text not null check (form_type = '990'),
    amended boolean,
    total_revenue bigint check (abs(total_revenue::numeric) < 1000000000000000000),
    total_expenses bigint check (abs(total_expenses::numeric) < 1000000000000000000),
    facts_sha256 text not null check (facts_sha256 ~ '^[0-9a-f]{64}$'),
    imported_at timestamptz not null default now()
);
create index filings_period on nonprofit_ingest.organization_filings(organization_id, tax_period_end);
create index filings_source on nonprofit_ingest.organization_filings(source_filing_id);
create table nonprofit_ingest.import_run_filings (
    run_key text not null references nonprofit_ingest.import_runs(run_key),
    filing_key text not null references nonprofit_ingest.organization_filings(filing_key),
    sources jsonb not null check (jsonb_typeof(sources) = 'array' and jsonb_array_length(sources) between 1 and 20),
    primary key (run_key, filing_key)
);

-- RLS applies even to the function's narrow, non-login owner.
do $$
declare t text;
begin
    foreach t in array array['storage_policy', 'capacity_measurement', 'approved_eins',
        'organizations', 'import_runs', 'organization_filings', 'import_run_filings'] loop
        execute format('alter table nonprofit_ingest.%I enable row level security', t);
        execute format('alter table nonprofit_ingest.%I force row level security', t);
        execute format('create policy executor_read on nonprofit_ingest.%I for select to nb_import_executor using (true)', t);
    end loop;
    foreach t in array array['organizations', 'import_runs', 'organization_filings', 'import_run_filings'] loop
        execute format('create policy executor_insert on nonprofit_ingest.%I for insert to nb_import_executor with check (true)', t);
        execute format('grant insert on nonprofit_ingest.%I to nb_import_executor', t);
    end loop;
end $$;
revoke all on all tables in schema nonprofit_ingest from public, anon, authenticated, service_role, nb_ingest;
grant select on all tables in schema nonprofit_ingest to nb_import_executor;
grant usage on sequence nonprofit_ingest.organizations_organization_id_seq to nb_import_executor;

create function nonprofit_ingest.load_990(payload jsonb) returns jsonb
language plpgsql security definer set search_path = pg_catalog
as $$
declare
    policy nonprofit_ingest.storage_policy%rowtype;
    capacity nonprofit_ingest.capacity_measurement%rowtype;
    item jsonb;
    source jsonb;
    facts_hash text;
    batch_key text;
    result jsonb;
    actual_bytes bigint;
    estimated_growth numeric;
    projected numeric;
    row_count integer;
begin
    -- One loader at a time, including all policy/capacity reads and writes.
    perform pg_advisory_xact_lock(741021, 990);
    select * into policy from nonprofit_ingest.storage_policy where singleton;
    if not found then raise exception 'storage_policy_missing'; end if;
    select * into capacity from nonprofit_ingest.capacity_measurement where singleton;
    if not found then raise exception 'capacity_missing'; end if;
    if capacity.project_ref <> policy.project_ref
        or capacity.measured_at > clock_timestamp()
        or capacity.measured_at < clock_timestamp() - make_interval(secs => policy.max_measurement_age_seconds)
        or capacity.provisioned_bytes > policy.included_bytes then
        raise exception 'capacity_stale_mismatched_or_over_allowance';
    end if;
    if jsonb_typeof(payload) is distinct from 'object'
        or payload->>'parser_version' is distinct from 'form990-xml-provisional-v2'
        or (payload->>'manifest_sha256' ~ '^[0-9a-f]{64}$') is distinct from true
        or (payload->>'scope_version' ~ '^[A-Za-z0-9_-]{1,80}$') is distinct from true
        or jsonb_typeof(payload->'filings') is distinct from 'array' then
        raise exception 'invalid_batch';
    end if;
    row_count := jsonb_array_length(payload->'filings');
    if row_count < 1 or row_count > policy.max_rows
        or octet_length(payload::text) > policy.max_payload_bytes then
        raise exception 'batch_limit';
    end if;
    batch_key := encode(sha256(convert_to(payload::text, 'UTF8')), 'hex');
    select receipt into result from nonprofit_ingest.import_runs where run_key = batch_key;
    if found then return result; end if;
    actual_bytes := pg_database_size(current_database());
    estimated_growth := greatest(
        octet_length(payload::text)::numeric * policy.growth_multiplier,
        row_count::numeric * policy.minimum_bytes_per_filing);
    projected := greatest(actual_bytes, capacity.database_bytes)::numeric
        + capacity.other_disk_bytes + policy.reserve_bytes + estimated_growth;
    if projected >= least(policy.stop_bytes, capacity.provisioned_bytes) then
        raise exception 'storage_budget_exceeded';
    end if;
    if (select count(distinct r->>'filing_key') from jsonb_array_elements(payload->'filings') r) <> row_count
        or (select count(distinct r->>'source_filing_id') from jsonb_array_elements(payload->'filings') r) <> row_count
        or exists (select 1 from jsonb_array_elements(payload->'filings') r
                   group by r->>'ein', r->>'tax_period_end' having count(*) > 1) then
        raise exception 'duplicate_or_conflicting_batch';
    end if;
    for item in select value from jsonb_array_elements(payload->'filings') loop
        if jsonb_typeof(item) is distinct from 'object'
            or (select count(*) from jsonb_object_keys(item)) <> 11
            or not (item ?& array['filing_key','source_filing_id','xml_sha256','ein','tax_period_end',
                'tax_year','form_type','amended','total_revenue','total_expenses','sources'])
            or (item->>'ein' ~ '^[0-9]{9}$') is distinct from true
            or (item->>'xml_sha256' ~ '^[0-9a-f]{64}$') is distinct from true
            or (item->>'source_filing_id' ~ '^[A-Za-z0-9_-]{1,100}$') is distinct from true
            or item->>'form_type' is distinct from '990'
            or (item->>'tax_period_end' ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$') is distinct from true
            or jsonb_typeof(item->'sources') is distinct from 'array' then
            raise exception 'invalid_filing';
        end if;
        if item->>'filing_key' is distinct from encode(sha256(
            convert_to(item->>'source_filing_id', 'UTF8') || decode('00', 'hex')
            || convert_to(item->>'xml_sha256', 'UTF8')), 'hex') then
            raise exception 'filing_key_mismatch';
        end if;
        if jsonb_typeof(item->'ein') <> 'string'
            or jsonb_typeof(item->'tax_period_end') <> 'string'
            or jsonb_typeof(item->'tax_year') not in ('number', 'null')
            or (item->>'tax_year' is not null and item->>'tax_year' !~ '^[0-9]{4}$')
            or jsonb_typeof(item->'amended') not in ('boolean', 'null')
            or jsonb_typeof(item->'total_revenue') not in ('number', 'null')
            or jsonb_typeof(item->'total_expenses') not in ('number', 'null')
            or (item->>'total_revenue' is not null and item->>'total_revenue' !~ '^-?[0-9]{1,18}$')
            or (item->>'total_expenses' is not null and item->>'total_expenses' !~ '^-?[0-9]{1,18}$') then
            raise exception 'invalid_filing_types';
        end if;
        if item->>'tax_year' is null
            or not ((item->>'tax_year')::integer = any(policy.approved_tax_years)) then
            raise exception 'outside_approved_tax_years';
        end if;
        if not exists (select 1 from nonprofit_ingest.approved_eins a
            where a.scope_version = payload->>'scope_version' and a.ein = item->>'ein') then
            raise exception 'outside_approved_scope';
        end if;
        if jsonb_array_length(item->'sources') not between 1 and 20 then
            raise exception 'invalid_provenance';
        end if;
        for source in select value from jsonb_array_elements(item->'sources') loop
            if jsonb_typeof(source) is distinct from 'object'
                or (source->>'archive_sha256' ~ '^[0-9a-f]{64}$') is distinct from true
                or (source->>'source_url' like 'https://%') is distinct from true
                or coalesce(length(source->>'member'), 0) not between 1 and 2048
                or coalesce(length(source->>'archive_path'), 0) not between 1 and 2048
                or coalesce(length(source->>'downloaded_at'), 0) not between 1 and 2048 then
                raise exception 'invalid_provenance';
            end if;
            if (select count(*) from jsonb_object_keys(source)) <> 5
                or not (source ?& array['archive_path','archive_sha256','source_url','downloaded_at','member'])
                or jsonb_typeof(source->'archive_path') <> 'string'
                or jsonb_typeof(source->'archive_sha256') <> 'string'
                or jsonb_typeof(source->'source_url') <> 'string'
                or jsonb_typeof(source->'downloaded_at') <> 'string'
                or jsonb_typeof(source->'member') <> 'string'
                or length(source->>'source_url') > 2048
                or source->>'downloaded_at' !~ '(Z|[+-][0-9]{2}:[0-9]{2})$' then
                raise exception 'invalid_provenance_types';
            end if;
            perform (source->>'downloaded_at')::timestamptz;
        end loop;
        facts_hash := encode(sha256(convert_to((item - 'sources')::text, 'UTF8')), 'hex');
        if exists (select 1 from nonprofit_ingest.organization_filings f
            join nonprofit_ingest.organizations o using (organization_id)
            where (f.filing_key = item->>'filing_key' and f.facts_sha256 <> facts_hash)
               or (f.filing_key <> item->>'filing_key' and
                  (f.source_filing_id = item->>'source_filing_id'
                   or (o.ein = item->>'ein' and f.tax_period_end = (item->>'tax_period_end')::date)))) then
            raise exception 'existing_filing_conflict_needs_review';
        end if;
    end loop;
    result := jsonb_build_object('status','complete', 'run_key',batch_key, 'filings',row_count);
    insert into nonprofit_ingest.import_runs
        (run_key, manifest_sha256, parser_version, scope_version, row_count,
         database_bytes_before, projected_bytes, provisioned_bytes, measurement_time, receipt)
    values (batch_key, payload->>'manifest_sha256', payload->>'parser_version', payload->>'scope_version',
        row_count, actual_bytes, projected::bigint, capacity.provisioned_bytes, capacity.measured_at, result);
    for item in select value from jsonb_array_elements(payload->'filings') loop
        insert into nonprofit_ingest.organizations(ein) values (item->>'ein') on conflict do nothing;
        insert into nonprofit_ingest.organization_filings
            (filing_key, organization_id, source_filing_id, xml_sha256, tax_period_end, tax_year,
             form_type, amended, total_revenue, total_expenses, facts_sha256)
        values (item->>'filing_key',
            (select organization_id from nonprofit_ingest.organizations where ein = item->>'ein'),
            item->>'source_filing_id', item->>'xml_sha256',
            (item->>'tax_period_end')::date, (item->>'tax_year')::integer, item->>'form_type',
            (item->>'amended')::boolean, (item->>'total_revenue')::bigint,
            (item->>'total_expenses')::bigint,
            encode(sha256(convert_to((item - 'sources')::text, 'UTF8')), 'hex')) on conflict do nothing;
        insert into nonprofit_ingest.import_run_filings(run_key, filing_key, sources)
        values (batch_key, item->>'filing_key', item->'sources');
    end loop;
    return result;
end $$;
-- Temporary CREATE is needed solely to transfer function ownership.
-- Set the ACL while the migration role still owns the function; after transfer
-- a non-superuser cannot grant/revoke without assuming or inheriting its owner.
revoke all on function nonprofit_ingest.load_990(jsonb) from public, anon, authenticated, service_role;
grant execute on function nonprofit_ingest.load_990(jsonb) to nb_ingest;
grant create on schema nonprofit_ingest to nb_import_executor;
-- PostgreSQL 16 CREATEROLE does not imply SET ROLE on a role it creates.
-- The migration owner already holds ADMIN; permit only this ownership transfer.
grant nb_import_executor to current_user with set true;
alter function nonprofit_ingest.load_990(jsonb) owner to nb_import_executor;
grant nb_import_executor to current_user with set false;
grant nb_import_executor to current_user with inherit false;
revoke create on schema nonprofit_ingest from nb_import_executor;
commit;
