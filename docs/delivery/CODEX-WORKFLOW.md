# Efficient Codex workflow

This package is optimized to keep an agent focused, reduce repeated context loading, and make each change reviewable. **Codex is a coding assistant, not the authority to accept business risk or deploy.**

## 1. Keep context small

For a task, point Codex to `AGENTS.md`, `docs/requirements/INDEX.md`, **one milestone**, the **two or three relevant domain files**, and `docs/delivery/TEST-MATRIX.md`. Never paste the whole original product interview into every prompt.

## 2. Use a plan → implement → verify loop

1. **Plan only:** enumerate touched files, dependencies, schema changes, source provenance, authorization concerns and tests; request unresolved owner decisions.
2. **Implement one vertical slice:** e.g., filing parser + staging contract + quality tests, not an entire portal in one change.
3. **Verify locally:** run formatting, lint/type checks, unit/integration tests; include actual command output summary.
4. **Review diff:** ask Codex for risks, migration reversibility, permission/PII review, acceptance evidence, unresolved items.
5. **Stop:** human makes technical/business gate decision before proceeding.

## 3. Suggested repository conventions (adapt when code exists)

```text
app/ or src/app/            Next.js routes and app shell
src/components/             Reusable UI components
src/lib/                    Shared validation, domain contracts
supabase/migrations/        Versioned SQL including RLS
pipelines/                  Python ETL with source adapters
tests/                      Fixtures + unit/integration/RLS coverage
docs/                       Product requirements, decisions, test coverage
```

Prefer one implementation of each calculation with tested, explicit schemas; do not copy financial formulas into independent Python, TypeScript and SQL codepaths unless needed and cross-validated. Avoid unnecessary frameworks.

## 4. Reusable task prompt

```text
Read AGENTS.md and docs/requirements/INDEX.md.
You are working ONLY on milestone [M0X], task [short description].
Relevant requirements: [ID list]. Read only their owning files,
MILESTONES.md, DECISIONS.md, and TEST-MATRIX.md.

FIRST: return a concise plan with proposed files, data and security
boundaries, assumptions, tests, acceptance criteria, rollback strategy,
and any blocking decisions. Do not code until I approve the plan.

AFTER approval: implement the smallest testable slice with synthetic
fixtures, run verification, and report results + unresolved issues.
Do not provision, deploy, call external paid services, use private data,
or begin another milestone without my explicit approval.
```

## 5. Avoid common agent inefficiencies

- **Duplicate specs:** One owning requirement and ID; link instead of copying full paragraphs.
- **Over-scaffolding:** No M05 AI tables, project finance APIs, or empty future modules in M01.
- **Unverifiable claims:** Provide commands/tests and exact source reconciliation samples.
- **Unsafe data assumptions:** Null is not zero; filing year is not tax year; mailing address is not service area; grant award is not proof of an obligation.
- **Premature infra:** Local synthetic tests before production accounts, service roles, scheduling, paid resources or batch crawling.
- **Oversized PRs:** Changes should be easy to inspect, revert and connect to acceptance tests.
- **Demo metrics:** Label synthetic fixtures; never blend generated nonprofit numbers with actual public records.

## 6. Architecture Decision Record (ADR) trigger

Write a short ADR when choosing data source normalization, map provider, authorization pattern, deployment mechanism, or any decision hard to reverse. Template:

```markdown
# ADR-XXX — Decision
Status: Proposed / Accepted
Context:
Options considered:
Chosen option and rationale:
Privacy/security/cost implications:
Rollback/migration path:
Related requirement IDs:
Approval/date:
```

## 7. Change reporting format

```markdown
Task / milestone / requirement IDs:
Files changed:
Tests run and actual result:
Data/privacy/security checks:
Unresolved questions:
Rollback notes:
Technical gate evidence:
Business gate: NOT EVALUATED (owner decision required)
```
