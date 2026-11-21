# Requirement-to-test matrix

This is a **test plan**, not a claim that tests have been written or passed. Add actual test paths and results as code is created.

| Milestone | Requirements | Minimal verification | Status |
|---|---|---|---|
| M01 | DAT-002–DAT-005, DAT-007–DAT-008 | Idempotent import; EIN alias/collision; source tax periods; amendment selection; missing-vs-zero handling | NOT RUN |
| M01 | DAT-001, DAT-006, DAT-009–DAT-011 | Source metadata, manual import validation, county config, geocoding provenance, failed-run integrity | NOT RUN |
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
