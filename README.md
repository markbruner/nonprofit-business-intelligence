# Nonprofit Business Portal — implementation handoff

**Status:** Requirements baseline; not authorization to deploy, spend money, or access private records.  
**Prepared:** November 14, 2026  
**Pilot:** 60 days **after** the complete prospect-to-outreach workflow is functional.

Build a private business operations portal starting with an evidence-based workflow to **find nonprofits → screen financials → review profiles → track relationships and service-specific opportunities**. The purpose is to reduce research effort and support actual discovery conversations, not maximize the number of records or features.

## Start here

1. Read [requirements index](docs/requirements/INDEX.md) for scope and ownership of every requirement.
2. Read [AGENTS.md](AGENTS.md) for Codex constraints and stop/approval rules.
3. Read [milestones and gates](docs/delivery/MILESTONES.md). **Only one explicitly approved milestone may be implemented at a time.**
4. Review [unresolved decisions](docs/delivery/DECISIONS.md) before touching data, infra, or production.
5. For the first coding session use [M01 kickoff task](docs/tasks/M01-data-foundation.md).

## Directory map

```text
AGENTS.md                         Codex safety, scope and work protocol
README.md                         Repository entrypoint
docs/requirements/INDEX.md        Canonical requirements navigation & statuses
docs/requirements/*.md            Domain-specific, uniquely identified requirements
docs/delivery/MILESTONES.md       Milestone scope, two gates, acceptance criteria
docs/delivery/DECISIONS.md        Confirmed choices, assumptions, unresolved approvals
docs/delivery/CODEX-WORKFLOW.md   Efficient agent work patterns and prompts
docs/delivery/TEST-MATRIX.md      Requirement-to-test traceability
docs/tasks/M01-data-foundation.md First bounded task brief
supabase/README.md                Unapplied loader/schema drafts and design-review hold
docs/reference/original-product-spec-v1.md  Archived interview synthesis
```

## Initiate the virtual environment
1. Run ```py -3.12 -m venv .venv``` (or whatever is the stable version)
2. Ensure it is listed on the .gitignore file.
3. Run the below command to initiate the environment replacing your location:
```
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& <insert your path>\.venv\Scripts\Activate.ps1)
```

## Change discipline

- Domain requirements in `docs/requirements/` are authoritative; the original spec under `reference/` is **historical context**, not a competing source of truth.
- Changes to product scope must update the owning requirements file, then this index and any affected tests/milestones. Use a short ADR for meaningful architectural changes.
- **No implementation approval is implied by including a requirement in these files.**
