# Nonprofit Business Portal — Product & Implementation Specification

**Status:** Interview-complete design baseline; implementation not authorized by this document  
**Version:** 1.0 (planning), November 14, 2026  
**Intended users:** System Administrator (business owner) and Business Manager (partner)  
**Pilot:** 60 days after the first complete workflow is functional

## 1. Executive decision

Build an internal business operations portal, starting with a complete **nonprofit prospect research → financial screening → organization review → relationship management** workflow. Measure whether the portal reduces research effort and supports genuine discovery conversations. Do not build the full future business operating system upfront.

**Milestone promotion rule:** Advance only when (a) objective functional, data-quality, and security acceptance criteria pass **and** (b) there is a documented business-value case for the next milestone. A technically complete milestone does not automatically justify the next one.

## 2. User outcomes and scope

### Primary jobs to be done

1. Find nonprofits across the Greater Cincinnati and Greater Cleveland areas.
2. Filter for organizations with approximately **$1 million–$5 million annual revenue** and relatively stable finances.
3. Compare operating surplus/deficit, 3-year revenue trends, mission category, organization size, and an explainable financial-capacity assessment.
4. Review a nonprofit's organization, financial, impact-reporting, and funding/grant information, with citations and dates wherever research supports it.
5. Select organizations for outreach; manage contacts, interactions, follow-up tasks, and relationships.
6. Create **multiple service-specific opportunities per organization** when a plausible engagement is identified; do not inflate the opportunity pipeline with every imported or financially qualified nonprofit.
7. Coordinate work between an administrator and a business-manager partner.

### Included in first complete workflow (release candidate)

- Authenticated private portal; responsive left sidebar; home dashboard with tasks/follow-ups, opportunity pipeline, and available research/import activity.
- Organization registry, original-source references, EIN matching, annual financial facts, rule-based screening, geographic and mission filters.
- Prospects workspace with **Table / Map / Summary** switchable views sharing filter state.
- Organization profiles showing organization overview, financial overview, impact reporting research (manual initially), and funding/grants evidence (manual initially).
- Basic structured CRM: contacts, relationship status, interaction notes, owners, tasks and deadlines, multiple service-specific opportunities, and their stage histories.
- Administrator and business-manager roles with server-side authorization and RLS.

### Explicitly deferred

- Automated website/annual-report research, batch AI reviews, and complex agent orchestration: **next candidate milestone** after measuring manual research bottlenecks.
- Public client portal, client data pipelines, customer-facing reporting, project-delivery management, invoicing, bookkeeping, payment processing, and email/calendar synchronization.
- Automatic lead scoring by opaque model, predictive purchase probability, automatic outbound emails, autonomous opportunity creation, auto-changing approved assessments.
- Complex customizable dashboards, drag-and-drop screen builder, or multitenant SaaS architecture.

**Note:** Deferred items should be anticipated in the information architecture, not built as empty production features.

## 3. Product information architecture

### Navigation

- **Overview:** upcoming and overdue follow-ups, active opportunities by stage, research/import review queue or status, direct links to urgent work.
- **Prospects:** shared Table / Map / Summary views, filters, profiles, bulk selection, shortlist.
- **Relationships:** contacts, interactions, assignments and next actions associated with organizations.
- **Opportunities:** service-specific opportunities, pipeline stages, value estimates where justified, next steps, owner, close outcome.
- **Settings** (administrator): users, permissions, system configuration, ingestion and screening-rule administration.
- **Future modules (not active in first release):** Clients, Projects, Finances, AI Research.

### Organization profile

1. **Organization:** legal/display names, EIN, location, website, NTEE/mission category where sourced, mission/program descriptions, source dates.
2. **Financials:** fiscal-year total revenue and expenses, annual surplus/deficit, operating margin, trend over observed years, balance-sheet fields where reliable, source filing link, calculation details, screen outcome and reason.
3. **Impact reporting:** existing reports, measures, suspected gaps, internal process notes when discovered, links to evidence; visually distinguish observed facts, hypotheses, and discovery-confirmed needs.
4. **Funding/grants:** public grants and funders when source-backed; reporting requirements only when explicitly evidenced, never inferred as definite from an award alone.
5. **Relationships/opportunities:** contact history, owners and tasks, separate opportunity records and stages; accessible from profile but not mixed with the organization's financial screening status.

### UX principles

- Match a **unified design system** derived from existing personal homepage and nonprofit solutions page: share typography, color tokens, controls, tables; keep branding replaceable when a new business name is chosen.
- Desktop-first for analysis, mobile-friendly for follow-ups; consistent sidebar, accessible contrast and keyboard navigation.
- Clearly label fiscal years, source update dates, missing values, and unreviewed/approved findings.
- Zero fabricated research summaries, metrics or financial figures; use explicit empty states.

## 4. Prospect qualification logic

### Initial filter and rules

- Primary target band: annual total revenue **$1M–$5M**; configurable, not hard-coded into records.
- Primary mission segmentation: source-derived mission/NTEE category, with manual corrections stored separately from raw values.
- Initial geographic scope: Greater Cincinnati and Greater Cleveland metro areas, including suburbs. **County lists and metro reference year require final approval before ingestion**; store counties in a configuration table, not application code.
- Financial facts: annual revenue, expenses, `surplus_deficit = revenue - expenses`, `operating_margin = (revenue - expenses) / revenue` when revenue > 0, multi-year year-over-year revenue changes.
- **Financial stability** is a documented, versioned ruleset considering multiple periods, revenue trajectory, and available balance-sheet information (when comparable). Do not treat one deficit year as automatic exclusion.
- Proposed screen results: `priority`, `needs_review`, `lower_priority`, with **reason codes**, source/fiscal year, and ruleset version.
- Financial **capacity to pay is an inference**, not a fact derivable solely from 990 filing totals. Do not equate positive net assets with unrestricted cash or willingness to spend.
- Pass/fail criteria and numerical rule thresholds must be calibrated against a manually checked sample; do not invent final thresholds before exploring the data.
- Allow administrator/manager manual review and overrides **without overwriting raw financial facts**; persist actor, reason and timestamp.

### Research need signals (human-led for first release)

Evaluate four potential reporting-need signals: (1) no public impact report readily found, (2) reporting mainly activities/outputs rather than measured outcomes, (3) fragmented/manual workflows revealed through discovery, and (4) documented funder reporting requirements. Each is `observed`, `inferred`, `confirmed`, or `unknown`; a missing website document is *not* proof that internal reporting is absent. Public financial/organization research precedes deep investigation.

## 5. Data sources and ingestion

- Start from official **IRS Exempt Organizations Business Master File (BMF)** for organization identities where suitable, and official **IRS Form 990 series and financial extracts** for year-specific facts. Preserve public-source links and exact source dataset/report versions.
- IRS official references:
  - Public datasets: https://www.irs.gov/charities-non-profits/public-disclosure-datasets-and-downloads
  - Form 990 XML downloads: https://www.irs.gov/charities-non-profits/form-990-series-downloads
  - Tax-exempt financial extracts: https://www.irs.gov/statistics/soi-tax-stats-irs-tax-exempt-organization-population-data
- **Do not confuse filing year with tax/fiscal year.** Use returns' tax-period fields. Handle multiple filings, amended returns, 990 versus 990-EZ/990-PF differences, duplicates, missing data, and stale filings explicitly.
- Use EIN for organization matching but support source ID, aliases and history; detect anomalous merges; do not assume organization name or mailing address is permanent.
- Maintain raw/staged and curated data layers or equivalents, along with import batch ID, source, loaded_at, fiscal period, parser version, and quality checks.
- Perform hybrid updates: manual CSV import and controlled scheduled refresh of reproducible source data. Do not crawl every nonprofit's site continuously.
- Store geocoded locations and geocoding provenance only when needed for map display; do not conflate headquarters locations with program service geography.

## 6. Suggested logical data model

**Core tables to implement as needed, not necessarily all at once:**

| Entity | Representative fields | Relationship |
|---|---|---|
| `organizations` | id, ein, legal_name, display_name, website, mission_category, address, lat/long, source | One organization, many records below |
| `organization_filings` | id, organization_id, tax_period_end, fiscal_year, form_type, original_return_id, amended_flag, source_uri, imported_at | Financial provenance, one per filing |
| `organization_financials` | filing_id, annual_revenue, annual_expenses, total_assets, total_liabilities, net_assets, missing_flags | Curated measures from filing |
| `screening_rule_versions` | id, effective_date, parameters_json, author, notes | Immutable/versioned screening logic |
| `screening_results` | organization_id, rule_version, classification, reason_codes, calculated_at, override_by, override_reason | Auditable assessment |
| `contacts` | id, organization_id, name, position, business contact details, source | Multiple contacts per organization |
| `relationships` | id, organization_id, status, owner_user_id, next_action_at | One organization can have a relationship independently of opportunities |
| `interactions` | id, organization_id, contact_id, actor, type, occurred_at, summary | Contact history |
| `tasks` | id, organization_id, opportunity_id (nullable), assignee, due_at, status, description | Follow-ups and assignments |
| `opportunities` | id, organization_id, service_type, stage, owner, value_estimate (nullable), next_step, created_at | Multiple opportunities per organization |
| `opportunity_events` | id, opportunity_id, from_stage, to_stage, changed_by, changed_at | Stage transitions/audit |
| `user_memberships` | user_id, role, active | Admin vs business manager |
| `import_runs` | id, source, initiated_by, started_at, finished_at, status, record_counts, error_summary | Operational observability |
| `audit_events` | id, actor_id, action, entity, entity_id, occurred_at, metadata | Security/review trail |

**Future AI research entities** (create only if/when research milestone is approved): `research_batches`, `research_jobs`, `research_sources`, `research_findings`, `finding_reviews`. Each finding should carry source citation/URL, reporting/publication date, collected_at, evidence excerpt/locator if permitted, observation/inference distinction, research-run ID, review status, reviewer and decision. Only approved research should affect accepted qualification summaries. Avoid fabricated numerical AI-confidence measures.

### Pipeline state separation

- `screening_results.classification` = financial / prospect screen, not sales status.
- `relationships.status` = connectedness / outreach status at organization level.
- `opportunities.stage` = specific possible paid engagement. Create only when there is a plausible service-specific project; an organization need not have any opportunity.

Suggested opportunity stages: `identified`, `discovery`, `proposal`, `negotiation`, `won`, `lost`, `deferred`. Relationship stages can include `not_contacted`, `contact_identified`, `contacted`, `engaged`, `inactive`.

## 7. Security, roles, and governance

- **Private application:** deny all unauthenticated access to portal records and server actions. A non-secret `.vercel.app` URL is not itself access control.
- **Administrator:** all authorized business operations plus user provisioning, configuration, permissions, ingestion/screening administration and security settings.
- **Business Manager:** nonprofit research, contact and relationship changes, opportunities and business operational financial records **when those modules are implemented**; cannot change user permissions, secrets, infrastructure, or screening rule implementations.
- Supabase Auth and **database-enforced RLS**; apply least-privilege database grants as well as policies. Check authorization on every server-side mutation and import endpoint; do not rely on hidden UI.
- Mandatory MFA for administrative access (and consider for manager); private repository; separate production/preview secrets; secrets never exposed to browser or committed to Git.
- Service-role keys bypass RLS and must remain server-only with narrowly scoped execution. Log administrative changes and manual financial-screen overrides.
- Dedicated Supabase project, dedicated Vercel project, dedicated private GitHub repository; do not reuse Greenspace Guardians or Hamilton County application credentials/data.
- Use public nonprofit material for initial prospect research. **No employee, donor, volunteer or client-provided confidential data** without separate approval, contractual authority, data boundaries and security review.
- No agent-initiated outreach, web publishing, payments, or destructive data modifications.
- Security docs: https://supabase.com/docs/guides/database/postgres/row-level-security
- Deployment environments: https://vercel.com/docs/deployments/environments

## 8. Technology and deployment approach

- **App:** Next.js (TypeScript), responsive app-shell with left sidebar, shared component library/tokens.
- **Hosting:** dedicated Vercel project at a temporary `*.vercel.app` deployment address (exact name subject to availability); custom business domain later.
- **Database/auth:** separate Supabase PostgreSQL + Supabase Auth + RLS; SQL migrations under version control.
- **Data processing:** Python for ETL and financial normalization, SQL for deterministic screening; run repeatable jobs with explicit logs/limits. Scheduling mechanism to be chosen once data volumes and execution constraints are measured.
- **Maps:** choose implementation after validating location data, licensing, and mapping effort. Use a single geocoded organization dataset for table and map.
- **AI research later:** manually approved bounded batches, cost caps, external-public-source-only scope, structured evidence, review queue, no autonomous outreach. Execution runtime and model/provider remain an implementation decision.
- **Deployment safety:** local development, preview/testing environment, explicit production promotion. Do not connect test workflows to private data by default.

## 9. Development milestones and two-gate decisions

### Milestone 1 — Data foundation

**Deliver:** Import pipeline; organization registry; IRS filing/financial history; first version of transparent financial rules; data-quality/reporting script.

**Technical acceptance checks**
- Re-running an import does not create duplicate organizations or tax-period records.
- Curated revenue, expenses, surplus/deficit and fiscal periods reconcile to a manually inspected sample of source filings; no unresolved critical identifier merges in the sample.
- Missing, conflicting, amended, and stale records are distinguishable, not silently filled.
- Rules are versioned, explainable, configurable and testable with known cases.
- County inclusion list and source/fiscal-year rules documented.

**Business-value gate**
- Produce a manually reviewable shortlist of real, financially plausible organizations within the selected geography.
- Record time/effort versus the manual baseline and whether the findings are credible enough to support real outreach.

### Milestone 2 — Prospect intelligence interface

**Deliver:** Authentication/RLS, sidebar/Overview shell, prospect Table/Map/Summary views with shared filters, individual nonprofit profiles, shortlist and organization-level assessment notes.

**Technical acceptance checks**
- Signed-out users cannot read data via UI or API; manager/admin policy tests pass.
- Table, map, and summary show consistent record counts and results for identical filters.
- Organization profile values show tax years, source links, and missing-data states; no fabricated research.
- Filtering for revenue range, financial status, mission and geography works and performs acceptably on realistic dataset size.
- Basic accessibility/responsive tests and error/empty-state tests pass.

**Business-value gate**
- Compare representative research tasks using the portal versus the manual method. Show actual reductions in time or better qualification accuracy; otherwise fix before expanding.

### Milestone 3 — Relationship and opportunity management

**Deliver:** Multiple contacts, relationship owner/status, interaction history, follow-up tasks and due dates, one-to-many opportunities with separate stages and stage change history, a home dashboard showing actionable tasks and pipeline.

**Technical acceptance checks**
- An organization has one canonical profile and can have zero, one, or many opportunities.
- Contacts, tasks and interactions are linked correctly; overdue tasks appear on Overview.
- Opportunity stage changes are retained with actor/time; won/lost/deferred are not conflated.
- Manager can perform business workflows but cannot alter permissions/configuration; direct API tests enforce restrictions.

**Business-value gate**
- Run a real outreach workflow without a parallel spreadsheet, and verify that the portal does not introduce substantial duplicate data entry or follow-up administration.

### Milestone 4 — 60-day field pilot

**Deliver:** Real-world use, comparison baseline, documented follow-ups/meetings, outcome review and prioritized roadmap.

**Technical acceptance checks**
- Core workflows remain operational, imports auditable, backups/recovery understood, incidents tracked, and account permissions verified.
- Research time and CRM events are measurable without requiring excessive manual logging.

**Business-value gate**
- Compare time per *credible qualified prospect* (not merely imported record), number of qualified outreaches, discovery conversations, specific needs confirmed, signs of willingness to pay, and operational overhead.
- Document **continue / revise / stop** decision. Set numerical pass thresholds from baseline and outreach capacity before starting the pilot; do not retroactively choose targets.

### Possible Milestone 5 — AI-assisted impact research (only if justified)

Batch-select a bounded set of nonprofits, approve scope/cost, research public reports/websites, produce source-linked structured findings, review at organization level with per-finding edit/reject controls, and add only accepted findings to profiles. Gate against manual research on both **time saved** and **error rate**. Do not create automated research jobs merely because they can be built.

## 10. Measurement plan

| Measure | Definition / caution |
|---|---|
| Research minutes per credible qualified organization | Count complete research and verification time; compare like-for-like organizations and tasks. |
| Qualification precision on reviewed sample | Human-confirmed viable prospects / AI/rule-prioritized prospects reviewed. The denominator is not all imported nonprofits. |
| Outreach effectiveness | Meaningful replies and qualified discovery conversations per organization contacted; do not overinterpret small samples. |
| Commercial validation | Confirmed reporting pain, budget or funding path, decision process, willingness to pay; a meeting alone is not validation. |
| Operational overhead | Time spent maintaining records/imports and reconciling data; subtract this from claimed time savings. |

## 11. Open decisions requiring explicit answers before corresponding work

1. **Exact geographic county lists** (Cincinnati and Cleveland metro reference definition/year), and treatment of organizations whose legal mailing address is outside the service region.
2. Initial permitted source coverage, date range, and financial-field priority; sample of organizations/forms for validation.
3. Thresholds for financial screening and what counts as an unacceptable false qualification.
4. Research and CRM data retention limits; contact data sourcing and permissible outreach practices.
5. Site branding asset source and authoritative CSS/color values from the current website(s); brand name can stay provisional.
6. Whether partner has formally approved portal access and what specific financial records they may see once finance modules are added.
7. Milestone pilot baseline and explicit numerical success thresholds, set *before* the 60-day evaluation begins.
8. Hosting subscription costs, backup/restore approach, and who maintains the service; confirm account ownership before any provisioning.

These are **implementation gates**, not reasons to build a larger application now.

## 12. Instructions for Codex / implementation agent

- Treat this specification as a **planning baseline, not a command to deploy**. Work on one approved milestone at a time.
- Before coding each milestone, propose: architecture changes, exact tables/migrations, acceptance tests, data provenance, security risks, known ambiguities, cost and rollback approach.
- Never access or copy existing client, donor, volunteer, employee, or personal project data; use synthetic fixtures unless explicitly authorized otherwise.
- Do not provision new paid resources, write production data, transmit sensitive data, change account permissions, or deploy to production without explicit approval.
- Prefer Python/SQL for data ingestion and deterministic screening; use TypeScript/Next.js for the app. Keep data access on appropriately authorized server routes and RLS-protected queries.
- Require tests for migrations, imports, idempotency, formulas, RLS and role restrictions, filter consistency, and workflow lifecycle.
- Commit small reviewed changes; surface dependency and security implications; document how to run locally and test acceptance criteria.
- Stop after meeting a milestone's acceptance criteria and present results for **technical readiness and business-value review** before starting the next one.

---

**Bottom line:** Build the smallest trustworthy system that improves nonprofit prospecting and follow-up. Expand it only when usage evidence—not feature enthusiasm—justifies the next investment.
