# Requirements index — authoritative navigation

**Baseline:** 2026-11-14 | **Scope:** version 1 first, future functionality clearly marked.  
**Implementation authorization:** none implied.  
**Change policy:** each requirement lives in **one** domain file. Other documents reference IDs rather than copying statements.

## Requirements map

| File | Domain | IDs | Timing |
|---|---|---|---|
| [01-product-scope.md](01-product-scope.md) | Goals, scope, business rules | PRD-001–PRD-009 | M01–M04 |
| [02-data-ingestion.md](02-data-ingestion.md) | Public sources, identity, ETL, provenance, disk budget, state scope | DAT-001–DAT-013 | M01 |
| [03-financial-screening.md](03-financial-screening.md) | Measures, rules, review, priority | SCR-001–SCR-010 | M01 |
| [04-profiles-and-evidence.md](04-profiles-and-evidence.md) | Profiles, impact/funding evidence | RES-001–RES-009 | M02–M03 |
| [05-crm-and-opportunities.md](05-crm-and-opportunities.md) | Relationships, contacts, tasks, pipeline | CRM-001–CRM-012 | M03 |
| [06-interface-and-design.md](06-interface-and-design.md) | Dashboard, filters, map, accessibility | UX-001–UX-011 | M02–M03 |
| [07-security-and-governance.md](07-security-and-governance.md) | Roles, RLS, least privilege, privacy | SEC-001–SEC-014 | M02; apply throughout |
| [08-architecture-and-operations.md](08-architecture-and-operations.md) | Stack, environments, observability | ARC-001–ARC-011 | M01–M04 |
| [09-pilot-and-measurement.md](09-pilot-and-measurement.md) | Business validation & measurement | PIL-001–PIL-009 | Baseline before pilot; M04 |
| [10-ai-research-deferred.md](10-ai-research-deferred.md) | Approved design intention, **not MVP scope** | AIR-001–AIR-010 | Possible M05 only |

## Milestone reading lists

- **M01 — Data foundation:** 01, 02, 03, relevant 08, 09 baseline; `MILESTONES.md` M01; `DECISIONS.md` geography/source/rule gaps.
- **M02 — Prospect intelligence:** 01, 04, 06, 07, relevant 08; `MILESTONES.md` M02.
- **M03 — Relationships and opportunities:** 01, 05, 06, 07; `MILESTONES.md` M03.
- **M04 — 60-day pilot:** 09 and operational criteria in 07–08; `MILESTONES.md` M04.
- **Possible M05 — AI research:** 10, 04, 07, 08, 09; only after approval following pilot evidence.

## Cross-cutting distinctions

1. **Financial screen:** automated rules/classification of financial plausibility, with reasons; does not prove available budget.
2. **Reporting need:** evidence-based hypothesis or discovery-confirmed problem; not inferred from financial filings alone.
3. **Relationship:** activity and contacts associated with an organization; no dollar value implied.
4. **Opportunity:** concrete possible paid service engagement; zero to many per organization.
5. **Client/project/financial operations:** longer-term product vision, not initial release implementation.

## Stop/go gates and outstanding choices

2026-11-21 runner checkpoint: one local command prepares tax-2023 reviewed batches
of at most thirty records with payload bounds; explicit injected execution API
reuses server capacity/scope gates and never retries automatically. 75 tests pass;
thirteen-record package prepared, no cloud contact. Partial DAT-003/005/006/007/008/
011/012/013 and ARC-005 evidence. Credentials/live transport/owner settings and upload
remain unapproved; see ../delivery/PIPELINE-RUNNER-PREFLIGHT.md.

2026-11-21 tax-2023 checkpoint: 13 actual examples found in the existing local
archive across all three states (OH 4 / KY 2 / IN 7), 91 direct-field checks and
offline contract pass, 67 Python tests pass. Partial DAT-003/007/008/013 evidence;
sample absence is resolved, complete history remains unverified. See
IRS_SOURCE_CONTRACT.md and ../delivery/TAX2023-COVERAGE-PREFLIGHT.md. No cloud action.

2026-11-21 latest storage checkpoint: owner read-back verifies second-trial counts,
max_rows=30, remaining safeguards and LOGIN false. DB/relation growth each 73,728
bytes; WAL allocation unchanged. Partial DAT-005/011/012 evidence, not bulk-scale
calibration. Pending SQL read-back notes below are superseded; future imports and
milestone release remain unapproved.

2026-11-21 latest completion: owner returned 33 organizations / 33 filings / 2 runs /
33 provenance links, LOGIN false, DB 11,622,067 bytes. Matches second-trial expected
totals; partial DAT-005/011/012 evidence. Post-batch storage/policy read-back pending;
earlier pending-execution notes are historical. Further imports remain unapproved.

2026-11-21 latest next-batch checkpoint: post-import diagnostic received and reviewed;
conservative thirty-filing projection ~560 MB including reserve/growth, below 1.5 GB
stop. Populated-target SQL prepared/tested; max_rows 3->30 and upload await explicit
approval. DAT-005/011/012 partial evidence; 62 Python tests pass. Earlier pending
measurement notes below are historical. No milestone release.

2026-11-21 next-batch preparation: 30 additional filings validated locally, 10/state,
for partial DAT-003/007/008/013 evidence. DAT-012 post-import query prepared; owner
results and fresh System/provisioned readings pending. No cloud policy change or
larger import approved. See `../delivery/NEXT-BATCH-PREFLIGHT.md`.

2026-11-21 latest checkpoint: Mark approved and ran the first cloud transaction;
returned complete with 3 organizations / 3 filings / 1 run / 3 provenance links
and LOGIN false. Partial DAT-005/011/012 evidence. Earlier preparation blockers
below are historical for this trial. Further loads and milestone gates remain open.

2026-11-21: Cloud policy metadata matches approved values. First three-record
transaction is prepared and tested offline (DAT-005/011/012 partial evidence),
not executed in Supabase. Fresh System evidence and explicit first-data approval
are still required. See `../delivery/CLOUD-TRIAL-PREFLIGHT.md`.

2026-11-21: Owner-run cloud schema metadata verification matches expected counts,
RLS, role flags and grants. This is a schema-only checkpoint; cloud imports,
capacity calibration and live loader authentication remain unverified/unapproved.

2026-11-21: Approved local selected-member XML validation passed for three records
(2024 and 2025 variants). See source contract/test matrix. This strengthens partial
DAT-003/007/008 evidence; full 2023–2025 coverage and cloud capacity remain open.

2026-11-21: Approved bounded OH/KY/IN EO plus 2026-index sample completed locally;
actual headers and aggregate scope counts are recorded in `IRS_SOURCE_CONTRACT.md`.
This supplies partial DAT-001/006/007/011/013 evidence, not XML tax-year coverage.

2026-11-21: Initial full-990 XML tax years are 2023–2025 inclusive (DAT-003).
Archive publication year is not the filing tax year; availability and source
mapping still require verification before collection. The SQL gate is tested
locally for rejecting unknown and out-of-policy years.

2026-11-21: DAT-013 / D-17 establish Ohio, Kentucky, and Indiana as the candidate
registry/EIN allowlist scope. County targeting remains a separate decision.
Local loader and migration drafts add partial M01 evidence only; database
integration/security tests and measured storage calibration remain outstanding.

2026-11-21: Mark established a disk-budget constraint for future Supabase ingestion
(DAT-012; D-16 in the decision register). Capacity checks, stop thresholds, and
regional filtering are required design work, not implemented controls. Numeric
headroom and batch limits require representative measurements before bulk loading.

2026-11-15: The approved M01 local-downloader slice has offline test evidence
for portions of DAT-001, DAT-006, DAT-007, and DAT-011. See
`../delivery/TEST-MATRIX.md` and `../../scripts/README.md`. This does not complete
the ingestion requirements or approve real data collection or the M01 gate.

2026-11-17: Offline Form 990 batch planning, artifact checks, and run manifests
add partial evidence for DAT-006, DAT-007, and DAT-011. See the test matrix.

2026-11-17: Local Form 990 XML staging adds synthetic evidence for portions
of DAT-003, DAT-005, DAT-007, DAT-008, and DAT-011. See the test matrix.

See [MILESTONES](../delivery/MILESTONES.md), [DECISIONS](../delivery/DECISIONS.md), and [TEST-MATRIX](../delivery/TEST-MATRIX.md). State scope is approved by DAT-013; source-field coverage and collection limits still require review before real ingestion. County boundaries remain open for finer targeting. Approve access before partner provisioning and any production deployment.
