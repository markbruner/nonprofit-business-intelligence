# 01 — Product outcomes and scope

**Status:** Decision baseline. **Owner:** product/business. **Release:** M01–M04.

## Product requirements

- **PRD-001** Build an internal, private **business operations** portal whose first complete workflow is nonprofit prospect discovery → financial screen → organization review → relationship and opportunity tracking.
- **PRD-002** Prioritize **impact reporting and measurement** as the initial consulting service for prospect qualification, without excluding future offerings.
- **PRD-003** Initially target nonprofits with roughly **$1M–$5M annual revenue**; this is a configurable hypothesis, not a verified purchase-propensity threshold.
- **PRD-004** Initially cover Greater Cincinnati and Greater Cleveland including suburbs; county inclusion and reference definition remain an explicit pre-import decision.
- **PRD-005** Prioritize **financial stability**, but never automatically reject an organization based only on one deficit year.
- **PRD-006** Prioritize three distinct prospect attributes: demonstrated reporting need, financial capacity, and mission/service fit. Record evidence/inference separately from confirmed needs.
- **PRD-007** Allow organization relationships without sales opportunities, and multiple service-specific opportunities per organization.
- **PRD-008** Evaluate success by research efficiency and meaningful sales validation, not number of records imported, dashboard cards, or unqualified meetings.
- **PRD-009** Preserve flexibility for later Clients, Projects, Finances, and AI Research capabilities, without building placeholder features or infrastructure ahead of demonstrated need.

## In the first complete workflow

A dedicated data foundation, authenticated prospect interface, nonprofit profiles, transparent rules, shared table/map/summary filters, relationships, contact notes, tasks and follow-ups, and opportunity stages with history. See milestone assignment in `../delivery/MILESTONES.md`.

## Explicitly out of current release

Automated report/website AI research; client portals; client data processing; program impact dashboards for customers; contract/invoice/payment functionality; email/calendar synchronization; autonomous outreach; predictive purchase scoring; general-purpose workflow engine; multi-tenant SaaS; public publishing.

## Constraints / business assumptions

- Publicly observable reporting shortcomings are a **research lead**, not proof of an internal operational problem.
- A deficit is a contextual signal; tax filings may lag and restricted funds/assets may be unusable for consulting services.
- A prospect enters a dollar-valued opportunity pipeline only when a specific plausible paid engagement exists.
- Version 1 is evaluated over 60 days **after the complete workflow is functional**.
