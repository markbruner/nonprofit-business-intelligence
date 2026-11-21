# Scripts

Place repeatable local development and data-maintenance scripts here. Document inputs, side effects, and safety.

## Restricted connection setup (operator-run)

Follow `../docs/tasks/loader-connection-setup.md`: download the public project CA,
run `set_loader_password.ps1` in your own interactive terminal, review/apply the
guarded one-hour LOGIN script, then run `python -m scripts.check_loader_connection
--ca-cert ./data/connection/supabase-ca.crt`. Commands accept no password argument,
environment variable or secret file. The helper uses cached PostgreSQL 17 psql's
hidden password commands; the probe pins the dev pooler/role with verify-full,
read-only metadata and no import. Driver is optional: `uv sync --extra loader`.
Never run the password prompt through agent tools; share only sanitized output.

## Repeatable 2023 pipeline preparation

```powershell
./.venv/Scripts/python.exe -m scripts.run_irs_pipeline data/irs-source-sample-20261121-01 data/irs-xml-sample-20261121-01 data/NEW-pipeline-package
```

One local command reuses source/coverage validators, preserves discovery evidence,
selects actual tax-2023 records, and writes reviewed batches under the current
30-record / 64 KiB limits. It never downloads or connects. Stable sorted payloads
preserve database idempotency; each plan also binds its particular evidence files.
The plan is written last; inspect partial outputs before trying a new directory.
Real records/packages stay Git-ignored. Preparation failure prints only error type.

`execute_prepared(connection, package, batch_id, expected_plan_sha256=...)` is a
Python API for a future approved caller, not a live CLI command. Pass an explicitly
reviewed plan digest and idle non-autocommit restricted connection. It checks all
artifact hashes before calling existing `load_batch`; the DB checks scope/policy/
fresh capacity. One selected batch per call, no automatic retry. A connection loss
may leave a committed run; inspect server state before any explicit resubmission.
No driver/credential setup or LOGIN activation is implemented by this runner.
See `../docs/delivery/PIPELINE-RUNNER-PREFLIGHT.md` for limits and recovery.

## Check tax-2023 sample coverage locally

```powershell
./.venv/Scripts/python.exe -m scripts.check_2023_coverage data/irs-source-sample-20261121-01 data/irs-xml-sample-20261121-01 data/NEW-tax2023-check
```

No downloads or DB connection. Reuses checksummed sources and selects at most 500
regional candidates in the existing January archive with period ends in 2023/2024.
Coverage uses actual XML TaxYr, never publication/end year. Seven direct-path
checks per tax-2023 record supplement index reconciliation. Writes only a new ignored
selection/staging/aggregate-report directory; preserves findings and missing data.
Exit 0 means samples in all three states passed, 2 means review required, 1 means
failure. No upload is authorized or historical completeness claimed. Partial output
must be reviewed before retrying in a new directory. Roll back only task-owned
code/output if requested; source snapshots and cloud data are untouched.

## Prepare the next local batch

`prepare_next_cloud_trial.py` revalidates the same sources and creates populated-
target SQL for the exact next thirty. Use module invocation with source, original
sample and NEW ignored output SQL, `--system-timestamp-us`, `--system-mb` and
`--database-mb` from the same Disk panel observation. Missing System evidence makes
a blocked review template. Database-category bound accounts for the difference
from SQL current-database size. Never retimestamp old evidence. The generated
transaction proposes max_rows=30, preserving other limits; it is NOT authorized
to run without explicit batch/policy approval. No credentials or DB connection.

```powershell
./.venv/Scripts/python.exe -m scripts.prepare_next_batch data/irs-source-sample-20261121-01 data/irs-xml-sample-20261121-01 data/NEW-next-batch
```

Uses existing checksummed sources only; no downloads or credentials. Selects ten
new EINs per state from the January archive, excludes original trial EINs, validates
index/XML identity/period and XML tax years 2023–2025. Writes exclusive ignored
selection/staging/report files; a load payload is emitted only on full validation.
Exit 0 means complete, 2 means review required, 1 means failure. Inspect partial
outputs before retrying in a new directory. Logs contain aggregate fields only.
This does not query existing cloud records or authorize any import/policy change.
See `../docs/delivery/NEXT-BATCH-PREFLIGHT.md` for evidence, gates and recovery.

## Offline loader draft (`load_supabase.py`)

### First cloud trial review preparation

`prepare_cloud_trial.py` generates local SQL only; it has no database/network or
credential access. It checks the local archive against staging/selection and
uses collision-safe dollar quoting. Real-data output is restricted to ignored
repo `data/`, exclusively/atomically published, never overwritten.

```powershell
./.venv/Scripts/python.exe -B -m scripts.prepare_cloud_trial data/irs-xml-sample-20261121-01 data/irs-xml-sample-20261121-01/NEW-review.sql
```

Without `--system-timestamp-us` and `--system-mb`, output is a blocked review
template. Those arguments accept the metric's actual Unix-microsecond timestamp
and displayed MB value, using a conservative binary upper bound plus rounding.
Supplying them does NOT grant execution approval. Refresh stale data, obtain
named trial approval, then run the complete reviewed transaction manually.
No LOGIN activation is needed; temporary owner SET permission is restored.
The SQL Editor may retain its public IRS payload. Never add the output to Git.

Validates bounded full-990 staging output without opening a database connection:

```powershell
./.venv/Scripts/python.exe -B -m scripts.load_supabase data/synthetic/filings.json --scope-version synthetic-v1
./.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_load_supabase.py -v
```

`prepare_batch` rejects review findings, unsupported/malformed/missing fields,
duplicate/conflicting rows and oversized batches. `load_batch` accepts a caller-owned
idle DB-API connection, invokes one parameterized function, commits a completed
receipt or rolls back errors, and never retries automatically. It creates no
connection and reads no credentials. The CLI only reports offline validation
counts, not row data. SQL, scope and capacity configuration are described in
`../supabase/README.md`. The SQL migration is ON HOLD for design review, not ready
to apply. No driver, credentials or automatic pipeline runner are configured.

## IRS downloader (`download_irs.py`)

### Local selected-member XML validation

`validate_xml_sample.py` is a small explicit-run wrapper around the existing
downloader, extractor and offline loader validator. It verifies the completed
CSV snapshot checksums, selects one full-990 candidate per state in the fixed
January batch, downloads that one archive, and parses ONLY selected filing IDs.
Use only with named source-collection approval:

```powershell
./.venv/Scripts/python.exe -B -m scripts.validate_xml_sample data/APPROVED-csv-snapshot data/NEW-approved-xml-snapshot
```

It writes ignored local selection/staging/provenance plus an aggregate validation
report, never a database connection. Mismatched index identity/period or out-of-scope
tax year marks staging for review. Other archive members are skipped before reads.
The operational 80 MB transfer cap is unrelated to Supabase storage. Existing
snapshot/output paths are never overwritten. Windows uses exclusive rename for
atomic publication; POSIX uses an exclusive hard link. Failed runs require review
before a new snapshot/retry. No raw identities or amounts are printed by the runner.

The extractor also accepts `selected_filing_ids` as a set (1–500 safe IDs), or
`--selection` pointing to an ignored local JSON array of IDs. Missing requested
members produce review findings; there is no fallback to parsing the full archive.
The XML downloader wrapper now accepts per-file caps, max attempts and a shared
budget, recording these operational controls in its existing manifest.

M01 local downloader slice, approved by Mark on 2026-11-15. Importing the module
does no I/O. Real IRS collection still requires the source/scope decisions in
`docs/delivery/DECISIONS.md` (O-01/O-02); this task used synthetic HTTP responses
only. A fixed-scope sample CLI was subsequently approved below; there is no
scheduled refresh or Supabase connection.

Functions:

### Bounded source sample (one-time approval required)

```powershell
./.venv/Scripts/python.exe -B -m scripts.download_irs --source-sample data/NEW-approved-snapshot
```

Fixed plan: OH/KY/IN EO CSVs (25 MB each), 2026 publication index (100 MB),
175 MB shared response-payload budget. No retries, redirects or compression.
Requires a NEW snapshot path and validates headers before publishing each file.
Reports only aggregate counts, saves source/hash/time/size/header provenance, and
marks partial failures explicitly. Existing snapshots are not replaced. Failed
file partials are removed; completed files remain. Unknown-length bodies at the
exact cap are rejected without an additional read. No XML or cloud actions.

`download_file` now accepts optional `max_bytes`, `max_attempts` (1–3) and a shared
`DownloadBudget`. Legacy callers retain three attempts and their original streaming
behavior. The bounded path counts actual identity payload bytes across failed
files/attempts; HTTP/TLS overhead is excluded. Source sample uses one attempt only.
Source collection approval applies to a named run, not arbitrary future CLI runs.
The completed approved snapshot and evidence are in the source contract/test matrix.

The former `download_eo_state_file(url, states_list, local_filename)` interface
is replaced by the functions below. Callers should use
`download_eo_files(states, output_dir)` and read paths from the returned results.

- `build_eo_url(state)` accepts a state name or two-letter abbreviation, ignoring
  case, surrounding whitespace, and spaces versus hyphens in names. Supported
  scope is the existing 50-state and DC mapping; territories are not included.
- `download_file(url, destination)` downloads one file and returns a
  `DownloadResult` with source URL, local path, UTC completion timestamp, byte
  count, and SHA-256 checksum. Call only with an approved public source URL and
  a local destination you are authorized to write.
- `download_eo_files(states, output_dir)` validates every state before doing I/O,
  deduplicates state aliases, and downloads sequentially to `eo_<code>.csv`.
  Empty input returns an empty list without creating a directory. The first
  failure raises its original exception with a batch-progress note; earlier
  completed files remain and later states are not attempted.

Downloads create parent directories and temporary `.part` files beside the
destination. A nonempty completed file atomically replaces the destination;
failed attempts clean up their temporary file and preserve the existing file.
Use a separate dated output directory when retaining historical snapshots.
A process crash can leave a `.part` file, which must not be ingested; abrupt
shutdown/power-loss durability and concurrent writers are outside this slice.

Each download permits at most three attempts. HTTP 429/500/502/503/504,
connection errors, timeouts, and interrupted chunked responses are retried with
0.5-second and 1-second waits. Other HTTP errors, empty responses, and local I/O
errors fail immediately. Connect/read inactivity timeouts are 10/60 seconds;
there is no overall deadline or resume support. Retry-After is not interpreted.

The EO BMF wrapper checks HTTP status and nonempty content and returns metadata
in memory. Its parser still needs to validate headers and preserve EIN, ZIP,
and missing values.

### Form 990 indexes and XML archives

- `download_series_990_index(years, output_dir)` takes four-digit integer
  publication years. `download_series_990_xml(batches, output_dir)` takes
  `(year, archive_basename)` pairs with the `.zip` suffix omitted. These years
  belong to the source URL and do not establish an organization's tax period.
- The full plan is checked before downloads. Exact duplicates are skipped,
  empty input does no I/O, and colliding paths are rejected. Use a distinct
  snapshot directory under ignored `data/` for each set of files you want to
  retain. Files are written to `<output_dir>/<year>/<filename>`. Use one writer
  per snapshot directory.
- Before replacing an earlier copy, the index must have a CSV header with
  `EIN`, `TAX_PERIOD`, and `OBJECT_ID` and no duplicate columns. An archive
  must have a readable ZIP directory and at least one nonempty XML member that
  can be opened. These checks do not validate index rows, verify every ZIP
  member or checksum, or parse filing XML. The source contract remains
  provisional until checked against an approved live sample.
- Each nonempty batch keeps a separate JSON manifest under
  `<output_dir>/manifests/`. It records planned paths and URLs, run status and
  timestamps, completed byte counts and SHA-256 hashes, and failure type.
  A failure stops the batch and leaves later files pending. If a crash or
  manifest write error leaves the run marked `running`, reconcile published
  files with the manifest and retry in a fresh snapshot. A manifest is
  download provenance. Import and filing-level provenance remain separate.

### Stage Form 990 filings locally

Run from the repository root. Use the manifest of a completed XML archive
download and choose a new output file in an existing directory under
ignored `data/`. Use synthetic archives until the real source contract and
scope are approved.

```powershell
./.venv/Scripts/python.exe -m scripts.extract_990 data/synthetic/snapshot/manifests/run.json data/synthetic/filings.json
```

The JSON output contains staged filings and a report. Exit code `0` means
the batch staged without review findings, `2` means the JSON was written
and needs review, and `1` means extraction failed or the output path already
exists. A failed run leaves any earlier batch intact. For rollback, revert
the extractor change and remove only the generated batch files.

The provisional mapping covers full Form 990 only. It preserves leading
zeros in EINs, distinguishes zero amounts from missing amounts, and keeps
the return's tax year separate from its period end. It uses the ZIP member
basename (minus `_public`) as the provisional filing ID. Identical filing
IDs and XML hashes share a stable key. Conflicting observations are staged
with a review finding and remain separate. Archive and manifest checksums,
source URLs, download times, ZIP member names, and parser version are
recorded for provenance. The byte limits are 8 MiB per XML member and
512 MiB of eligible XML per run. Use separate snapshots for larger jobs.
Source identifiers and field mappings still require reconciliation with
an approved IRS sample before loading real data.

### Offline validation

From the repository root, with the existing Python environment and `requests`:

```powershell
./.venv/Scripts/python.exe -m unittest discover -s tests -p test_data_extract.py -v
```

Tests mock HTTP and retry waits; no IRS or Supabase access is performed. They
cover successful bytes/metadata, input validation, multiple states and aliases,
HTTP errors, bounded retries, empty bodies, interrupted downloads, publication
failure, reruns, and partial batch completion. Live endpoint/header compatibility
remains unverified.

Rollback: restore the pre-task downloader and scripts README, remove only this
task's new `tests/test_data_extract.py` and preflight report, and revert the
task-specific additions in the index, milestone, and test matrix. Preserve all
pre-existing uncommitted work; no database rollback is needed.
