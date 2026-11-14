# M01 kickoff — bounded Codex task (plan first)

**Current status:** PROPOSED. No data collection, resource provisioning, deployment or production edits are authorized by this brief.

## Goal

Design and then, **after approval**, implement the smallest local, reproducible data foundation that can ingest representative **synthetic** nonprofit organization/filing records, normalize financial facts, and run versioned financial screening with auditable reasons.

## Read these only

- `AGENTS.md`
- `docs/requirements/INDEX.md`
- `docs/requirements/02-data-ingestion.md`
- `docs/requirements/03-financial-screening.md`
- `docs/requirements/08-architecture-and-operations.md`
- `docs/delivery/MILESTONES.md` (M01 only)
- `docs/delivery/DECISIONS.md` (O-01–O-03)
- `docs/delivery/TEST-MATRIX.md` (M01 rows)

## Phase 1 — plan only

Propose, do not implement:

1. Suggested minimal Python package layout, source adapter contract, staging/curated models, SQL schema and migration strategy.
2. A tiny synthetic fixture set with duplicate EIN/alias, amended filing, missing 990-EZ field, zero revenue, nonconsecutive fiscal years, 3-year history and one deficit year.
3. Deterministic metrics and configurable rules engine with explicit `unknown`/`needs_review` handling.
4. Idempotent ingest/re-run behavior, provenance, source versioning, and quality-report output.
5. Exact test names/commands and rollback approach.
6. List of blocked choices before real IRS ingestion, including counties, fields, tax-period semantics, comparability and thresholds.

**Stop and return the plan. Do not call external services or write code yet.**

## Phase 2 — after explicit approval

Implement only the authorized slice, run synthetic fixtures/tests, document discrepancies and candidate next task. Do not obtain bulk real nonprofit data until approved.

## M01 acceptance evidence to collect

- Same fixture imported twice → one canonical organization/filing set.
- Correct revenue-expense/margin computations and missing-data behavior.
- Amended return and identity collision surfaced with provenance.
- Ruleset version and reason codes visible in results.
- Clearly documented open choices and exact reproducible test commands.

## Copy/paste starter prompt for Codex

```text
Read AGENTS.md and docs/tasks/M01-data-foundation.md.
We are starting M01 only. Do PHASE 1: PLAN ONLY.
Use the requirement IDs and decision register referenced in the task.
Return the minimal proposed file tree, data model, synthetic fixture cases,
tests, assumptions, privacy/security risks and decisions that block real
IRS data ingestion. Do not code, fetch public data, spend money, provision,
or deploy. Stop for my approval.
```
