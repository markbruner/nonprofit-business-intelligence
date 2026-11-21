-- READ ONLY. Run as owner in the dedicated development project's SQL Editor.
-- Returns aggregate storage and counts only; no EINs, financial facts or secrets.
-- System/provisioned disk still require the Disk panel and actual metric timestamp.
-- If WAL access is denied, share the error; do not add grants or substitute zero.
begin transaction read only;
with relation_sizes as (
    select c.relname as table_name,
           pg_table_size(c.oid) as table_bytes,
           pg_indexes_size(c.oid) as index_bytes,
           pg_total_relation_size(c.oid) as total_bytes
    from pg_class c join pg_namespace n on n.oid=c.relnamespace
    where n.nspname='nonprofit_ingest' and c.relkind='r'
), latest_run as (
    select row_count, database_bytes_before, projected_bytes, completed_at
    from nonprofit_ingest.import_runs order by completed_at desc limit 1
)
select current_database() as database_name, current_user as connection_role,
       statement_timestamp() as measured_at,
       pg_database_size(current_database()) as database_bytes,
       (select sum(size)::bigint from pg_ls_waldir()) as wal_bytes,
       (select sum(total_bytes)::bigint from relation_sizes) as ingest_total_bytes,
       (select jsonb_agg(to_jsonb(r) order by table_name) from relation_sizes r) as ingest_relations,
       (select count(*) from nonprofit_ingest.organizations) as organizations,
       (select count(*) from nonprofit_ingest.organization_filings) as filings,
       (select count(*) from nonprofit_ingest.import_runs) as import_runs,
       (select count(*) from nonprofit_ingest.import_run_filings) as provenance_links,
       (select to_jsonb(r) from latest_run r) as latest_run,
       (select jsonb_build_object('stop_bytes',stop_bytes,'reserve_bytes',reserve_bytes,
            'max_rows',max_rows,'max_payload_bytes',max_payload_bytes,
            'growth_multiplier',growth_multiplier,'minimum_bytes_per_filing',minimum_bytes_per_filing,
            'max_measurement_age_seconds',max_measurement_age_seconds)
        from nonprofit_ingest.storage_policy where singleton) as current_policy,
       (select rolcanlogin from pg_roles where rolname='nb_loader_dev') as login_enabled;
commit;
