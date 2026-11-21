-- Mark approved this initial policy on 2026-11-21 for the dedicated dev project.
-- Execution/read-back pending. Run once; review any error before retrying.
-- Inserts the INITIAL THREE-FILING policy only. No measurement, EIN scope,
-- login activation, credential or nonprofit record is inserted by this script.
-- Target project reference: yxtslaaboriakfvpeedi (confirm selected project in UI).
begin;
do $$ begin
    if not exists (select 1 from pg_roles where rolname=current_user
                   and (rolbypassrls or rolsuper)) then
        raise exception 'reviewed_privileged_configuration_owner_required';
    end if;
    if not exists (select 1 from pg_roles where rolname='nb_loader_dev'
                   and not rolcanlogin and not rolbypassrls and not rolsuper) then
        raise exception 'disabled_restricted_loader_required';
    end if;
end $$;
insert into nonprofit_ingest.storage_policy (
    singleton, project_ref, included_bytes, stop_bytes, reserve_bytes,
    max_measurement_age_seconds, max_rows, approved_tax_years,
    max_payload_bytes, growth_multiplier, minimum_bytes_per_filing,
    approved_at, approval_reference
) values (
    true, 'yxtslaaboriakfvpeedi',
    8000000000,  -- conservative floor for the included 8 GB allowance
    1500000000,  -- total projected-disk stop, below current 2 GB provisioned disk
    268435456,   -- 256 MiB additional reserve INSIDE the admission calculation
    900,        -- measurements older than 15 minutes block imports
    3, array[2023,2024,2025],
    65536,      -- 64 KiB maximum JSON batch
    4, 65536,   -- larger of 4x payload or 64 KiB per filing estimates growth
    statement_timestamp(),
    'Owner-authorized initial three-filing dev policy; see 2026-11-21 decision register'
);
-- No ON CONFLICT overwrite: an existing policy requires a new reviewed change.
commit;
