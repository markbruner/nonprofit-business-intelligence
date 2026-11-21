# Supabase — local loader preparation

This directory contains **unapplied drafts**, not an initialized cloud project.
M01: DAT-002/003/005/007/008/011/012/013 and SEC-003/006, partial only.

## Design review and execution hold — 2026-11-21

Mark requested a database-design review and star-schema alignment before creating
tables. Do not apply the current migration. It is an ingestion/staging design,
not an analytics star. Review identified these revisions/decisions:

- Revised: stable internal organization ID; EIN is a constrained business key
  (DAT-002). Filings reference the internal ID.
- Revised: typed financial fields are authoritative; an integrity hash detects
  changed facts without storing a duplicate financial JSON document. Provenance
  remains structured JSON separately.
- Define reporting grain before any dimensional model. Source filing observations
  and one selected organization/annual-period financial observation have different
  grains; summing original and amended returns would double count.
- Proposed direction: normalized ingestion/control tables plus star-shaped SQL
  reporting views (organization and period dimensions, curated financial fact).
  Views avoid a second physical financial copy initially. This is a proposal,
  not an implemented or owner-approved schema change. Filing selection/amendment
  rules and dimension history need explicit decisions before curated publication.
- PostgreSQL 16 migration, restricted-role authorization, capacity, retry and
  recovery tests passed in an isolated local Docker container. Cloud execution
  remains on hold for owner review, real scope evidence and measured settings.

The offline Python loader has eight passing synthetic unit tests. SQL validation
is separate (see below); neither establishes dimensional mart readiness.

`migrations/202611210001_990_loader.sql` defines an unexposed `nonprofit_ingest`
schema with a minimal EIN registry, immutable filing observations, per-run
provenance, import receipts, approved EINs and storage controls. There are no
curated financial selections, screening tables or app-facing policies yet.

The registry uses an internal ID and constrains EIN as a unique business key for
this full-990 slice. Aliases/name/address reconciliation are deferred to the
organization-source task; DAT-002 remains partially covered. Full-990 availability
is not registry coverage.
The allowlist will cover IRS source-listed nonprofits in OH/KY/IN (DAT-013).
Generating it from versioned organization snapshots is not implemented here.
Initial full-990 XML tax-year scope is 2023–2025 inclusive (DAT-003). Configure
`approved_tax_years` only after owner review. Missing or out-of-policy tax years
stop the entire bounded load for review; archive/index year must not substitute.

## Restricted interface

`setup/loader_role.sql` is a separate, unapplied permission preview. It creates
`nb_loader_dev` disabled (NOLOGIN, no password), with CONNECT to the selected
database and inherited `nb_ingest` execution permissions, no ability to SET that
role, no admin option, and no membership in the function-owner role. It sets
connection/time limits. No credentials are created or read by this script.
Owner approval is required before cloud application and separate secure activation.

The migration owner needs CREATE on the target database and CREATEROLE. PostgreSQL
16 requires explicit SET permission for ownership transfer. The draft grants it
temporarily on the executor role, transfers ownership, then disables SET and
INHERIT. The owner retains ADMIN to manage the task-owned role; the loader does
not. Function ACLs are configured BEFORE transferring ownership so a restricted
migration owner cannot silently fail to apply grants/revokes. The destructive
empty-target down migration temporarily inherits ownership for removal.

Connection planning uses the confirmed session pooler on port 5432,
database `postgres`; the session-pooler hostname was provided by Mark. Do not
infer the host from project region. Use a separate reviewed role for reading
capacity if automated collection is later approved; do not grant the loader
policy-update privileges. No connection has been attempted.

- `nb_ingest`: non-login role; only schema usage and function execution.
- `nb_import_executor`: non-login, no BYPASSRLS, function owner; SELECT plus
  INSERT on import tables, SELECT-only for policy/scope/capacity. No UPDATE/DELETE.
- Tables enable and force RLS. No grants to anonymous, authenticated, service-role
  or public callers. Owner-scoped RLS policies permit the function's narrow work.
- The migration creates roles but grants no login membership. Configure a dedicated
  least-privilege connection separately after review; do not use a superuser or
  service-role connection to claim the loader's permission tests passed.
- Migration owner is privileged; SQL-editor queries do not prove app authorization.

## Capacity gate (no default operational values)

The migration owner must separately configure `storage_policy`,
`capacity_measurement` and `approved_eins`. These are not caller-controlled inputs.
The loader cannot configure its own permissions, regional scope or disk budget.

Policy records included bytes, stop bytes BELOW the allowance, overhead reserve,
measurement age, approved XML tax years, payload/row limits, calibrated growth multiplier and minimum bytes
per filing, plus an approval reference. The fresh measurement records the project
reference, provisioned bytes, measured database bytes, and non-database disk usage
(including WAL/system usage) from trusted operational evidence. The loader cannot
measure all of those through ordinary SQL; configuring a measurement collector is
a separate task, not a reason to substitute zero or guess.

Before a write, the function serializes loaders, checks fresh matching measurements
and provisioned capacity, and evaluates:

```
max(live database bytes, measured database bytes)
  + measured other disk bytes + reserve + estimated batch growth
  < min(approved stop bytes, provisioned disk bytes)
```

The estimate is the larger of payload bytes times the growth multiplier and rows
times the minimum bytes per filing. Both must be calibrated with a representative
synthetic/local import and reviewed before real use. Table/index bytes are part of
the live database measurement; reserve covers estimation error and transient growth.
One missing/stale value blocks a load. Existing identical import receipts can be
returned without new writes after fresh policy/capacity validation.

This is a conservative admission check, not a hard provider disk quota. Other
writers, concurrent WAL growth, automatic provider disk growth and imperfect
estimates can still cause overages. Supabase bills provisioned disk, not simply
table sizes. Project-reference verification against the actual connection target
must be part of future approved connection setup.

## Validation and operation boundaries

`tests/990_loader.sql` is a transactional synthetic integration suite for an empty
disposable local database with Supabase's standard role names and a migration-owner
connection. Test values are fictional and NOT approved budgets. It passed on
2026-11-21 using installed `postgis/postgis:16-3.7`, networking disabled, tmpfs
database storage, and synthetic anon/authenticated/service_role roles. This tests
PostgreSQL behavior, not the entire Supabase platform or its managed role grants.

Verified: missing/stale/future/mismatched capacity, over-provisioned disk, exact
threshold equality, over-budget and out-of-scope rejection; ingestion-role direct
write/policy-change denial; anonymous read/execute and authenticated execute denial;
valid zero/null and leading-zero EIN; identical retry; changed facts/type/hash
rejection; forced late-write failure with atomic rollback and successful recovery;
provenance links for repeated observations. Empty-schema down migration and
reapplication also passed. Concurrent writers and interrupted COMMIT/network
outcomes still require separate tests before an unattended/live pipeline.

No database driver or credentials are installed/configured by this slice.
Python `load_batch` accepts an explicitly supplied DB-API connection. Its caller
must own an idle connection/transaction and close it afterward. Use a driver that
supports `%s` parameters (for example a separately reviewed psycopg installation).
The function commits success, rolls back errors and never automatically retries.
After uncertain commit/network failure, reconcile or replay the identical payload;
database receipt keys and filing keys support idempotency. Failed attempts are
not persisted inside the rolled-back transaction: an approved future runner must
capture sanitized failure type/timing separately. Do not log exception text, DSNs
or payloads. This is partial DAT-011 evidence, not complete failure logging.

## Recovery

Runtime errors roll back the whole import transaction. Earlier complete runs remain.
No conflicts overwrite stored facts; no current/amended filing is selected implicitly.
Local source rollback: remove only this task's additions after review, preserving
other work. `rollback/202611210001_990_loader.sql` is a destructive down-migration
draft for an approved EMPTY development target only. Once data exists, export and
rehearse restore before considering it. Never run the down migration automatically.
