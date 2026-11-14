# 06 — User interface, navigation, design

**Status:** UX decisions approved conceptually; visual token values pending reference assets. **Milestones:** M02–M03.

## Requirements

- **UX-001** Use an authenticated, desktop-focused but mobile-usable shell with persistent **left sidebar** that collapses on narrow screens.
- **UX-002** Home page is **Business Overview**, with priority areas for upcoming/overdue follow-ups, real sales opportunities/pipeline, and research/import activity. Show only available functions as milestones ship.
- **UX-003** Prospects workspace offers **Table / Map / Summary** switchable views using the same server-backed filters, result set and selection state.
- **UX-004** Provide clear filtering on annual revenue band, financial stability category, revenue trend, mission, organization size, and geography. Financial capacity is a rules explanation, not an unexplained slider or scalar score.
- **UX-005** Table view supports sortable/filterable nonprofits, financial period and status indicators, and links to organization profiles. Use pagination/server filtering on realistic datasets.
- **UX-006** Map view plots the **same filtered organizations** with grounded locations and clear unknown/approximate-location states. Never portray HQ points as geographic service coverage.
- **UX-007** Summary view presents interpretable breakdowns of the currently filtered set; counts must agree with Table and Map scope, including unmappable records explicitly.
- **UX-008** Profiles use distinct Organization, Financials, Impact reporting, and Funding/grants sections, with Contacts/Opportunities when M03 is released.
- **UX-009** Reuse a unified **brand-neutralizable** visual system derived from the current homepage and nonprofit consulting page. Extract actual color/typography assets before coding; do not invent the 'official' palette.
- **UX-010** Show loading, no-result, missing-data, stale-data, unreviewed-evidence, error, and unauthorized states. No fake dashboard metrics in production.
- **UX-011** Meet baseline keyboard usability, accessible labels/contrast, sensible mobile task access, and consistent date/currency formatting.

## Navigation at first complete workflow

`Overview` · `Prospects` · `Relationships` · `Opportunities` · `Settings` (admin-only). Future `Clients`, `Projects`, `Finances`, and `AI Research` are not active empty pages.

## UX consistency contracts

- Shared URL-serializable filters when practical, or clearly defined query state; changing Table ↔ Map ↔ Summary must preserve filters.
- Show both filtered total and mapped subset when some organizations lack a valid location.
- All revenue/financial numbers indicate selected fiscal period and latest available source date.
- Prefer action-oriented cards over vanity metrics.
