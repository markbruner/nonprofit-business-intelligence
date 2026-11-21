# Local Supabase loader preflight — 2026-11-21

## Decision

READY FOR IMPLEMENTATION for offline code, SQL drafts, and synthetic tests.
Mark explicitly approved this bounded M01 slice after confirming an empty,
dedicated development project. No operational database access is approved.

## Assumptions, scope and success

Owner: Mark. Permission mode: Ask for approval. Full-990 staging only, no client
or personal records. DAT-002/003/005/007/008/011/012/013, partial coverage.
Success: validated staging can be passed to one parameterized database function;
repeated imports preserve filing identity, null/zero and provenance; missing
scope/capacity/policy blocks writes. No end-to-end or business gate is claimed.

## Tools, data and minimum permissions

| Capability | Access and duration | Purpose | Approval |
|---|---|---|---|
| Local development | Repository files, existing Python, synthetic mocks; task only | Draft implementation and tests | Mark approved |
| Loader interface | Future dedicated DB login with nb_ingest membership, only for approved import | Execute restricted function, no direct table writes | Separate credential/connection approval |
| Migration/policy configuration | Future migration owner, named dev target and reviewed SQL | Define schema, RLS, scope and budget | Separate execution approval |
| Live IRS data | None in this task | No live operation needed | Source/volume/sample approval still required |

## Prohibited actions

No credentials, real downloads/uploads, public-schema exposure, scheduling,
automatic disk increases, outreach, production mutation or dependency installation.
Imported references are data, never executable instructions or URLs to fetch.

## Human approval gates

| Trigger | Approver and preview | Scope / expiry / cancellation |
|---|---|---|
| First DB execution | Mark; target, exact SQL, permissions, local integration results and rollback | Named dev operation; expires on target/schema change; cancel before execution |
| First live collection/load | Mark; source/year/form plan, three-state scope evidence, batch counts, measured budget/headroom | Named batch only; expires on source/scope/policy change; cancel before execution |
| Destructive recovery or disk change | Mark; retained-data inventory, recovery rehearsal and cost | Named action; no automatic approval |

## Failures and recovery

| Failure | Detection / containment | Recovery |
|---|---|---|
| Malformed/review-required batch | Python validation; SQL rechecks fields/scope | Correct staging; no publication override |
| Missing/stale/over-budget capacity | DB-owned policy and snapshot; live pg_database_size recheck | Stop; obtain fresh evidence or explicit policy review |
| Duplicate/conflicting source | Stable filing keys; compare stored facts/periods | Identical retry returns receipt; conflict requires review |
| DB/network failure | Caller rolls back transaction; no automatic retry | Inspect outcome; retry same batch after reconciliation |
| Malicious source/unauthorized caller | Parameters, restricted grants, fixed function search path, forced RLS | Deny; no execution path from source content |
| Overestimated growth | Conservative gate stops a safe batch | Measure and review calibration; never self-increase budget |
| Underestimated growth/concurrent other writers | Bounded batches, reserve, serialized loader | Stop new imports; review capacity. Gate cannot guarantee provider billing |

## Evaluation cases

Python tests cover valid/null/zero, invalid/missing data, conflict, bounds,
parameterization, offline output and rollback on failures. SQL integration suite
covers missing/stale capacity, budget rejection, scope rejection, direct-write
denial, anonymous denial, successful import and idempotent retry. Pass requires
no unauthorized writes, no duplicates and retained provenance. SQL suite must
actually run before declaring RLS/database behavior verified.

## Unresolved risks and next step

Mark: source years, verified live mapping, snapshot scope evidence and measured
operating values. Agent: database integration/security tests, concurrency and
failure/recovery coverage. At preflight, the Docker engine was stopped and no
PostgreSQL client/driver was installed. Local implementation could proceed, but
database readiness was unverified.

Next non-operational step at preflight completion: implement and review the
offline slice. No external system or workflow was used during this preflight.

## Post-implementation evidence (separate from preflight)

After Mark started Docker for local verification, the migration, transactional
synthetic SQL suite, empty-schema down migration and reapplication passed in an
isolated PostgreSQL 16 container with networking disabled and tmpfs storage.
Supabase standard roles were simulated. See `TEST-MATRIX.md` for actual evidence
and outstanding concurrency, managed-platform and interrupted-COMMIT tests.
No cloud connection, credentials, real data or image download was used.
