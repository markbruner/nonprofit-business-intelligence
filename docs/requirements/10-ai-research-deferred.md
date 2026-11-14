# 10 — AI research design intent — **not authorized for version 1**

**Status:** Backlog candidate only. **Earliest possible milestone:** M05 after business-value review.

## Requirements if separately approved

- **AIR-001** Use two-stage research: first rule-screen broad public nonprofit data, then perform deep research for approved selected organizations only.
- **AIR-002** Authorized users can select nonprofits into **bounded batches** with proposed research questions, run limits and a cost cap.
- **AIR-003** Require explicit approval before starting a research batch and a controlled stop/cancel path; do not research thousands by default.
- **AIR-004** Research only approved public organization websites/reports/funding sources within source terms; block private data collection and unauthorized outbound actions.
- **AIR-005** Store **structured findings and evidence**: category, asserted claim, URL/source, excerpt/locator where permitted, source date, collection date, run ID, and clear observed/inferred/confirmed/unknown status.
- **AIR-006** Retain organization-level review, with per-finding edit/approve/reject controls. Do not bulk-trust findings automatically.
- **AIR-007** Only approved findings influence accepted summaries/qualification. Preserve rejected/edited versions and reviewer decisions for audit.
- **AIR-008** Track error/unsupported-claim rate and complete review time, not a made-up model confidence percentage.
- **AIR-009** Never initiate outreach, edit protected records, publish externally, or manipulate security/roles from a research agent.
- **AIR-010** Require measured net time savings **and** acceptable research quality relative to manual process before expanding automation.

## Possible logical entities (do not migrate yet)

`research_batches`, `research_jobs`, `research_sources`, `research_findings`, `finding_reviews`.

## Approval criteria for proposing M05

1. M04 identifies manual impact-report research as a meaningful bottleneck.
2. Expected savings exceed build/maintenance/review costs based on actual workflow data.
3. Source use, model/provider, data retention, batch/runtime costs and review design are approved.
4. A bounded evaluation dataset and factual-error acceptance thresholds exist.
