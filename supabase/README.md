# Supabase — local loader preparation

The initial schema migration was applied manually by Mark to the dedicated cloud
development project and its reported metadata checks passed. The disabled-loader
identity and initial storage policy were applied by Mark and their metadata checks
passed. Rollback scripts remain unapplied; login activation and data imports are
not authorized. CLI configuration/migration history is not initialized here.
M01: DAT-002/003/005/007/008/011/012/013 and SEC-003/006, partial only.

## Design review and execution status — 2026-11-21

Mark requested database-design review and star-schema alignment before creating
tables. Following revisions and local PostgreSQL 17.12 tests, Mark approved the
schema-only migration for the dedicated cloud development project. He ran it
manually and returned the expected `diagnostics/schema_verification.sql` results:
counts 7/7/7/2, loader execution and function hardening true, other access flags
false. This is metadata verification, not a live loader or app authorization test.
This is an
ingestion/staging design, not an analytics star. Do not apply setup/rollback files
or load records under this approval. Review identified these revisions/decisions:

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
  recovery tests passed in isolated local Docker containers (16 and 17.12).
  Schema-only cloud trial is approved; data loading still requires real scope
  evidence, measured settings and separate execution approval.

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

`setup/storage_policy.sql` is the owner-approved initial three-filing policy,
applied manually with matching owner-returned read-back:
1.5 billion byte projected-disk stop, 256 MiB reserve, 15-minute measurement age,
3-row / 64 KiB batch limits, growth max(4x payload, 64 KiB/row), tax years 2023–2025.
It inserts policy only and refuses to overwrite an existing row. It requires a
reviewed privileged owner and disabled loader. No capacity/scope seed or LOGIN
activation is bundled. `diagnostics/storage_policy_verification.sql` reads it back.
Do not run either a policy-changing script or a load merely because it is in Git.

Mark's planning snapshot supplied exact SQL DB/WAL bytes and rounded provider
System/provisioned units. Conservative interpretation uses a 2-billion-byte
provisioned floor and 168 MiB System upper bound for reported 167 MB. Preserve
the underlying component timestamps: use the OLDEST, not insertion time, for a
capacity snapshot. Unit-bound assumptions require owner approval. These readings
must be refreshed when stale; policy setup deliberately does not seed them.

Local-only calibration is in `tests/storage_calibration.sql` and refuses other
database names. On PostgreSQL 17.12, 1,000 synthetic organizations and 3,000 filings
added 4,505,600 schema bytes including indexes (1,501.87 bytes/filing amortized).
This is one shape/ratio, not a production-size guarantee or approved cloud policy.
Fixture policy values must never be copied into cloud configuration automatically.

`diagnostics/storage_baseline.sql` reads current DB and on-disk WAL as the approved
owner; it does not measure System/provisioned disk. Permission failure is not zero.
Supabase documents that dashboard disk metrics update daily; retain the actual
metric timestamp and do not label an old metric fresh merely because it was viewed
now. Resolve freshness/measurement limitations before seeding capacity or enabling
imports. Source: https://supabase.com/docs/guides/platform/database-size

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

On 2026-11-21, Mark's read-only cloud metadata showed PostgreSQL 17.12. The official
`postgres:17` local image also reported 17.12; migration, synthetic SQL suite,
disabled-loader setup and empty-schema rollback passed under a non-superuser
CREATEROLE database owner. This strengthens version compatibility evidence but
does not verify Supabase's managed-role hooks or approve a cloud write.

Before the first cloud write, run `diagnostics/migration_preflight.sql` read-only
in the explicitly selected development project. Expected: role/schema creation
capabilities true, pipeline schema absent, pipeline role count zero. Review other
results; do not drop/reuse unexpected objects automatically. The first cloud
migration is schema-only and requires explicit approval; budgets/scope/capacity
remain unset, so ingestion remains blocked. Loader identity setup/activation and
data uploads are separate operations. Database size alone is not total disk use.

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

## Post-import storage and next batch

Post-second-trial read-back at 17:29:55 UTC confirms max_rows=30, unchanged remaining
returned safeguards, counts 33/33/2/33 and LOGIN false. Current DB=11,622,067 bytes,
ingestion relations=352,256, WAL=83,886,444. DB and relation interval growth each
73,728 bytes; small-sample evidence only. Retain growth/reserve limits. Earlier
requests for the second-trial read-back below are historical and now satisfied.

Latest completion: Mark returned the next trial's expected 33 organizations,
33 filings, 2 import runs, 33 links; LOGIN false, DB 11,622,067 bytes. The presented
transaction leaves max_rows=30. Run `diagnostics/post_import_storage.sql` again to
read back policy, relation sizes, WAL and the second run's baseline before further
batch planning. No further import is authorized; do not rerun either trial script.
Earlier preparation checkpoints below are historical.

Latest checkpoint: owner returned successful diagnostic with counts 3/3/1/3,
11,548,339 database bytes, 83,886,444 WAL bytes and 278,528 ingestion relation bytes.
DB delta from recorded pre-import baseline is 90,112 bytes; do not extrapolate from
three filings. At 17:23 UTC the Disk panel shows 273.26 MB total, System 167.54 MB,
Database 25.72 MB. Conservative next-batch projection including reserve/growth is
559,808,876 bytes. The larger panel Database category is accounted for separately.
Thirty-record continuation SQL passed isolated PostgreSQL 17.12 tests; cloud run
and exact max_rows 3->30 change are pending explicit approval. Other limits and
LOGIN remain unchanged. See NEXT-BATCH-PREFLIGHT.md for complete evidence.

Run `diagnostics/post_import_storage.sql` as the owner in the dedicated dev project
and return its aggregate result. The transaction is read-only: DB/WAL bytes,
per-table/index sizes, counts, latest import baseline and current policy. No grants,
EINs or financial facts are emitted. Supply Disk panel System usage, provisioned
size and actual metric timestamp separately. Do not substitute zero on errors.
The owner has returned its successful cloud result; it also passed locally.

Thirty new filings are prepared locally (ten/state; 9 tax-2025, 21 tax-2024), with
no source identity/period/year or quality findings. Payload 20,121 compact bytes;
current conservative growth floor is 1,966,080 bytes. No policy change or upload
occurred; max_rows remains 3. Review storage before a separate exact policy/batch
approval. See `../docs/delivery/NEXT-BATCH-PREFLIGHT.md`.

## First data trial — owner-run completion

Mark approved and manually ran `first-cloud-trial-20261121-1715.sql` with System
evidence 167.53 MB at 17:15 UTC on 2026-11-21. Returned complete: 3 organizations,
3 filings, 1 import run, 3 provenance links, LOGIN false; database size 11,548,339
bytes. No agent connection or authenticated Python transport was used. The
following preparation notes describe the earlier review template. Do not rerun
either first-trial artifact now that the target contains data. Further uploads
require a separately reviewed batch and current capacity evidence.

`scripts/prepare_cloud_trial.py` re-extracts the three local sample filings from
their checksummed archive and compares them with staging, validates the index
selection and creates a NEW Git-ignored SQL review artifact. It never connects
to Supabase, reads credentials or enables LOGIN.

The current `data/irs-xml-sample-20261121-01/first-cloud-trial-REVIEW.sql` has NULL
System inputs and deliberately raises before writes. Do not paste/run this review
template in Supabase. It contains three public financial observations; SQL Editor
may retain query text, so actual execution requires explicit data-upload approval.

The execution design adds only those three EINs, measures DB/WAL live as owner,
retains the System observation's original timestamp, temporarily assumes the
disabled loader role, calls the guarded import twice, restores SET/INHERIT false
and verifies counts, all in one transaction. It checks an empty target and the
approved policy exactly. No password or network driver is needed for this trial.
It tests the SQL path, not an authenticated Python pipeline.

Local PostgreSQL 17.12 tests with a real non-superuser owner session passed the
success, duplicate-repeat, missing/stale/over-budget and whole-script replay cases.
Expected success: 3 organizations, 3 filings, 1 run, 3 provenance links; login false.
Fresh evidence and approval were supplied for the completed trial only. See
`../docs/delivery/CLOUD-TRIAL-PREFLIGHT.md`. Do not reuse expired capacity evidence.

## Recovery and migration history

The cloud schema was applied through SQL Editor, not CLI migration tracking. Before
introducing `supabase db push`, review and reconcile migration history explicitly;
do not rerun the applied CREATE-role migration or automatically repair the ledger.
Future schema changes require a new versioned migration and approval.

Runtime errors roll back the whole import transaction. Earlier complete runs remain.
No conflicts overwrite stored facts; no current/amended filing is selected implicitly.
Local source rollback: remove only this task's additions after review, preserving
other work. `rollback/202611210001_990_loader.sql` is a destructive down-migration
draft for an approved EMPTY development target only. Once data exists, export and
rehearse restore before considering it. Never run the down migration automatically.
