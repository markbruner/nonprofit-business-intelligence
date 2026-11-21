# Decision register and assumptions

Keep this file small and current. **Chosen design preferences are not blanket authorization for cloud provisioning, real-data transfers, or production actions.**

## Confirmed in the interview

| ID | Decision |
|---|---|
| D-01 | Portal purpose: manage business operations; v1 focus is nonprofit discovery/qualification and outreach. |
| D-02 | Focus service: impact reporting and measurement. |
| D-03 | Qualification: need, financial capacity, mission/service fit; favor financial stability. |
| D-04 | Revenue screening target: $1M–$5M, configurable. |
| D-05 | Rule-based financial screening, not opaque weighted/predictive scores. |
| D-06 | Two-stage hybrid research; batch AI with human evidence review intended for a later milestone. |
| D-07 | Organization profiles: organization, finances, impact reporting, funding/grants. |
| D-08 | Separate organization relationships from multiple service-specific opportunities. |
| D-09 | Structured CRM for contacts/interactions/follow-ups. |
| D-10 | Admin plus Business Manager; partner may manage business functions, not system administration. |
| D-11 | Home: tasks/follow-ups, sales pipeline, research activity. Left sidebar, Table/Map/Summary views. |
| D-12 | Unified design based on personal homepage and nonprofit consulting page, replaceable brand. |
| D-13 | Temporary Vercel domain, separate Vercel project, separate Supabase database. |
| D-14 | Build one complete workflow in milestones, not an hours quota. |
| D-15 | Two-gate milestone reviews; 60-day pilot on research efficiency + sales validation. |

## Open decisions / blockers

| ID | Decision needed | Blocks | Low-risk work before answer |
|---|---|---|---|
| O-01 | Metro definition/year and exact Cincinnati/Cleveland **county lists**, mailing vs service geography | Real geographic extract | Synthetic fixture and configurable geography model |
| O-02 | IRS return types, years, preferred extraction datasets, field mapping, validation examples, source terms | Real ingestion | Build parser contracts and tests with synthetic/source-safe sample |
| O-03 | Calibrated screening thresholds and tolerance for false qualified prospects | Final rule release | Parameterized rules & edge-case tests |
| O-04 | Public/professional contact sourcing, acceptable outreach practices, retention/deletion period | Live CRM content | Build synthetic CRM tests |
| O-05 | Authoritative current homepage/nonprofit CSS, colors, typography, logos | Final visual tokens | Use temporary neutral design tokens |
| O-06 | Formal partner authorization to be provisioned; business finance data categories for manager | Invite/account & future finance access | Implement and test roles with fixtures |
| O-07 | Pilot baseline sample, quantitative targets, outreach capacity and review owner | Starting pilot clock | Define instrumentation and draft baseline method |
| O-08 | Subscription budget, account ownership, backup/restore owner and acceptable recovery | Paid resources / production | Local development and infra plan |
| O-09 | Chosen mapping/geocoding library/provider, data license and price | Map live integration | Build map data contract / placeholder without fake data |

## Proposed, not yet locked

### Bounded implementation approval — 2026-11-15

Mark's instruction, "Go ahead and implement the recommendations," approved the
reviewed local downloader refactor and synthetic-response tests. Scope:
state-specific URLs/files, request timeouts/bounded retries, temporary-file
publication, returned provenance, and documentation. See
`IRS-DOWNLOADER-PREFLIGHT.md` for the pre-implementation safety decision.
No source/geography choice, live collection, credential use, Supabase write,
paid resource, deployment, or next milestone was approved. O-01/O-02 remain open.

On 2026-11-17 Mark approved the reviewed Form 990 downloader improvements:
validated and deduplicated batch plans, separate year destinations, basic
checks before replacing a file, download manifests, and synthetic verification.
O-01 and O-02 remain open.

On 2026-11-17 Mark selected full Form 990 XML archives as the first extractor
source and approved local extractor implementation with synthetic tests.
Live source mapping, collection scope, credentials, and Supabase writes
require separate decisions. O-01 and the remaining O-02 questions stay open.

- Python + SQL ETL with Next.js/TypeScript app; Postgres migrations and dedicated private GitHub repository.
- Initial opportunity stages: identified, discovery, proposal, negotiation, won, lost, deferred.
- Three financial-screen labels: priority, needs_review, lower_priority.
- M01→M04 implementation sequence. Proposal from interview synthesis, subject to gate decisions.

## How to resolve an open decision

Record: date, decision-maker, selected choice, supporting evidence, affected requirements, and whether implementation/spend/deployment authority is granted. Do not merely replace `OPEN` with an assumption.
