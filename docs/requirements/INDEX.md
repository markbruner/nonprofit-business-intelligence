# Requirements index — authoritative navigation

**Baseline:** 2026-11-14 | **Scope:** version 1 first, future functionality clearly marked.  
**Implementation authorization:** none implied.  
**Change policy:** each requirement lives in **one** domain file. Other documents reference IDs rather than copying statements.

## Requirements map

| File | Domain | IDs | Timing |
|---|---|---|---|
| [01-product-scope.md](01-product-scope.md) | Goals, scope, business rules | PRD-001–PRD-009 | M01–M04 |
| [02-data-ingestion.md](02-data-ingestion.md) | Public sources, identity, ETL, provenance | DAT-001–DAT-011 | M01 |
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

2026-11-15: The approved M01 local-downloader slice has offline test evidence
for portions of DAT-001, DAT-006, DAT-007, and DAT-011. See
`../delivery/TEST-MATRIX.md` and `../../scripts/README.md`. This does not complete
the ingestion requirements or approve real data collection or the M01 gate.

2026-11-17: Offline Form 990 batch planning, artifact checks, and run manifests
add partial evidence for DAT-006, DAT-007, and DAT-011. See the test matrix.

2026-11-17: Local Form 990 XML staging adds synthetic evidence for portions
of DAT-003, DAT-005, DAT-007, DAT-008, and DAT-011. See the test matrix.

See [MILESTONES](../delivery/MILESTONES.md), [DECISIONS](../delivery/DECISIONS.md), and [TEST-MATRIX](../delivery/TEST-MATRIX.md). Must resolve county boundaries and financial/source-field coverage before a real M01 geographic extraction; must approve access before partner provisioning and any production deployment.
