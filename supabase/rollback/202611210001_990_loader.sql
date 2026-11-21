-- DESTRUCTIVE DRAFT: only for an explicitly approved empty development target.
-- Export/restore planning is mandatory once records exist. Never run automatically.
begin;
-- Reviewed migration owner must hold ADMIN on this task-owned role.
-- Temporarily inherit function ownership for its removal; role is dropped below.
grant nb_import_executor to current_user with inherit true;
drop function nonprofit_ingest.load_990(jsonb);
drop table nonprofit_ingest.import_run_filings;
drop table nonprofit_ingest.organization_filings;
drop table nonprofit_ingest.import_runs;
drop table nonprofit_ingest.organizations;
drop table nonprofit_ingest.approved_eins;
drop table nonprofit_ingest.capacity_measurement;
drop table nonprofit_ingest.storage_policy;
drop schema nonprofit_ingest;
-- Role memberships/logins must first be reviewed and removed explicitly.
drop role nb_ingest;
drop role nb_import_executor;
commit;
