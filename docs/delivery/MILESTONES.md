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

**Scope:** Reproducible source imports, canonical registry, filing/financial history, transparent financial rules, provenance and quality report. Initial local-only development using synthetic fixtures can proceed as a proposed task after owner approval. Real extract awaits county/source selection.

**Technical gate:**
- Repeated import is idempotent; amended/duplicate/conflicting filings handled transparently.
- Sample reconciles to source filing for amounts, tax periods, and identifiers.
- Missing/zero/unsupported fields cannot fabricate margins or trend data.
- Versioned screening rules have readable reasons; overrides are traceable.
- Geographic list, data coverage, source-selection rules, and discrepancies documented.

**Business gate:** Produce a manually inspectable shortlist of plausible nonprofits and comparison of effort/quality against hand research. Owner decides if UI is worth building.

## M02 — Prospect intelligence interface

**Scope:** Auth/RLS, shell/sidebar, Overview with honest early data, Table/Map/Summary with common filters, profiles, manual evidence, shortlist. No CRM implementation unless separately approved after M02 gate.

**Technical gate:**
- Signed-out and wrong-role API/database access denied; MFA/admin policy assessed.
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
