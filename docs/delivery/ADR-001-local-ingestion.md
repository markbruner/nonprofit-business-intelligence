# ADR-001 — Restricted ingestion staging

Status: Implemented locally; cloud execution pending owner review.

Context: M01 needs repeatable full-990 imports with provenance and a disk admission
gate. Mark approved local schema/loader work on 2026-11-21 and clarified that the
star schema belongs in the reporting mart. Candidate geography is OH/KY/IN.

Options considered: browser/API writes using a broadly privileged key; direct
loader table mutations; one restricted database function with owner-managed scope
and storage policy. The function interface was selected for the local draft so
the caller cannot bypass admission checks through ordinary table writes.

Chosen design: private ingestion schema, stable internal organization IDs, typed
filing observations with integrity hashes, per-run provenance, forced RLS and a
non-login function owner without BYPASSRLS. A separate non-login ingestion role
has execute-only access. A future approved login receives only that role. Owner
configuration is separate from the loading interface. Reporting fact selection,
dimensions and star-shaped views are deferred, not scaffolded.

Security/cost: no service-role key, credentials or browser access; no raw XML in
the database. Missing scope/policy/fresh measurements blocks writes. Estimated
growth plus reserve must fit below the approved threshold and provisioned disk.
This cannot guarantee provider billing or contain unrelated writers.

Recovery: atomic transaction; identical payload receipt on retry; changed facts
require review. Empty-target down migration and reapplication tested locally.
Nonempty destructive recovery requires export/restore review and explicit approval.

Evidence: `TEST-MATRIX.md` and `../../supabase/README.md`. Local PostgreSQL tests
simulate standard Supabase roles; cloud-managed grants, concurrency, lost-COMMIT
outcomes and real calibration remain unverified.

Requirements: DAT-002/003/005/007/008/011/012/013, SEC-003/006, ARC-003/005/009.
Approval: Mark authorized local implementation only, 2026-11-21. No cloud execution,
real collection, permissions provisioning or budget increase is authorized.
