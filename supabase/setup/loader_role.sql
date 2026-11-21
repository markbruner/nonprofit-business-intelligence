-- REVIEWABLE DRAFT, not automatically run by migrations.
-- Apply only to the approved dev target AFTER the schema migration.
-- Creates a DISABLED login identity: no password, no LOGIN, no credentials here.
begin;
create role nb_loader_dev nologin inherit nosuperuser nobypassrls
    nocreatedb nocreaterole noreplication connection limit 1;
grant nb_ingest to nb_loader_dev with inherit true;
grant nb_ingest to nb_loader_dev with set false;
do $$ begin
    execute format('grant connect on database %I to nb_loader_dev', current_database());
end $$;
alter role nb_loader_dev set search_path = pg_catalog;
alter role nb_loader_dev set statement_timeout = '120s';
alter role nb_loader_dev set lock_timeout = '10s';
alter role nb_loader_dev set idle_in_transaction_session_timeout = '60s';
-- An approved owner must separately set a strong password securely and enable
-- LOGIN. Use an interactive password command, never literals in SQL/logs/chat.
-- Session-pooler username: nb_loader_dev.<project-ref> (host from Connect panel).
-- Client must verify TLS certificate/hostname and use an idle dedicated connection.
-- Defaults above are safeguards, not resource quotas or billing guarantees.
commit;
