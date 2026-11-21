# Decision register and assumptions

Keep this file small and current. **Chosen design preferences are not blanket authorization for cloud provisioning, real-data transfers, or production actions.**

## Confirmed in the interview

| ID | Decision |
|---|---|
| D-01 | Portal purpose: manage business operations; v1 focus is nonprofit discovery/qualification and outreach. |
| D-02 | Focus service: impact reporting and measurement. |
| D-03 | Qualification: need, financial capacity, mission/service fit; favor financial stability. |
| D-04 | Revenue screening target: $1M–$5M, configurable. |
| D-05 | Rule-based financial screening, not opaque weighted/predictive scores. |
| D-06 | Two-stage hybrid research; batch AI with human evidence review intended for a later milestone. |
| D-07 | Organization profiles: organization, finances, impact reporting, funding/grants. |
| D-08 | Separate organization relationships from multiple service-specific opportunities. |
| D-09 | Structured CRM for contacts/interactions/follow-ups. |
| D-10 | Admin plus Business Manager; partner may manage business functions, not system administration. |
| D-11 | Home: tasks/follow-ups, sales pipeline, research activity. Left sidebar, Table/Map/Summary views. |
| D-12 | Unified design based on personal homepage and nonprofit consulting page, replaceable brand. |
| D-13 | Temporary Vercel domain, separate Vercel project, separate Supabase database. |
| D-14 | Build one complete workflow in milestones, not an hours quota. |
| D-15 | Two-gate milestone reviews; 60-day pilot on research efficiency + sales validation. |

## Open decisions / blockers

| ID | Decision needed | Blocks | Low-risk work before answer |
|---|---|---|---|
| O-01 | Metro definition/year and exact Cincinnati/Cleveland **county lists**, mailing vs service geography | County-level prospect targeting; three-state candidate registry is approved separately in D-17 | Synthetic fixture and configurable geography model |
| O-02 | IRS return types, years, preferred extraction datasets, field mapping, validation examples, source terms | Real ingestion | Build parser contracts and tests with synthetic/source-safe sample |
| O-03 | Calibrated screening thresholds and tolerance for false qualified prospects | Final rule release | Parameterized rules & edge-case tests |
| O-04 | Public/professional contact sourcing, acceptable outreach practices, retention/deletion period | Live CRM content | Build synthetic CRM tests |
| O-05 | Authoritative current homepage/nonprofit CSS, colors, typography, logos | Final visual tokens | Use temporary neutral design tokens |
| O-06 | Formal partner authorization to be provisioned; business finance data categories for manager | Invite/account & future finance access | Implement and test roles with fixtures |
| O-07 | Pilot baseline sample, quantitative targets, outreach capacity and review owner | Starting pilot clock | Define instrumentation and draft baseline method |
| O-08 | Subscription budget, account ownership, backup/restore owner and acceptable recovery | Paid resources / production | Local development and infra plan |
| O-09 | Chosen mapping/geocoding library/provider, data license and price | Map live integration | Build map data contract / placeholder without fake data |

## Owner decisions after baseline

### D-16 — Disk-budget constraint — 2026-11-21

Mark requested that future development explicitly avoid exceeding this project's
included Supabase disk allowance. Initial ingestion is limited to nonprofits in
the target regions; exact geography and source scope remain governed by O-01/O-02.
The owning requirement is DAT-012 in `../requirements/02-data-ingestion.md`.

Mark reported an existing paid plan and an 8 GB included gp3 allowance per project;
verify the new project's actual allowance before use. The numeric stop threshold,
headroom, batch-size estimate, and measurement freshness limit remain unresolved
until a representative development import is measured and reviewed with Mark.
Loader checks reduce risk but cannot guarantee total project disk usage or billing.
Provisioned disk can remain larger than actual database usage after cleanup.

This decision authorizes recording the design constraint only. It does not approve
project provisioning, credential use, live downloads/uploads, automatic disk growth,
additional spending, or deployment. No loader controls have been implemented or
verified. O-08 remains open.

### D-17 — Candidate registry scope and bounded loader approval — 2026-11-21

Mark selected Ohio, Kentucky, and Indiana for the initial nonprofit candidate
registry/EIN allowlist (DAT-013). This expands ingestion candidates beyond the
metro prospecting scope; it does not redefine service geography. County choices
remain open for prospect targeting. IRS state-address coverage and missing/other
return types must remain explicit; full-990 XML cannot establish a complete
three-state nonprofit registry by itself.

Mark confirmed an empty, dedicated Supabase development project and explicitly
approved local schema/loader preparation with storage checks and synthetic tests.
No credentials, project URL, or keys are needed in these source files. This slice
does not approve connection/credential use, migration execution against Supabase,
live collection, uploads, spending, or deployment. O-02/O-08 and the measured
DAT-012 operating thresholds remain open. See `SUPABASE-LOADER-PREFLIGHT.md`.

Mark subsequently started Docker and authorized continuation of the local tests.
An isolated synthetic PostgreSQL test database was used; no live/cloud operation
or real source collection was approved by this step.

### Initial filing years — 2026-11-21

Mark selected tax years 2023 through 2025 inclusive for the first full-990 import
(DAT-003). These are XML tax years, not archive publication years or years inferred
from period end. O-02 is partially resolved; mapping, source terms, actual coverage
and collection limits remain open. Selection does not approve live collection or
cloud execution. The storage screenshot showed approximately 0.25 GB used on a
2 GB provisioned disk, with an 8 GB included allowance and spend cap shown enabled.
These rounded readings are planning context, not fresh operational measurements
or approved capacity thresholds.

## Proposed, not yet locked

### Initial storage-policy approval — 2026-11-21

Mark supplied current DB bytes 11,409,075 and WAL bytes 83,886,444, measured at
2026-11-21 14:31:47 UTC, provisioned disk 2 GB, System 167 MB and System timestamp
1795271293373000. Interpreted as Unix microseconds, that timestamp is
2026-11-21 14:28:13.373 UTC, consistent with the SQL reading. Do not substitute
the time of viewing or executing SQL for those observation timestamps.

Conservative unit bounds for planning: provisioned floor 2,000,000,000 bytes;
System upper bound 168 MiB (176,160,768 bytes), covering common MB/MiB integer
rounding interpretations. Other-disk bound with measured WAL: 260,047,212 bytes;
combined observed/bounded baseline: 271,456,287 bytes. These are explicit bounds,
not claims of exact provider bytes. Refresh before use; do not seed stale readings.

Proposal for the initial three-record trial only: stop 1,500,000,000 bytes;
reserve 256 MiB; max age 15 minutes; max rows 3; max payload 64 KiB; growth estimate
max(4x payload, 64 KiB per row). Approved tax-year scope remains 2023–2025. The
three-row admission estimate using these readings is about 540 MB INCLUDING the
reserve, below the proposed stop and provisioned floor. This is not a provider
quota or guarantee against other writers/WAL growth.

After clarification that the three-filing limit is per trial batch, Mark explicitly
approved `../../supabase/setup/storage_policy.sql`. Owner execution/read-back is
PENDING. Approval covers policy only; no capacity snapshot, EIN allowlist,
credentials, LOGIN activation or records. Mark will run the SQL manually.
Next capacity seed must retain the oldest component measurement timestamp and
document the unit bounds; currently supplied values can expire before first load.

### Disabled loader identity approval — 2026-11-21

After schema verification passed, Mark explicitly approved
`../../supabase/setup/loader_role.sql` in the same dedicated development project.
Scope: create nb_loader_dev as NOLOGIN with no password; grant CONNECT and
inherited nb_ingest function access without SET/admin/executor membership; set
connection/time safeguards. No credential creation, LOGIN activation, capacity/
scope seed or data import is included. Mark will run the script manually.
Mark returned the expected loader-role verification: login/admin/bypass flags
false, connection limit 1, CONNECT/inherited ingestion/function execution true,
SET-ingest/executor membership/direct insert/budget update false. Cloud metadata
checkpoint PASSED; no live authentication has been tested or enabled. No browser
automation or direct agent database connection is authorized by this decision.

### Schema-only cloud migration approval — 2026-11-21

After read-only cloud preflight confirmed PostgreSQL 17.12, role/schema creation
capabilities, no pipeline schema and no pipeline-role collisions, Mark explicitly
approved the schema-only migration in the dedicated development project. Scope:
`../../supabase/migrations/202611210001_990_loader.sql` only (seven tables, forced
RLS, import function, indexes and two non-login roles). No loader identity setup/
activation, passwords, scope/capacity seeding, records, data upload or deployment.

Local PostgreSQL 17.12 migration/security/storage/rollback checks passed before
approval. Chrome automation was not approved; no UI action or cloud SQL was
executed by the agent. Mark elected to run the reviewed SQL manually in Supabase's
SQL Editor. Mark subsequently reported seeing all seven expected tables in
`nonprofit_ingest`. Mark then returned the read-only schema verification result:
7 tables, 7 RLS enabled, 7 forced RLS, 2 locked non-login roles, loader function
execution allowed, anonymous/authenticated/service-role function execution denied,
loader direct insert/budget update denied, and hardened function metadata true.
All reported checks match expected values. This verifies cloud metadata, not a
live loader login, adversarial app calls or import behavior. No destructive
rollback, login activation, configuration seed or import is approved here.
Applied manually in SQL Editor; CLI migration-history reconciliation remains
pending before any future `supabase db push`. Do not rerun the applied CREATE-role
migration or silently mark migration history without review.

### Supabase versus local storage; January sample — 2026-11-21

Mark clarified that the storage constraint concerns Supabase, not local download
volume, and explicitly approved the proposed local January XML sample. One
national archive was retained locally; only three indexed regional filings were
parsed. The successful sample and limited 2024/2025 mapping evidence are recorded
in the source contract and test matrix. No cloud execution or upload was approved.
Operational transfer caps remain separate from the project's disk-budget policy.

### Bounded public CSV sample approval and execution — 2026-11-21

After reviewing the exact four-file/175 MB plan, Mark asked to reuse the existing
downloaders and explicitly instructed "Sounds good, proceed." This approved one
local OH/KY/IN EO snapshot plus the 2026 publication index, with hard payload caps,
no retries/redirects, no XML archives and no Supabase access. The safety review is
`SOURCE-SAMPLE-PREFLIGHT.md`. The run completed within bounds (89,863,197 bytes),
with aggregate findings in `../requirements/IRS_SOURCE_CONTRACT.md`. No further
collection, cloud operation or milestone gate was approved.

### Bounded implementation approval — 2026-11-15

Mark's instruction, "Go ahead and implement the recommendations," approved the
reviewed local downloader refactor and synthetic-response tests. Scope:
state-specific URLs/files, request timeouts/bounded retries, temporary-file
publication, returned provenance, and documentation. See
`IRS-DOWNLOADER-PREFLIGHT.md` for the pre-implementation safety decision.
No source/geography choice, live collection, credential use, Supabase write,
paid resource, deployment, or next milestone was approved. O-01/O-02 remain open.

On 2026-11-17 Mark approved the reviewed Form 990 downloader improvements:
validated and deduplicated batch plans, separate year destinations, basic
checks before replacing a file, download manifests, and synthetic verification.
O-01 and O-02 remain open.

On 2026-11-17 Mark selected full Form 990 XML archives as the first extractor
source and approved local extractor implementation with synthetic tests.
Live source mapping, collection scope, credentials, and Supabase writes
require separate decisions. O-01 and the remaining O-02 questions stay open.

- Python + SQL ETL with Next.js/TypeScript app; Postgres migrations and dedicated private GitHub repository.
- Initial opportunity stages: identified, discovery, proposal, negotiation, won, lost, deferred.
- Three financial-screen labels: priority, needs_review, lower_priority.
- M01→M04 implementation sequence. Proposal from interview synthesis, subject to gate decisions.

## How to resolve an open decision

Record: date, decision-maker, selected choice, supporting evidence, affected requirements, and whether implementation/spend/deployment authority is granted. Do not merely replace `OPEN` with an assumption.
