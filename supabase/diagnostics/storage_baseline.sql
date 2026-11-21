-- READ ONLY: run as the approved project owner in SQL Editor, never as the loader.
-- Measures current DB and on-disk WAL; NOT total/project System/provisioned disk.
-- If WAL access is denied, report that error; do not expand privileges or enter 0.
select
    current_database() as database_name,
    statement_timestamp() as measured_at,
    pg_database_size(current_database()) as database_bytes,
    (select sum(size)::bigint from pg_ls_waldir()) as wal_bytes;
