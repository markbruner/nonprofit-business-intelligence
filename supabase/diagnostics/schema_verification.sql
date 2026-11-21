-- READ ONLY. Run after the approved schema-only migration in the dev project.
-- Expected: counts 7/7/7/2; loader_can_execute/function_hardened=true;
-- all other access booleans=false.
with pipeline_tables as (
    select c.relrowsecurity, c.relforcerowsecurity
    from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'nonprofit_ingest' and c.relkind = 'r'
), pipeline_roles as (
    select * from pg_roles where rolname in ('nb_ingest', 'nb_import_executor')
)
select
    (select count(*) from pipeline_tables) as table_count,
    (select count(*) from pipeline_tables where relrowsecurity) as rls_enabled_count,
    (select count(*) from pipeline_tables where relforcerowsecurity) as rls_forced_count,
    (select count(*) from pipeline_roles where not rolcanlogin and not rolsuper
        and not rolbypassrls and not rolcreaterole and not rolcreatedb
        and not rolreplication) as locked_nonlogin_role_count,
    has_function_privilege('nb_ingest', 'nonprofit_ingest.load_990(jsonb)', 'EXECUTE') as loader_can_execute,
    has_function_privilege('anon', 'nonprofit_ingest.load_990(jsonb)', 'EXECUTE') as anonymous_can_execute,
    has_function_privilege('authenticated', 'nonprofit_ingest.load_990(jsonb)', 'EXECUTE') as authenticated_can_execute,
    has_function_privilege('service_role', 'nonprofit_ingest.load_990(jsonb)', 'EXECUTE') as service_role_can_execute,
    has_table_privilege('nb_ingest', 'nonprofit_ingest.organization_filings', 'INSERT') as loader_can_insert_directly,
    has_table_privilege('nb_ingest', 'nonprofit_ingest.storage_policy', 'UPDATE') as loader_can_change_budget,
    exists (
        select 1 from pg_proc p
        join pg_namespace n on n.oid = p.pronamespace
        join pg_roles r on r.oid = p.proowner
        where p.oid = to_regprocedure('nonprofit_ingest.load_990(jsonb)')
          and n.nspname = 'nonprofit_ingest' and r.rolname = 'nb_import_executor'
          and p.prosecdef and p.proconfig @> array['search_path=pg_catalog']
    ) as function_hardened;
