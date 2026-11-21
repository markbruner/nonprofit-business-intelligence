-- Owner-run connection setup only; no password literals, grants, capacity or imports.
-- Dedicated development project yxtslaaboriakfvpeedi. Set password securely FIRST.
-- Authorizes new password-authenticated connections for one hour. Existing sessions
-- are not terminated by password expiry; the probe closes its own connection.
begin;
do $$
begin
    if current_user <> 'postgres' then
        raise exception 'reviewed_owner_required';
    end if;
    if not exists(select 1 from nonprofit_ingest.storage_policy
        where singleton and project_ref='yxtslaaboriakfvpeedi' and max_rows=30
          and stop_bytes=1500000000 and reserve_bytes=268435456
          and max_payload_bytes=65536 and max_measurement_age_seconds=900
          and growth_multiplier=4 and minimum_bytes_per_filing=65536) then
        raise exception 'reviewed_dev_policy_required';
    end if;
    if not exists(select 1 from pg_roles where rolname='nb_loader_dev'
        and not rolcanlogin and not rolsuper and not rolbypassrls
        and not rolcreatedb and not rolcreaterole and not rolreplication
        and rolconnlimit=1) then
        raise exception 'disabled_restricted_loader_required';
    end if;
    if not pg_has_role('nb_loader_dev','nb_ingest','USAGE')
        or pg_has_role('nb_loader_dev','nb_ingest','SET')
        or pg_has_role('nb_loader_dev','nb_import_executor','MEMBER')
        or pg_has_role('nb_loader_dev','postgres','MEMBER')
        or not has_function_privilege('nb_loader_dev','nonprofit_ingest.load_990(jsonb)','EXECUTE')
        or has_schema_privilege('nb_loader_dev','nonprofit_ingest','CREATE')
        or has_schema_privilege('nb_loader_dev','public','CREATE')
        or has_database_privilege('nb_loader_dev',current_database(),'CREATE')
        or exists(select 1 from pg_auth_members a
            where a.member=(select oid from pg_roles where rolname='nb_ingest')
               or (a.member=(select oid from pg_roles where rolname='nb_loader_dev')
                   and (a.roleid<>(select oid from pg_roles where rolname='nb_ingest')
                        or a.admin_option or a.set_option or not a.inherit_option)))
        or exists(select 1 from pg_tables where schemaname='nonprofit_ingest'
            and has_table_privilege('nb_loader_dev',format('%I.%I',schemaname,tablename),
                'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')) then
        raise exception 'loader_privileges_unexpected';
    end if;
    execute format('alter role nb_loader_dev login valid until %L',
        statement_timestamp()+interval '1 hour');
end $$;
commit;
select rolname,rolcanlogin as login_enabled,rolvaliduntil as password_valid_until,
       rolconnlimit as connection_limit
from pg_roles where rolname='nb_loader_dev';
-- Recovery for new connections: ALTER ROLE nb_loader_dev NOLOGIN;
