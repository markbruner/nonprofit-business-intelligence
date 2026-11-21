# Scripts

Place repeatable local development and data-maintenance scripts here. Document inputs, side effects, and safety.

## IRS downloader (`data_extract.py`)

M01 local downloader slice, approved by Mark on 2026-11-15. Importing the module
does no I/O. Real IRS collection still requires the source/scope decisions in
`docs/delivery/DECISIONS.md` (O-01/O-02); this task used synthetic HTTP responses
only. There is no CLI, scheduled refresh, parser, or Supabase connection.

Functions:

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
