# Instructions for Codex and other coding agents

## Read order
1. `docs/requirements/INDEX.md`
2. `docs/delivery/MILESTONES.md`
3. `docs/delivery/DECISIONS.md`
4. **Only** the domain requirement files relevant to the currently approved milestone
5. `docs/delivery/TEST-MATRIX.md` and the active task brief

Do not load the archived original specification unless a requirement conflicts or requires historical context. Each requirement has one owning file.

## Mission and scope lock
- Deliver the smallest credible private nonprofit-prospecting workflow that saves research time and supports outreach.
- Work on **one approved milestone and one small vertical task at a time**. Do not begin the next milestone without an explicit technical-readiness AND business-value decision.
- Deferred features are not permission to create schema, integrations, screens, or scaffolding for them.
- Do not silently decide business-critical questions in `docs/delivery/DECISIONS.md`. Mark blocked items and propose low-risk alternatives.

## Safety and authority
- **No access, copying, logging, uploading, or transmission of client, donor, volunteer, employee, personal, or proprietary data** without explicit user approval and clearly defined boundaries. Use synthetic test fixtures.
- Public IRS/nonprofit research is allowed for design and local development subject to documented source terms and approved geographic/scope choices; avoid bulk external collection until its limits are agreed.
- Do not create paid cloud resources, deploy to production, change production databases, add users, grant permissions, send outreach, publish externally, or perform destructive operations without explicit approval.
- Keep secrets out of code, logs, prompts, test fixtures, and browser bundles. Never use service-role credentials in the browser.
- All persistent data access and mutations require server-side authorization and Postgres RLS; UI hiding is not security.

## Technical defaults
- App: Next.js + TypeScript; data engineering: Python + SQL; Postgres/Supabase with versioned migrations.
- Prefer deterministic, auditable financial rules over opaque scoring. Preserve source, tax period, and import provenance.
- Separate organization identities, relationship statuses, financial screening, and individual sales opportunities.
- No speculative abstractions, premature microservices, or duplicated domain logic. Prefer pure functions for math, validated inputs, and tested idempotent ETL.
- No realistic-looking fabricated nonprofit facts in production or demos; synthetic fixtures clearly labeled.

## Task protocol
For each task:
1. State milestone, requirement IDs, proposed files, assumptions, test plan, risks, and rollback.
2. Stop for unresolved approvals affecting data, permissions, external activity, cost, or deployment.
3. Implement a narrow change with migrations/tests/docs when required.
4. Run relevant tests; report commands and actual results, including failures.
5. Provide a short diff summary, requirement coverage, outstanding issues, and whether **technical** gate evidence exists. Never self-approve **business** gate.

## Definition of done (per task)
- Behavior satisfies cited requirement IDs; tests verify positive, negative, and missing-data paths.
- Migrations are reviewed, reversible where practical, and do not modify production without approval.
- Data provenance/permissions remain intact; lint/type/test checks pass or failures are disclosed.
- Index, test matrix, decision log, and milestone status are updated where affected.
- Stop and request milestone review. Do **not** deploy automatically.
