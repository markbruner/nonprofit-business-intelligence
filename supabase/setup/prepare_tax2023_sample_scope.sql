-- Owner-run setup for the 13-record tax-2023 sample batch.
-- Dedicated dev project yxtslaaboriakfvpeedi.
-- Seeds approved scope, stamps fresh capacity, and opens 1-hour loader LOGIN.
begin;
do $$
begin
    if current_user <> 'postgres' then
        raise exception 'reviewed_owner_required';
    end if;
    if not exists(select 1 from nonprofit_ingest.storage_policy
        where singleton and project_ref='yxtslaaboriakfvpeedi' and max_rows=30
          and stop_bytes=1500000000 and reserve_bytes=268435456
          and max_payload_bytes=65536 and max_measurement_age_seconds=900) then
        raise exception 'reviewed_dev_policy_required';
    end if;
    if not exists(select 1 from pg_roles where rolname='nb_loader_dev'
        and not rolsuper and not rolbypassrls and not rolcreatedb
        and not rolcreaterole and not rolreplication and rolconnlimit=1) then
        raise exception 'restricted_loader_required';
    end if;
end $$;

-- 1. Seed the 13 approved EINs for this sample scope
insert into nonprofit_ingest.approved_eins(scope_version, ein, evidence_reference) values
    ('oh-ky-in-tax2023-sample-v1', '610716816', 'data/irs-tax2023-pipeline-20261121-02/plan.json'),
    ('oh-ky-in-tax2023-sample-v1', '344444311', 'data/irs-tax2023-pipeline-20261121-02/plan.json'),
    ('oh-ky-in-tax2023-sample-v1', '881999697', 'data/irs-tax2023-pipeline-20261121-02/plan.json'),
    ('oh-ky-in-tax2023-sample-v1', '351898835', 'data/irs-tax2023-pipeline-20261121-02/plan.json'),
    ('oh-ky-in-tax2023-sample-v1', '461518852', 'data/irs-tax2023-pipeline-20261121-02/plan.json'),
    ('oh-ky-in-tax2023-sample-v1', '237307013', 'data/irs-tax2023-pipeline-20261121-02/plan.json'),
    ('oh-ky-in-tax2023-sample-v1', '352152098', 'data/irs-tax2023-pipeline-20261121-02/plan.json'),
    ('oh-ky-in-tax2023-sample-v1', '461195331', 'data/irs-tax2023-pipeline-20261121-02/plan.json'),
    ('oh-ky-in-tax2023-sample-v1', '310995844', 'data/irs-tax2023-pipeline-20261121-02/plan.json'),
    ('oh-ky-in-tax2023-sample-v1', '272096655', 'data/irs-tax2023-pipeline-20261121-02/plan.json'),
    ('oh-ky-in-tax2023-sample-v1', '310242575', 'data/irs-tax2023-pipeline-20261121-02/plan.json'),
    ('oh-ky-in-tax2023-sample-v1', '311085555', 'data/irs-tax2023-pipeline-20261121-02/plan.json'),
    ('oh-ky-in-tax2023-sample-v1', '351065063', 'data/irs-tax2023-pipeline-20261121-02/plan.json')
on conflict (scope_version, ein) do nothing;

-- 2. Stamp fresh capacity measurement
insert into nonprofit_ingest.capacity_measurement
    (singleton, project_ref, measured_at, database_bytes, other_disk_bytes, provisioned_bytes)
select true, 'yxtslaaboriakfvpeedi', statement_timestamp(),
       pg_database_size(current_database()),
       (select sum(size)::bigint from pg_ls_waldir()) + (169 * 1024 * 1024) + (2 * 1024 * 1024),
       2000000000
on conflict (singleton) do update set
    project_ref = excluded.project_ref,
    measured_at = excluded.measured_at,
    database_bytes = excluded.database_bytes,
    other_disk_bytes = excluded.other_disk_bytes,
    provisioned_bytes = excluded.provisioned_bytes;

-- 3. Open temporary 1-hour loader login window
do $$
begin
    execute format('alter role nb_loader_dev login valid until %L',
        statement_timestamp() + interval '1 hour');
end $$;

commit;

-- Confirm prepared state
select
    (select count(*) from nonprofit_ingest.approved_eins where scope_version = 'oh-ky-in-tax2023-sample-v1') as approved_eins_count,
    (select measured_at from nonprofit_ingest.capacity_measurement where singleton) as capacity_stamped_at,
    (select rolcanlogin from pg_roles where rolname = 'nb_loader_dev') as login_enabled,
    (select rolvaliduntil from pg_roles where rolname = 'nb_loader_dev') as password_valid_until;
