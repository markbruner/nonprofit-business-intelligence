# 03 — Financial screening and prospect priority

**Status:** Framework confirmed; numeric thresholds not yet calibrated. **Milestone:** M01.

## Requirements

- **SCR-001** Provide configurable annual revenue target band, initially $1,000,000–$5,000,000; show reporting year, form, and data freshness.
- **SCR-002** Compute `surplus_deficit = revenue - expenses` for comparable periods; retain source values and derived results separately.
- **SCR-003** Compute `operating_margin = (revenue - expenses) / revenue` only when revenue is known and >0; otherwise classify metric as missing/not computable.
- **SCR-004** Compute year-over-year revenue change and show a multi-year trend (ideally 3 tax periods when available). Do not hide nonconsecutive or missing years.
- **SCR-005** Support source-derived mission/NTEE filtering and separately recorded, attributed manual mission corrections.
- **SCR-006** Use a deterministic **versioned financial screening ruleset** considering trends, margins and available comparable balance-sheet measures. Do not invent final decision thresholds prior to sample validation.
- **SCR-007** Return one of `priority`, `needs_review`, `lower_priority`, accompanied by reason codes, timestamp, and ruleset version. Incomplete data must not silently become a negative result.
- **SCR-008** Support authorized human override/review with actor, timestamp, rationale, and old/new result. Raw finance and prior computed result remain unchanged and auditable.
- **SCR-009** Treat **financial capacity to purchase consulting** as an inference/qualification judgment; surplus, assets, reserves, and positive net assets are not proof of unrestricted budget or willingness to pay.
- **SCR-010** Keep financial screen outcomes distinct from impact-reporting need assessments, relationship stages, and sales opportunity stages.

## Data contracts / behavior

- Parameters live in a versioned record (`screening_rule_versions` or equivalent); no silent edits to past rules.
- Results link to exact filing selection and rule version; recalculating creates a reviewable history.
- Positive and negative reason codes are readable in organization profiles and filters.
- An admin configures rule versions; authorized manager may record case-specific override with a reason but cannot alter the rule implementation.

## Acceptance examples

| Input | Expected behavior |
|---|---|
| Revenue 0 or missing | Margin unknown; no divide-by-zero |
| Revenue $1.5M in the selected reporting year | Passes the **size** band only; financial-stability decision still separate |
| Single-year deficit | No automatic exclusion solely for that reason |
| One missing tax year in 3-year window | Trend labels gaps, not a manufactured annual change |
| Ruleset changed | Prior screening results remain attributable to their original version |
| Manual override | Review reason and actor preserved; original computed classification not overwritten |

**Approval needed:** thresholds, filing-selection conventions, financial field comparability, sample review process, unacceptable false qualification rate.
