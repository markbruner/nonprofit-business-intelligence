# Milestones and two-gate release policy

**Rule:** Each milestone advances only when (1) its technical acceptance evidence is documented **and** (2) the owner explicitly approves the business case for the next. Agent/test success alone cannot approve a next milestone.

| Milestone | Status | Requirement domains | Business outcome |
|---|---|---|---|
| M01 Data foundation | **Not started / not authorized** | DAT, SCR, selected ARC/PRD | Credible financially screened shortlist |
| M02 Prospect intelligence | **Blocked on M01 gate** | UX, RES, SEC, ARC | Faster review of real prospects |
| M03 CRM & opportunities | **Blocked on M02 gate** | CRM, UX, SEC | Track actual outreach without parallel spreadsheet |
| M04 Field pilot | **Blocked on M03 gate** | PIL, SEC, ARC | 60-day research & commercial validation |
| M05 AI research (possible) | **Deferred, not committed** | AIR | Only if bottleneck/ROI evidence justifies |

## M01 — Data foundation

**Loader permission/storage checkpoint — 2026-11-21:** Owner-returned disabled
loader metadata matches the reviewed permissions; no login is enabled. A local
synthetic storage benchmark passed (3,000 filings / 1,000 organizations, ~4.5 MB
schema/index growth). Cloud WAL/System/provisioned measurements and approved
operating thresholds remain pending; no cloud policy/data seed is authorized.

**Cloud schema checkpoint — 2026-11-21:** Mark applied the approved schema-only
migration manually. His returned verification matches all expected table, forced
RLS, role-lockdown and function ACL/hardening metadata. No live loader/import or
capacity calibration is verified. Scope/budget configuration, login activation
and uploads still require separate approval. Neither milestone gate is passed.

**Local XML validation — 2026-11-21:** Explicitly approved January sample passed:
one local archive, three selected regional records, index and direct-source field
checks, and offline loader-contract validation. Actual variants include two 2025
and one 2024 filing; 2023/historical coverage remains open. All 49 Python tests pass.
No Supabase changes. Fresh capacity measurements, approved policy settings and a
separate cloud-execution approval are required before a data load.

**Bounded source update — 2026-11-21:** Mark approved one fixed four-CSV local
sample. Existing downloader gained tested payload caps and one-attempt support;
the run completed at 89,863,197 bytes with source manifests and aggregate checks.
All 43 Python tests pass. Actual EO/index headers are now observed, but tax-year
coverage, XML sample reconciliation, scope persistence and operational storage
calibration remain open. No XML collection, cloud execution or M01 gate approval.

**Bounded task update — 2026-11-21:** Mark approved local schema/loader preparation
with storage checks and synthetic tests, then requested database-design review and
star-schema alignment before table creation. Draft SQL remains unapplied and on
execution hold (see `../../supabase/README.md`). Schema review added internal IDs
and removed duplicate financial JSON storage. All 34 Python and 8 API tests pass;
isolated PostgreSQL 16 SQL gate/recovery tests and empty-schema rollback/reapply
passed. Full Supabase platform behavior, concurrency and real capacity calibration
remain unverified. OH/KY/IN candidate scope is recorded in
DAT-013. No credential use, live collection/upload, deployment or gate advancement
has been approved.

**Bounded task update — 2026-11-15:** Mark approved the local IRS downloader
refactor and synthetic tests only. Implemented URL selection, sequential batch
downloads, safe temporary-file publication, bounded retries, and returned
provenance. All 15 downloader tests and 8 existing API/contract tests passed;
Black passed for the two changed Python files. See `TEST-MATRIX.md` and
`IRS-DOWNLOADER-PREFLIGHT.md`. This is partial technical evidence, not an M01
gate pass. Broader M01 implementation, real collection, Supabase loading, and
advancement to M02 remain unapproved.

**Bounded task update — 2026-11-17:** The owner approved the reviewed Form 990
downloader improvements for local implementation. Form 990 batches now
validate the download plan and basic artifact structure, preserve prior files
when validation fails, and persist a manifest for each run. See
`TEST-MATRIX.md` for synthetic test evidence. The M01 gate remains open.

**Bounded task update — 2026-11-17:** The local Form 990 extractor stages
filings and quality findings from a completed archive manifest. Synthetic
tests verified stable filing keys, visible conflicts, provenance, and local
publication behavior. Live source reconciliation and the Supabase loader
remain future tasks. See `TEST-MATRIX.md`.

**Scope:** Reproducible source imports, canonical registry, filing/financial history, transparent financial rules, provenance and quality report. Initial local-only development using synthetic fixtures can proceed as a proposed task after owner approval. Real extract awaits county/source selection.

**Technical gate:**
- Repeated import is idempotent; amended/duplicate/conflicting filings handled transparently.
- Sample reconciles to source filing for amounts, tax periods, and identifiers.
- Missing/zero/unsupported fields cannot fabricate margins or trend data.
- Versioned screening rules have readable reasons. A local test using synthetic data verifies that an override records the actor, timestamp, rationale, and previous and new outcomes while preserving the original computed result (SCR-008).
- Geographic list, data coverage, source-selection rules, and discrepancies documented.

**Business gate:** Produce a manually inspectable shortlist of plausible nonprofits and comparison of effort/quality against hand research. Owner decides if UI is worth building.

## M02 — Prospect intelligence interface

**Scope:** Auth/RLS, shell/sidebar, Overview with honest early data, Table/Map/Summary with common filters, profiles, manual evidence, shortlist. No CRM implementation unless separately approved after M02 gate.

**Technical gate:**
- Signed-out and wrong-role API/database access is denied. A test verifies that a privileged action is denied to an administrator without verified MFA and succeeds for the same administrator with verified MFA (SEC-005). Assess whether to require manager MFA before shared launch.
- Before enabling shared portal overrides, verify that authorized users can record an override, unauthorized users are denied at the server and database, and the original computed result remains auditable (SCR-008, SEC-003, SEC-004).
- Filtered counts agree across table, map, summary, including unmappable records labeled.
- Financial data show fiscal period/source; missing/unknown states clear.
- Revenue, mission, geography, stability filters work with representative volume; responsive/keyboard checks pass.

**Business gate:** Representative research tasks are measurably faster or more accurate vs manual approach. Owner documents whether next CRM investment is justified.

## M03 — CRM and opportunities

**Scope:** Contacts, relationship status/owner, manual interactions, tasks/overdue, separate opportunities with stage history, actionable home dashboard.

**Technical gate:**
- One organization supports zero or multiple opportunities without duplicate identity.
- Follow-ups/overdue tasks reflect dates and assignments; stage transitions auditable.
- Manager business actions permitted; settings/roles changes rejected by UI, API and RLS tests.
- No automatic opportunity creation from screening.

**Business gate:** Run real prospect outreach without parallel sheet and record administration time, data quality and follow-up reliability.

## M04 — 60-day pilot

**Scope:** Real usage over 60 days after M03 readiness, baseline comparison, outreach/deeper conversations, evaluation report.

**Technical gate:** Stable workflows, documented recovery/backups, visible import failures, secure accounts, measurable activity with low logging friction.

**Business gate:** Compare against pre-registered targets for net research time, screen quality, meaningful conversations and buying signals. Document **continue/revise/stop** and approve or decline M05.

## Two-gate review note template

```markdown
### Milestone M0X decision — YYYY-MM-DD
Technical gate: PASS / FAIL (evidence links)
Business gate: CONTINUE / REVISE / STOP (measured evidence)
Known defects / operational burden:
Next milestone explicitly approved? YES / NO
Approver and approval record:
```
