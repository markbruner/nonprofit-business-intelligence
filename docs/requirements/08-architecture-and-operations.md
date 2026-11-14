# 08 — Architecture and operations

**Status:** Architecture direction confirmed; operational specifics pending. **Milestones:** M01–M04.

## Requirements

- **ARC-001** Use a **dedicated** Next.js + TypeScript Vercel project and a **dedicated** Supabase PostgreSQL/Auth project; do not share database or credentials with existing applications.
- **ARC-002** Initial address is an available temporary `*.vercel.app` URL. Later custom domain/business name must not require rewriting business logic.
- **ARC-003** Store database DDL/policies in version-controlled SQL migrations; review irreversible changes and document rollback strategies.
- **ARC-004** Prefer Python for extraction/normalization and SQL for deterministic financial calculations/screening; TypeScript for app/API. No duplicate financial business logic across languages.
- **ARC-005** Make public-data imports reproducible and idempotent, with validation reports and import/run logging. Separate staged data from published curated results.
- **ARC-006** Keep the data model normalized enough to represent canonical organizations, individual filings, manual evidence, relationships, and zero-to-many opportunities without coupling statuses.
- **ARC-007** Prefer a single filter/query contract powering Table/Map/Summary; test consistency and performance on representative volume.
- **ARC-008** Select mapping library/geocoder only after checking source precision, licensing/usage limits, cost, and realistic dataset size; preserve geocoding provenance.
- **ARC-009** Establish local/test/production boundaries, gated promotions, and a documented no-real-data-by-default development approach.
- **ARC-010** Instrument import/research job failures, audit events, and enough workflow analytics to measure pilot value without unnecessary instrumentation or PII.
- **ARC-011** Document operational owner, expected service/subscription costs, backup/restore procedure, and recovery test prior to live deployment.

## Core logical entities (planned, implement only when needed)

- **M01:** `organizations`, `organization_filings`, `organization_financials`, `screening_rule_versions`, `screening_results`, `import_runs`; add `organization_aliases`, source tables if needed for provenance.
- **M02:** `user_memberships`, `manual_evidence`/`research_notes` as necessary, `audit_events` where required.
- **M03:** `contacts`, `relationships`, `interactions`, `tasks`, `opportunities`, `opportunity_events`.
- **Possible M05:** see 10; no speculative migrations during M01–M04.

## Design principles

- Same organization ID across phases; don't rebuild contact/financial records on conversion to a client.
- Keep raw facts immutable or historically traceable, derived screening versioned, and manual overrides as separate reviewed events.
- Functions fail closed on auth/permission errors. Explicit empty/missing states over fake defaults.
- Avoid cron/job provider choice until workload measurements justify it.
