# Requirement-to-test matrix

This is a **test plan**, not a claim that tests have been written or passed. Add actual test paths and results as code is created.

| Milestone | Requirements | Minimal verification | Status |
|---|---|---|---|
| M01 | DAT-002–DAT-005, DAT-007–DAT-008 | Idempotent import; EIN alias/collision; source tax periods; amendment selection; missing-vs-zero handling | NOT RUN |
| M01 | DAT-001, DAT-006, DAT-009–DAT-011 | Source metadata, manual import validation, county config, geocoding provenance, failed-run integrity | NOT RUN |
| M01 | SCR-001–SCR-005 | Revenue band, surplus, margin guard, trend gaps, mission corrections | NOT RUN |
| M01 | SCR-006–SCR-010 | Versioned deterministic rules, reason codes, override audit, no pipeline contamination | NOT RUN |
| M02 | SEC-001–SEC-007, SEC-009, SEC-011 | Signed-out/manager/admin/inactive DB+API authorization and secret exposure tests | NOT RUN |
| M02 | RES-001–RES-009 | Profile fields and source citations; manual observed/inferred/confirmed; no fabricated grants/outcomes | NOT RUN |
| M02 | UX-001, UX-003–UX-011, ARC-007–ARC-008 | Table/map/summary same filters/counts, unmappable records, empty/errors, keyboard/mobile tests | NOT RUN |
| M03 | CRM-001–CRM-004 | Multiple contacts, relationship without opportunity, dated interactions | NOT RUN |
| M03 | CRM-005–CRM-006 | Due/overdue tasks by assignee and timezone, overview actions | NOT RUN |
| M03 | CRM-007–CRM-012 | Two opportunities per org, independent stages, stage audit and manager permissions | NOT RUN |
| M03 | UX-002, SEC-002–SEC-004, SEC-014 | Dashboard real data; manager capabilities vs admin restrictions | NOT RUN |
| M04 | PIL-001–PIL-009, ARC-009–ARC-011, SEC-012 | Pilot metrics, reproducible baseline, security/account audit, recovery review | NOT RUN |
| Possible M05 | AIR-001–AIR-010 | Public source constraints, bounded costs, review workflow, factual error audit | DEFERRED |

## Report actual execution per task

- Test ID or path:
- Requirement ID(s):
- Input fixtures/source reference:
- Expected result:
- Actual result:
- Run command and environment:
- Status (PASS / FAIL / BLOCKED):
- Known limitations:

Do not claim an end-to-end release is verified merely because one unit test passes.
