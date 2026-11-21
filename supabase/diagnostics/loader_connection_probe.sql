-- One read-only metadata query, executed as the actual nb_loader_dev connection.
-- No import-function call and no organization, filing, scope or capacity data read.
select jsonb_build_object(
    'database_name',current_database(),
    'connection_role',current_user,
    'login_enabled',r.rolcanlogin,
    'password_valid',r.rolvaliduntil > clock_timestamp(),
    'connection_limit',r.rolconnlimit,
    'read_only',current_setting('transaction_read_only')='on',
    'superuser',r.rolsuper,
    'bypass_rls',r.rolbypassrls,
    'can_create_database',r.rolcreatedb,
    'can_create_roles',r.rolcreaterole,
    'replication',r.rolreplication,
    'inherits_ingest',pg_has_role(current_user,'nb_ingest','USAGE'),
    'can_set_ingest',pg_has_role(current_user,'nb_ingest','SET'),
    'executor_member',pg_has_role(current_user,'nb_import_executor','MEMBER'),
    'owner_member',pg_has_role(current_user,'postgres','MEMBER'),
    'can_execute',has_function_privilege(current_user,'nonprofit_ingest.load_990(jsonb)','EXECUTE'),
    'can_create_schema',has_database_privilege(current_user,current_database(),'CREATE'),
    'can_create_in_ingest',has_schema_privilege(current_user,'nonprofit_ingest','CREATE'),
    'can_create_in_public',has_schema_privilege(current_user,'public','CREATE'),
    'unexpected_membership',exists(select 1 from pg_auth_members a
        where a.member=(select oid from pg_roles where rolname='nb_ingest')
           or (a.member=r.oid and (a.roleid<>(select oid from pg_roles where rolname='nb_ingest')
                or a.admin_option or a.set_option or not a.inherit_option))),
    'direct_table_access',exists(select 1 from pg_tables where schemaname='nonprofit_ingest'
        and has_table_privilege(current_user,format('%I.%I',schemaname,tablename),
            'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER'))
) from pg_roles r where r.rolname=current_user;
