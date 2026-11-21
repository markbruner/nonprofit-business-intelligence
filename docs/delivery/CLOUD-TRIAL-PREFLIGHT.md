# First three-record cloud trial — review and local evidence

## Execution checkpoint — 2026-11-21

The preparation assessment below is historical. Mark supplied System=167.53 MB
at 17:15 UTC, explicitly approved the final three-record SQL, and manually ran it
in the named development project. Returned result: complete; 3 organizations,
3 filings, 1 import run, 3 provenance links; LOGIN false; database size 11,548,339
bytes. Internal repeat and role-restoration assertions completed. No agent cloud
connection occurred. This approval is consumed for this trial; future batches,
login activation and milestone release remain separate decisions. Do not rerun.

## Decision

READY FOR IMPLEMENTATION for offline preparation/testing only. Cloud execution
is NOT approved: it requires fresh System evidence and Mark's explicit approval
of the generated three-record transaction. No secrets or agent cloud connection
are needed; Mark will use his existing SQL Editor session if he approves it.

## Scope, objective and success

M01 DAT-003/005/007/011/012/013 and SEC-003/006, partial. Inputs are the three
approved local IRS sample filings, rechecked against their checksummed archive,
local index selection and loader contract. This is a functional trial, not
historical completeness, screening or mart release.

Success: three organizations, three filings, one import run, three provenance
links after calling the guarded import twice; login stays disabled and owner
role-assumption permissions are restored. No raw archive, state CSV, names,
addresses or unrelated filings are uploaded.

## Tools, data and minimum permissions

| Capability | Access / duration | Justification / approval |
|---|---|---|
| Preparation | Existing local sample; Python; ignored SQL output | Mark authorized continuation/preparation |
| Testing | Isolated PostgreSQL 17.12, no network, synthetic rows | Local-test approval |
| Owner SQL | Existing session in named dev project; one transaction | Scope/capacity seed and temporary role assumption; trial approval pending |
| Loader context | Temporary SET to existing nb_loader_dev; function only | Test restricted role without authentication |
| Credentials | None read/generated; no LOGIN activation | Unnecessary for this trial |

The SQL artifact contains public EIN/financial/provenance data. SQL Editor may
retain query text; approval must cover that destination as well as database rows.
Do not paste the review template into Supabase before approval.

## Prohibited actions

No credentials, browser automation, new downloads, scheduling, bulk imports,
production changes, disk expansion, public API exposure or silent policy widening.
No client/donor/employee/private records. Source text stays inside collision-safe
dollar-quoted JSON, never executable SQL. Real-data SQL stays Git-ignored; only
synthetic fixtures enter tests. Never blindly rerun a successful whole trial.

## Human approval gates

| Trigger | Approver and evidence | Scope / expiry / cancellation |
|---|---|---|
| First cloud transaction | Mark; exact local SQL/payload, fixed dev reference, policy and tests | Named trial; expires on payload/target/policy/action change; cancel before Run |
| Fresh System evidence | Mark supplies actual metric timestamp and usage | Max age 15 minutes; never retimestamp old observations |
| Recovery after COMMIT | Mark; verified rows/run and recovery plan | No automatic delete/reset/down migration |

## Controls, failures and recovery

SQL checks the approved policy, disabled restricted role, owner ADMIN membership
with SET/INHERIT initially false, and empty target. It adds exactly three approved
EINs. Live SQL measures DB/WAL; System contributes a conservative upper bound and
its original timestamp. Missing/stale/future evidence stops execution. Provisioned
capacity is conservatively bounded at 2 billion bytes; no expansion is requested.

One transaction grants temporary SET, assumes nb_loader_dev, calls the import
twice, restores the owner, disables SET/INHERIT and asserts counts/restoration
before COMMIT. Errors roll back scope/capacity/records/grants. After an uncertain
COMMIT, inspect read-only before retrying. Successful-data removal needs approval.

## Evaluation evidence

- Five Python tests pass: review blocking, timestamp/units, selection/year
  validation, delimiter collisions and exclusive output. Full suite: 54 passed.
- PostgreSQL 17.12 tests used an actual non-superuser CREATEROLE/BYPASSRLS owner
  session, not merely SET ROLE from a superuser session.
- Missing/stale/over-budget evidence: expected errors, zero new rows and no owner
  elevation. First over-budget attempt hit a fixture WAL grant in the wrong DB;
  corrected local fixture and reran successfully.
- Success: 3 organizations / 3 filings / 1 run / 3 links, login false. Internal
  repeat is duplicate-free. Whole-script rerun rejects a nonempty target without
  new rows/elevation. No cloud test executed.

## Unresolved risks and next safest step

Fresh System evidence and first-data approval are pending. Cloud behavior may
differ; guards stop on unexpected state. No live login, Python network transport,
concurrent-writer, complete-history or billing guarantee is claimed. The reserve
is an estimate. Current review SQL deliberately has NULL capacity inputs.

Next non-operational step: Mark reviews the artifact and provides current System
usage/timestamp before a final execution copy and approval.
