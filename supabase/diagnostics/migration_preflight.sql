-- READ ONLY. Run in the explicitly selected empty development project's SQL Editor.
-- Expected: can_create_roles=true, can_create_schema=true,
-- pipeline_schema_exists=false, existing_pipeline_role_count=0.
-- Any other result requires review BEFORE applying the migration.
select
    current_database() as database_name,
    current_user as connection_role,
    current_setting('server_version') as postgres_version,
    r.rolcreaterole as can_create_roles,
    has_database_privilege(current_user, current_database(), 'CREATE') as can_create_schema,
    exists (select 1 from pg_namespace where nspname = 'nonprofit_ingest') as pipeline_schema_exists,
    (select count(*) from pg_roles
     where rolname in ('nb_ingest', 'nb_import_executor', 'nb_loader_dev')) as existing_pipeline_role_count,
    pg_database_size(current_database()) as database_bytes,
    statement_timestamp() as measured_at
from pg_roles r
where r.rolname = current_user;
