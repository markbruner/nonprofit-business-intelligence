-- READ ONLY. Run after the explicitly approved disabled-loader setup.
-- Expected: role exists, all privilege/login flags false, connection_limit=1;
-- can_connect/can_execute/inherits_ingest=true; remaining access booleans=false.
select
    r.rolname as role_name,
    r.rolcanlogin as login_enabled,
    r.rolsuper as superuser,
    r.rolcreatedb as can_create_database,
    r.rolcreaterole as can_create_roles,
    r.rolreplication as replication,
    r.rolbypassrls as bypass_rls,
    r.rolconnlimit as connection_limit,
    has_database_privilege(r.rolname, current_database(), 'CONNECT') as can_connect,
    pg_has_role(r.rolname, 'nb_ingest', 'USAGE') as inherits_ingest,
    pg_has_role(r.rolname, 'nb_ingest', 'SET') as can_set_ingest,
    pg_has_role(r.rolname, 'nb_import_executor', 'MEMBER') as executor_member,
    has_function_privilege(r.rolname, 'nonprofit_ingest.load_990(jsonb)', 'EXECUTE') as can_execute,
    has_table_privilege(r.rolname, 'nonprofit_ingest.organization_filings', 'INSERT') as direct_insert,
    has_table_privilege(r.rolname, 'nonprofit_ingest.storage_policy', 'UPDATE') as can_change_budget
from pg_roles r
where r.rolname = 'nb_loader_dev';
