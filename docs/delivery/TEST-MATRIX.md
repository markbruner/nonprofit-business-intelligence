# Requirement-to-test matrix

This is a **test plan**, not a claim that tests have been written or passed. Add actual test paths and results as code is created.

| Milestone | Requirements | Minimal verification | Status |
|---|---|---|---|
| M01 | DAT-002–DAT-005, DAT-007–DAT-008 | Idempotent import; EIN alias/collision; source tax periods; amendment selection; missing-vs-zero handling | NOT RUN |
| M01 | DAT-001, DAT-006, DAT-009–DAT-011 | Source metadata, manual import validation, county config, geocoding provenance, failed-run integrity | NOT RUN |
| M01 | DAT-012 | Below-budget batch proceeds; threshold-crossing batch stops before writes; missing/stale capacity fails closed; rerun adds no duplicates; measurements include indexes and overhead; actual usage and provisioned disk reported separately; no automatic disk expansion | PARTIAL: synthetic SQL gate tests pass; real calibration/provider behavior unverified |
| M01 | DAT-013 | Versioned OH/KY/IN source snapshots define EIN candidates; out-of-scope EIN rejected; no full-990 filing does not remove organization from registry | NOT RUN |
| M01 | SCR-001–SCR-005 | Revenue band, surplus, margin guard, trend gaps, mission corrections | NOT RUN |
| M01 | SCR-006–SCR-010 | Versioned deterministic rules, reason codes, override audit, no pipeline contamination | NOT RUN |
| M02 | SEC-001–SEC-007, SEC-009, SEC-011 | Signed-out/manager/admin/inactive DB+API authorization and secret exposure tests | NOT RUN |
| M02 | RES-001–RES-009 | Profile fields and source citations; manual observed/inferred/confirmed; no fabricated grants/outcomes | NOT RUN |
| M02 | UX-001, UX-003–UX-011, ARC-007–ARC-008 | Table/map/summary same filters/counts, unmappable records, empty/errors, keyboard/mobile tests | NOT RUN |
| M03 | CRM-001–CRM-004 | Multiple contacts, relationship without opportunity, dated interactions | NOT RUN |
| M03 | CRM-005–CRM-006 | Due/overdue tasks by assignee and timezone, overview actions | NOT RUN |
| M03 | CRM-007–CRM-012 | Two opportunities per org, independent stages, stage audit and manager permissions | NOT RUN |
| M03 | UX-002, SEC-002–SEC-004, SEC-014 | Dashboard real data; manager capabilities vs admin restrictions | NOT RUN |
| M04 | PIL-001–PIL-009, ARC-009–ARC-011, SEC-012 | Pilot metrics, reproducible baseline, security/account audit, recovery review | NOT RUN |
| Possible M05 | AIR-001–AIR-010 | Public source constraints, bounded costs, review workflow, factual error audit | DEFERRED |

## Report actual execution per task

### 2026-11-21 — second trial post-import policy/storage read-back

- Owner-supplied diagnostic at 17:29:55 UTC confirms 33/33/2/33, LOGIN false,
  latest row_count=30 and persisted max_rows=30; all returned remaining policy
  settings unchanged. DB 11,622,067, WAL 83,886,444, ingest relations 352,256 bytes.
- Latest run baseline 11,548,339; DB delta 73,728 bytes. Prior relation baseline
  278,528; relation delta also 73,728. This includes scope/provenance/page allocation
  and is small-sample evidence only. Stable allocated WAL does not measure WAL produced.
- Partial hosted DAT-005/011/012 evidence. No new code/test execution in this
  documentation-only checkpoint; no future load authorized. System/disk panel
  freshness, history coverage and authenticated Python transport remain separate.

### 2026-11-21 — owner-reported next thirty cloud completion

- Returned complete: organizations=33, filings=33, import_runs=2,
  provenance_links=33, login_enabled=false, database_bytes_after=11,622,067.
- Counts match the presented script's assertions and internal duplicate check;
  owner-reported evidence, no independent agent cloud connection. No separate
  pre-execution approval message was received; user manually ran and reported it.
- Difference from preceding DB observation is 73,728 bytes; this is not a precise
  batch-only estimate. Current WAL/relation sizes/second-run baseline and persisted
  max_rows=30 policy read-back remain pending. Do not rerun either trial script.

### 2026-11-21 — post-import review and next cloud SQL preparation

- Owner-reported diagnostic: 11,548,339 DB bytes / 83,886,444 WAL bytes / 278,528
  ingestion relation bytes; original baseline 11,458,227, delta 90,112; counts 3/3/1/3,
  LOGIN false and initial policy unchanged. System/Database category evidence
  timestamp 17:23 UTC. Larger dashboard Database bound is included conservatively.
- Full Python suite 62 passed. Added continuation tests for population fingerprint,
  exact quotas/exclusions/year boundaries, policy preview, and larger provider DB
  category accounting. Existing first-trial tests still pass.
- Actual non-superuser PostgreSQL 17.12 sessions: first trial succeeds; next missing,
  stale and over-budget cases reject without new records or max_rows changes; next
  success yields 33 organizations/33 filings/2 runs/33 links, LOGIN false; internal
  repeat adds no duplicates. Whole-script replay and changed-baseline cases reject;
  owner SET/INHERIT false verified. Read-only storage diagnostic executes locally.
- Container inspected/removed; final real-data SQL generated locally after source
  revalidation. No larger cloud execution or policy change approved/executed.

### 2026-11-21 — next thirty local preparation

- Five new synthetic selection tests pass; full Python suite 59 passed. Covers
  exclusions, latest-per-EIN selection, state quotas, malformed/conflicting index
  identities and form/archive boundaries. Reuses tested snapshot/ZIP validators.
- Actual local preparation: 30 selected/staged, ten/state, 9 tax-2025 / 21 tax-2024;
  zero index/year/quality findings, payload 20,121 compact bytes. No network or DB.
- Added read-only post-import diagnostic; hosted SQL execution and actual storage
  interpretation pending owner result. No larger upload or policy change tested.

### 2026-11-21 — owner-run first cloud import

- Explicit approval preceded manual SQL Editor execution of the generated trial.
  Owner returned complete, organizations=3, filings=3, import_runs=1,
  provenance_links=3, login_enabled=false, database_bytes_after=11,548,339.
- Completion implies generated internal repeat/count/role-restoration assertions
  passed. This is owner-supplied evidence, not an independent agent connection.
- Partial DAT-005/011/012 and restricted SQL-path evidence only. Final database
  size is not total disk usage or a measured before/after growth calibration.
  Authenticated Python transport and representative scale remain unverified.

### 2026-11-21 — three-record SQL trial preparation (no cloud execution)

- Owner's policy read-back matches every approved value, approved_at 14:42:52 UTC;
  this is a policy-only checkpoint, not capacity/scope/first-load authorization.
- `prepare_cloud_trial.py` and five synthetic unit tests added. Full Python suite:
  PASS, 54 tests. Black API formatting/check and whitespace check: PASS.
- On isolated PostgreSQL 17.12, actual non-superuser nbi_trial_owner sessions ran
  generated SQL. Missing/stale/over-budget cases failed as expected with scope,
  capacity and run counts 0 and owner SET/INHERIT false after rollback.
- First over-budget attempt found a test-fixture WAL grant in the wrong database;
  corrected grant in the synthetic test DB and reran all guards successfully.
- Success: 3 synthetic organizations / 3 filings / 1 run / 3 provenance links,
  login false, internal repeat receipt identical, role restoration verified.
  Whole-script replay stopped at nonempty-target guard with no extra rows/grants.
- Real-data review artifact generated offline, after re-extracting/checking the
  original local archive: 3 filings, 2,180-byte JSON payload, no capacity evidence
  supplied, no database contacted. Output is ignored and deliberately non-executable
  until fresh inputs. No actual record values were copied into code/tests/chat.
- This does not verify hosted execution, live authentication or Python transport.
  Test container removed after inspection; only synthetic ephemeral data discarded.

### 2026-11-21 — initial storage-policy proposal validation

- Owner supplied DB=11,409,075 bytes and WAL=83,886,444 bytes at 14:31:47 UTC;
  System=167 MB with timestamp 1795271293373000 (interpreted as Unix microseconds,
  14:28:13.373 UTC); provisioned=2 GB. Planning uses conservative unit/rounding
  bounds, not fabricated precision. No capacity row was seeded from these readings.
- Exact `setup/storage_policy.sql` and read-back query: PASS locally on PostgreSQL
  17.12 after existing migration/disabled-role setup. Verified policy values;
  capacity/approved-EIN/filing rows remain 0 and LOGIN remains false. Synthetic
  isolated container only, no cloud execution. Container removed afterward.
- Proposed values are NOT YET APPROVED: 1.5 GB stop, 256 MiB reserve, max age
  900 seconds, 3 rows / 64 KiB payload, growth max(4x payload, 64 KiB/row), tax
  years 2023–2025. Current readings will need refresh before the first data load.

### 2026-11-21 — disabled cloud loader and local storage calibration

- Mark's loader-role metadata matches expected values: NOLOGIN and no admin/bypass
  attributes; connection limit 1; CONNECT, inherited ingestion and function access
  true; SET/executor/direct-insert/budget-update access false. No live login tested.
- `supabase/tests/storage_calibration.sql` ran on isolated local PostgreSQL 17.12
  through the current guarded function: PASS, 1,000 synthetic organizations,
  3,000 synthetic filings, 12 batches, 3,000 provenance links. All rows rolled back.
- Table/index/schema growth: 4,505,600 bytes; database growth: 4,513,792 bytes;
  amortized schema growth: 1,501.87 bytes per filing in this fixture. This includes
  registry, allowlist, run and provenance overhead at this test ratio, not future
  organization fields, every source shape, managed WAL/System or provider billing.
- Largest synthetic admitted-batch estimate: 16,384,000 bytes for 250 rows. Its
  operational fixture values are NOT approved cloud defaults. No cloud settings
  or records were changed. Temporary container removed after measurement.
- Fresh cloud DB/WAL and provider System/provisioned evidence are still needed.
  Daily-updated dashboard metrics must not be relabeled as fresh measurements.

### 2026-11-21 — owner-run cloud schema verification

- Mark manually applied the approved schema-only migration, then supplied the
  `schema_verification.sql` result. PASS (reported metadata): table/RLS/forced-RLS
  counts 7/7/7; locked non-login roles 2; loader function execution and hardening
  true; anonymous/authenticated/service-role execute, direct loader inserts and
  budget updates false. No agent browser action or database connection was used.
- This does not verify live authentication, app authorization, managed API calls,
  cloud import behavior or capacity calibration. Loader setup/activation, policy
  seeding and data uploads remain unapproved. Manual SQL application has not
  reconciled CLI migration history; review before any future db push.

### 2026-11-21 — cloud-version readiness check

- Mark's read-only cloud metadata reports PostgreSQL 17.12 and database bytes
  11,114,163. This is database usage only, not total provisioned/WAL/system disk.
  No operational capacity policy was seeded from that reading.
- Official `postgres:17` image downloaded with approval; actual local server
  reports 17.12 (Debian 17.12-1.pgdg13+1). Migration under non-superuser CREATEROLE
  database owner: PASS. Existing synthetic SQL suite: PASS. Disabled-loader setup
  and empty-schema down migration under that owner: PASS. No code changes needed.
- Networking disabled, tmpfs data; standard Supabase role names simulated. Hosted
  managed-role behavior remains unverified. Temporary container removed afterward.
- `supabase/diagnostics/migration_preflight.sql` is a read-only cloud metadata
  check for role capabilities and pipeline-name collisions. Cloud results pending;
  no migration/role creation/upload approval is inferred from metadata sharing.

### 2026-11-21 — selected-member local XML validation

- Full Python suite: PASS, 49 tests. New tests verify selection before XML size/
  parse checks, missing/unsafe selection, fixed archive-budget forwarding,
  snapshot checksums, no overwrite and review marking on index mismatch.
- Sample runner tests initially hit Windows sandbox hard-link restrictions;
  escalated rerun passed. Changed to Windows exclusive rename (same as extractor)
  with POSIX hard-link publication; ordinary full suite then passed.
- Black API format/check for six changed Python files: PASS. Whitespace: PASS
  (line-ending warning only).
- `./.venv/Scripts/python.exe -B -m scripts.validate_xml_sample data/irs-source-sample-20261121-01 data/irs-xml-sample-20261121-01`:
  PASS, exit 0; 71,497,607 bytes, 3 staged, 3 index identity/period checks passed,
  no quality findings, 12,242 members skipped. Tax years: 2024 (1), 2025 (2).
- Direct source-to-staging field reconciliation: PASS, 15 checks. Actual schema
  variants observed: 2024v5.0 (1), 2025v4.0 (2). No sample identities/amounts in
  tests, chat or tracked artifacts. All source/staging artifacts remain ignored.
- Approval covered this local sample only. No database connection, credentials,
  Supabase write, cloud capacity calibration or full historical coverage claim.

### 2026-11-21 — approved bounded four-CSV source sample

- Eight new synthetic bounds tests: PASS; all 28 downloader tests: PASS before run.
  Full Python suite after run: PASS, 43 tests. Black API format/check: PASS for
  downloader and its tests; `git diff --check`: PASS (line-ending warning only).
- `./.venv/Scripts/python.exe -B -m scripts.download_irs --source-sample data/irs-source-sample-20261121-01`:
  PASS, exit 0, 89,863,197 payload bytes under the 175,000,000-byte budget.
  No retries, redirects, compressed payloads, XML archives, credentials or cloud access.
- Verified actual EO/index CSV headers and streamed aggregate EIN/state/index
  checks. 145,632 candidate EINs; 516,019 index rows; 17,177 matched full-990 rows
  for 16,605 EINs. No invalid checked row shapes. See IRS_SOURCE_CONTRACT.md for
  source limitations and exact byte counts. Real rows never copied into tests/logs.
- Response-budget tests cover exact declared boundaries, unknown-length boundary
  rejection without over-read, shared partial-byte accounting, header rejection,
  no retry/overwrite, validation failure and partial manifests.
- The preflight drove explicit fixed-source/cap/no-retry controls. Recovery is
  task-owned partial cleanup; earlier completed snapshots are preserved. Raw
  snapshots/manifests remain Git-ignored. This is partial M01 evidence only.

### 2026-11-21 — offline loader and local database verification

- Source verification follow-up: two official documentation schema ZIPs inspected
  in memory (2023v5.1 and 2024v5.0; under 300 KB each). Corrected amendment field
  location (IRS990 body) and checkbox value X. Parser contract bumped to v2;
  old v1 staging is rejected by the loader/SQL contract. Full Python suite: PASS,
  35 tests, including a new schema-shaped amendment test. Black API check: PASS
  for the four parser/loader files; whitespace check: PASS.
- Non-superuser migration-owner test initially FAILED at ownership transfer;
  a subsequent draft exposed ineffective grant ordering. Corrected temporary
  SET permission and ACL ordering. Final migration, SQL suite with explicit ACL
  assertions, and empty-schema rollback: PASS under a non-superuser CREATEROLE
  database owner on PostgreSQL 16.
- `setup/loader_role.sql` applied locally as that owner: disabled identity can
  execute loader, cannot insert directly or update budget, has no executor
  membership and no LOGIN/superuser/CREATEROLE/CREATEDB/replication/BYPASSRLS.
  Owner's final executor membership has SET=false and INHERIT=false.
- HTTP HEAD checks only: three state CSV and four annual index URLs returned 200;
  contents remain unverified. See `IRS_SOURCE_CONTRACT.md` for bounded proposed
  sampling and outstanding 2025 mapping evidence. No nonprofit datasets/XML
  archives downloaded, Supabase connections or credentials used.

- Follow-up after Mark selected XML tax years 2023–2025: migration and SQL suite
  rerun PASS in a fresh isolated PostgreSQL 16 container, including rejection of
  unknown and out-of-policy tax years. No operational policy was seeded in the
  migration; owner configuration must set the approved years before live use.

- `./.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_load_supabase.py -v`: PASS, 8 tests.
- Covers input/provenance/bounds validation, null/zero, deterministic payload,
  parameterized injected-connection call, commit/rollback behavior with mocks,
  and offline CLI output. Mocked database errors do NOT verify actual SQL gates.
- Full `./.venv/Scripts/python.exe -B -m unittest discover -s tests -v`: initially
  FAILED (20 downloader errors due to old mock targets after an existing module
  rename). Updated four mock targets only; rerun PASS, 34 tests. Downloader
  implementation unchanged. API/contract suite: PASS, 8 tests.
- Black CLI hung and was stopped; Black Python API formatted and then checked
  `scripts/load_supabase.py` and `tests/test_load_supabase.py`: PASS.
- `git diff --check`: PASS.
- SQL migration: PASS on isolated local PostgreSQL 16 (`postgis/postgis:16-3.7`).
  `docker exec nbi-loader-test-20261121 psql -U postgres -v ON_ERROR_STOP=1 -f /tmp/nbi-tests.sql`:
  PASS for `supabase/tests/990_loader.sql`, including storage threshold equality,
  missing/stale/future/mismatched/over-allowance measurements, scope rejection,
  direct-write and unauthorized-role denial, valid import/retry, cross-run conflict,
  late-write failure rollback, recovery and provenance. All test changes rolled back.
- Down migration on the empty synthetic schema and up-migration reapplication:
  PASS. Docker had networking disabled and tmpfs-only database storage; standard
  Supabase role names were simulated, not a full Supabase stack. No credentials,
  external data, downloads or Supabase connections used. Container removed afterward.
- Schema revised to internal organization IDs and authoritative typed financial
  facts with an integrity hash instead of duplicate JSON facts. Reporting mart,
  live source reconciliation, scope generation, capacity calibration, concurrency
  and interrupted-COMMIT tests remain outstanding. See `supabase/README.md`.
  This is partial technical evidence, not an M01 technical or business gate pass.

### 2026-11-17 — local Form 990 XML extractor

- Partial coverage for DAT-003, DAT-005, DAT-007, DAT-008, and DAT-011.
- `./.venv/Scripts/python.exe -B -m unittest discover -s tests -v` passed
  26 tests, including six extractor cases. Synthetic ZIPs verified the
  mapping, zero and null, repeatable keys, conflicting observations,
  malformed and unsupported records, member size limits, manifest integrity,
  and safe CLI publication.
- Black passed separately for the extractor and its test file.
- Live IRS reconciliation and database idempotency remain unverified.

### 2026-11-17 — Form 990 downloader improvements

- Partial coverage for DAT-006, DAT-007, and DAT-011.
- `./.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_data_extract.py -v`
  passed 20 tests, including five new Form 990 cases. Mocked HTTP covers
  invalid plans and collisions, duplicate requests, distinct year paths,
  index and ZIP validation, preservation of prior files, and partial-run
  manifest metadata.
- Live source compatibility, filing validation, and importer idempotency
  remain unverified. This evidence is for the downloader only.

### 2026-11-15 — approved local IRS downloader slice

- Test path: `tests/test_data_extract.py` (15 tests).
- Requirements: partial DAT-001, DAT-006, DAT-007, DAT-011; supports ARC-004/005/009.
- Input: in-memory synthetic CSV bytes; mocked HTTP and retry waits. No live
  source downloads or Supabase access.
- Expected: correct per-state URL/file selection, all-input validation before
  HTTP, returned URL/path/UTC time/byte count/hash, bounded retries, no partial
  publication, preserved existing files on failure, explicit partial-batch errors.
- Actual: **PASS — 15/15**; additionally **PASS — 8/8** existing API/IRS contract
  tests. Formatting: **PASS**, both changed Python files unchanged by Black check.
- Environment: existing repository `.venv`, Windows; interpreter access required
  sandbox escalation. No dependency installation or environment repair.
- Commands executed from repository root:

  ```powershell
  ./.venv/Scripts/python.exe -m unittest discover -s tests -p test_data_extract.py -v
  ./.venv/Scripts/python.exe -m unittest discover -s services/api/tests -v
  ./.venv/Scripts/python.exe -m black --check scripts/data_extract.py tests/test_data_extract.py
  git diff --check
  ```

- Limits: no live compatibility/schema test, persistent import log, source-version
  verification, parser, database idempotency, geographic filtering, or Supabase
  loader. Existing M01 matrix rows remain NOT RUN for their complete requirements;
  this narrow task does not pass either milestone gate.

- Test ID or path:
- Requirement ID(s):
- Input fixtures/source reference:
- Expected result:
- Actual result:
- Run command and environment:
- Status (PASS / FAIL / BLOCKED):
- Known limitations:

Do not claim an end-to-end release is verified merely because one unit test passes.
