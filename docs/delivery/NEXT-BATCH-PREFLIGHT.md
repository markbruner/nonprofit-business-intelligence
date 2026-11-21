# Next controlled batch and storage review — 2026-11-21

## Verified post-batch read-back

Owner returned diagnostic at 17:29:55.805315 UTC: 33 organizations, 33 filings,
2 runs, 33 links, LOGIN false. Latest run contains 30 rows, completed 17:28:57 UTC,
with database_bytes_before=11,548,339 and projected_bytes=559,808,876.
Current database=11,622,067 bytes; ingestion relations=352,256 bytes; WAL=83,886,444.
Both whole-database and relation-size interval deltas are 73,728 bytes (72 KiB),
averaging 2,457.6 bytes per added filing for this sample, including associated
scope/provenance and page allocation. This is not a reliable bulk growth rate.
Allocated WAL is unchanged; this does not mean the import generated no WAL.

Persisted policy read-back matches max_rows=30, stop=1,500,000,000,
reserve=268,435,456, max age=900 seconds, payload=65,536, multiplier=4 and
minimum growth=65,536 bytes/filing. The floor is about 26.7 times this sample's
observed average; retain it rather than reducing reserve or extrapolating capacity.
Current System/provisioned disk were not remeasured by this SQL. Future loads need
fresh full-capacity evidence and their own reviewed scope/payload. Neither trial
may be rerun; no next upload, policy widening or milestone advance authorized.

This read-back supersedes pending policy/storage-query statements below. Source
history coverage and authenticated repeatable Python loading remain unverified.

## Owner-reported thirty-record completion

Mark returned the presented trial's completion: 33 organizations, 33 filings,
2 import runs, 33 provenance links, LOGIN false, database_bytes_after=11,622,067.
No agent cloud connection occurred. No separate pre-execution approval message was
received; Mark manually executed and reported the result after the approval request.
Record this as owner-reported execution, not an invented prior approval.

This matches all expected totals and implies internal duplicate and role-restoration
assertions completed if the presented SQL was run unchanged. That transaction leaves
max_rows=30; an independent policy/storage read-back is next. Database change from
the previous observed 11,548,339 bytes is 73,728 bytes, an interval difference rather
than isolated batch growth. Need the second run's recorded baseline, current WAL,
relation sizes and provider metrics to calibrate. Neither first nor next trial may
be rerun. Further batches/login/milestone advancement remain unapproved.

Preparation and pending-execution statements below are historical for this batch.

## Post-import measurements and thirty-record SQL preparation

Mark returned the read-only diagnostic at 17:22:41.646147 UTC: database 11,548,339
bytes, WAL 83,886,444 bytes, ingestion tables/indexes 278,528 bytes, counts 3/3/1/3,
LOGIN false. Recorded first-run database baseline was 11,458,227 bytes: observed
whole-database difference 90,112 bytes, not a reliable per-filing growth rate.
Policy remains max_rows=3 with all other initial settings unchanged.

Disk panel observation at 17:23 UTC (12:23 Eastern): provisioned display 1.93 GB,
Database 25.72 MB, WAL 80 MB, System 167.54 MB, total 273.26 MB. The Database
category differs from current-database SQL size; its coverage is not assumed.
Capacity uses conservative 27 MiB Database-category and 169 MiB System bounds,
live WAL, and a 2,000,000,000-byte provisioned floor from the earlier 2 GB setting.
The 1.5-billion-byte stop is below either provisioned display interpretation.
Using reported WAL, projected usage including 256 MiB reserve and the 30-filing
growth floor is 559,808,876 bytes, below the unchanged 1.5-billion-byte stop.
Execution measures DB/WAL again and accounts for the larger of current SQL DB size
and the dashboard Database bound; System/category retain their actual timestamp.

`prepare_next_cloud_trial.py` regenerates the selection from verified local sources,
re-extracts the thirty candidates and original three, and compares original staging
before using its exact payload hash as the cloud baseline fingerprint. It reuses
the first-trial renderer for consistent policy/capacity/role controls. New SQL is
ignored and exclusive; no cloud connection. It checks counts 3/3/1/3, the original
run fingerprint and exact max_rows=3 policy; then changes only max_rows to 30 plus
approval metadata, updates capacity, adds the thirty-EIN scope, invokes the limited
loader twice and verifies final counts 33/33/2/33 and restored role assumptions.
Policy max_rows=30 persists on success; all other limits and LOGIN stay unchanged.
All transaction writes, policy/capacity changes and temporary grants roll back on
error. First-trial records are preserved; successful removal needs new approval.

Full Python suite now 62 passed. On isolated PostgreSQL 17.12 with an actual
non-superuser owner: first-trial regression, missing/stale/over-budget rollback,
thirty-row success/internal repeat, whole-script replay rejection, changed populated
baseline rejection, and role restoration passed. The post-import diagnostic also
ran successfully locally; its cloud execution is owner-reported above. Test container
removed after inspection. No new cloud execution occurred. Fresh observation expires
17:38 UTC; final SQL and the max_rows change still require Mark's explicit approval.

Earlier preparation notes below are retained as history and superseded by this
checkpoint where they describe pending measurements or an unprepared SQL artifact.

## Decision, authority and scope

READY FOR IMPLEMENTATION for local preparation and read-only SQL authoring only.
Mark requested commit/push, post-import storage review and larger batch preparation.
M01 DAT-003/005/007/008/011/012/013, partial; Ask for approval mode. Commit ca75e83
was pushed to the existing feature branch. Cloud writes are not approved here.

Reuse existing checksummed public state/index/January XML sources. Assume the three
trial records are the only cloud records; verify counts before a future transaction.
No new downloads, credentials, login, schema expansion, screening or mart release.

## Objective and success criteria

Stage thirty additional distinct organizations/filings, ten each OH/KY/IN, excluding
the original three EINs. Check deterministic selection, XML identity/period, tax
years, quality and provenance. Produce ignored local artifacts and a read-only
aggregate storage query. No new private data, real facts in fixtures or upload.

## Tools, data and minimum permissions

| Capability | Access, duration and purpose | Approval |
|---|---|---|
| Python preparation | Existing local sources; new ignored output for this task | Requested by Mark |
| Unit tests | Synthetic records in existing environment | Local preparation scope |
| Storage diagnostic | Author SQL; Mark runs read-only as existing dev owner | No new grants or agent connection |
| Future upload | None in this task | Separate exact SQL/payload and policy approval |

## Prohibited actions and human approval gates

Never widen policy, activate login, expand disks, retry an uncertain cloud commit,
silently replace failed candidates, upload raw archives or rerun the empty-target
trial. Never infer XML tax year from archive/index year. No credentials needed.

| Trigger | Approver and evidence | Scope / cancellation |
|---|---|---|
| Larger cloud batch/policy | Mark; fresh DB/WAL/System/provisioned readings, exact selected payload and tested SQL | Named dev project/batch; changes invalidate approval; cancel before Run |
| Credentials/connection activation | Mark; least-privilege and recovery proposal | Excluded from this preparation |
| Post-commit repair/deletion | Mark; read-only diagnosis and recovery proposal | No automatic reset or retry |

## Failure modes and recovery

| Failure / impact | Detection and containment | Recovery |
|---|---|---|
| Changed sources or trial selection | Reused checksum and deterministic selection checks | Stop and review locally |
| Invalid/conflicting identity or insufficient quota | Reject entire selection | No substitution with unapproved data |
| XML missing/mismatch/year/quality issue | Report needs_review; no load payload published | Preserve staging for review |
| Output exists or partial publication | New directory and exclusive writes | Inspect before choosing a fresh output |
| Stale or excessive storage | Existing DB gate; fresh measurements required | No automatic limit increase |
| Diagnostic privilege failure | Read-only error | Share error, do not add privileges |

Local rollback is reverting new source/docs and removing only task-owned ignored
output after review. Existing sources and cloud data stay intact. A future cloud
transaction needs its own rollback and uncertain-commit checks.

## Tests and actual evidence

| Case | Expected behavior and actual result |
|---|---|
| Prior EIN / multiple filings | Excluded / one latest indexed candidate per EIN; synthetic tests pass |
| Missing state, invalid ID/month, conflicting source ID | Reject selection; synthetic tests pass |
| Other form/archive | Cannot fill quota; synthetic tests pass |
| Real local preparation | 30 staged, 10/state; 9 tax-2025 and 21 tax-2024; no index/year/quality findings |

Initial Python suite: 59 passed. Payload is 20,121 compact UTF-8 bytes. Existing growth
floor gives 1,966,080 bytes for thirty filings; DB also applies its payload multiplier
to JSONB text. This is admission planning, not measured growth or a billing guarantee.
No downloads or DB contact occurred. Post-import SQL has not yet run in Supabase.

## Unresolved risks and next safest step

Mark supplies the diagnostic result plus Disk panel System/provisioned readings and
actual metric timestamp. Whole-DB size changes include unrelated activity; absolute
table/index sizes include initial allocation. No pre/post relation baseline exists
for the first trial. The January sample has no 2023 filings and is not history coverage.

Cloud policy still allows only three rows per batch. After storage review, propose
an exact thirty-row policy change and populated-target execution transaction, leaving
stop/reserve/freshness/payload/growth unchanged unless separately justified. Do not
delete first-trial guards to reuse it. No larger execution SQL, upload or milestone
advance is approved. This report records the read-only preflight completed before
implementation and subsequent local evidence.
