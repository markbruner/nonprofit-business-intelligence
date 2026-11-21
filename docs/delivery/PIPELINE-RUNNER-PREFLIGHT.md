# Repeatable local runner and injected loader — 2026-11-21

## Decision and scope

READY FOR IMPLEMENTATION for local preparation and synthetic injected-connection
tests. Mark approved the proposed runner after the 2023 coverage checkpoint.
Read-only preflight preceded implementation. Permission mode: Ask for approval.
M01 DAT-003/005/006/007/008/011/012/013 and ARC-005, partial; no milestone advance.

This first runner is explicitly tax-2023 and uses existing approved snapshots and
the January archive. It is not a nationwide/backfill/scheduled downloader. Users
are Mark and a future approved restricted loader caller in the dedicated dev project.
Public IRS facts/provenance only; no private/client/employee/donor records.

## Objective and success criteria

One offline command performs source selection, extraction, direct field checks,
quality/year validation and preparation of deterministic batches of at most thirty
records / 64 KiB estimated JSONB text. Preserve original discovery evidence. A
separately invoked API loads one reviewed batch through the existing DB function.
No automatic retries or skipping failed batches. A changed plan/payload/evidence
must stop before touching a connection. SQL policy/scope/fresh capacity remain the
authority; caller-side limits cannot widen them.

## Tools, data and minimum permissions

| Capability | Access / scope / duration | Approval |
|---|---|---|
| CLI preparation | Read approved local sources; new ignored package for this run | Mark's implementation instruction |
| Artifact publication | Exclusive JSON writes; plan last as completion marker | Reversible local preparation |
| Injected execution API | One idle, non-autocommit restricted DB-API connection; existing function only | Implementation/tests approved; live use NOT approved |
| Credentials/transport | None created/read; no driver installed or connection opened | Separate concrete connection approval required |

The plan names the dev project reference. It does not independently authenticate
the supplied connection's remote identity: a future caller must bind it to the
approved endpoint with verified TLS and restricted identity. No browser access.

## Prohibited actions and human gates

Never create a connection, read an environment secret, activate LOGIN, widen
permissions/budgets, refresh capacity as the loader, seed scope as the loader,
download, upload without approval, run the whole plan automatically, or retry a
commit with an uncertain outcome. Do not print driver exceptions, DSNs or facts.

| Trigger | Approver and concrete evidence | Scope / expiry / cancellation |
|---|---|---|
| Live connection/LOGIN/credential use | Mark; named restricted dev identity/endpoint, secure local setup and recovery | Separate approval; no secrets in chat; stop before activation |
| Scope/capacity and 13-record cloud load | Mark; reviewed plan digest, payload, owner-only settings, fresh full disk measurements, execution evidence | Fixed batch/target; changes invalidate approval; cancel before execution |
| Retry after uncertainty / post-commit deletion | Mark; read-only server receipt/state and recovery proposal | No automatic replay, deletion or down migration |

## Failure modes and recovery

| Failure | Detection / containment | Recovery |
|---|---|---|
| Wrong year or quality finding | Validate complete parent first; reject before partition/publication | Preserve source/report; review, no waivers |
| Large input/payload | Bounded reads; split under thirty/64 KiB; reject oversized single filing | Review smaller source work; never silently discard |
| Changed package/path escape | External reviewed plan digest plus canonical staging/payload/evidence hashes and path bounds | Stop before cursor call; regenerate/review if intended |
| Existing/partial output | Exclusive publication; plan last | Inspect; choose new directory, preserve input/earlier runs |
| DB denial/stale/missing capacity/over-budget | Existing function enforces and load_batch rolls back | Sanitized error; owner diagnoses and refreshes evidence |
| Lost response/commit connection | No retry, fixed sanitized error | Commit may have succeeded; inspect server state before resubmission |
| Successful batch, later batch fails | One explicit batch/transaction per API call | Earlier committed batches stay intact; no blind all-plan replay |

Local rollback: revert new runner/refactor/docs and remove only its ignored new
package after review. No cloud rollback is needed for this task. Future successful
cloud deletion requires separate approval and restore planning.

## Tests and evaluation evidence

Eight new synthetic tests: deterministic thirty/one splitting, payload-based
splitting/oversized singleton, unknown/wrong year and quality rejection, identical
explicit resubmission payload, changed plan/staging/evidence, server denial,
uncertain commit, autocommit and path-traversal rejection. No client retry occurs;
server failures roll back once, commit uncertainty is surfaced without driver text.
Prior hosted SQL tests established DB idempotency/capacity gates; these API tests
use mocks and do not establish live authentication/driver compatibility.

Full Python suite: 75 passed. Formatting/whitespace checks pass. The local runner
produced data/irs-tax2023-pipeline-20261121-02/ with one thirteen-record batch and
plan digest 4ace4f3b312512916af5b498c9d7e3d8eed5e1141a905e572cb02f4be0f36615.
Actual source evidence remains 91 direct checks, OH 4 / KY 2 / IN 7, one amended
filing. Payload digest 006d06363a8aee6fe49eb91867c292f3c2ac0bd7c196d8a4a9c8dbecb44032a2
is the local canonical payload digest, NOT the database JSONB run key. Comparison
with local copies of the thirty-three imported records shows thirteen distinct
new EINs, no existing filing keys or EIN/period collisions; live state still needs
verification. No cloud access or downloads occurred. LOGIN remains disabled.

## Unresolved risks and next safest step

No credential configuration, live DB driver, authenticated Python run, full-history
coverage or complete failed-run/timing audit is implemented or verified. The live
loader cannot set scope/capacity and must fail until owner settings are approved.
Existing capacity observations will need refreshing before any live batch. Keep
the current thirty-row/1.5 GB stop/256 MiB reserve and other safeguards unchanged.

Review the prepared package and decide the concrete restricted connection and
owner-only scope/capacity setup before asking for any live run. Neither technical
nor business milestone gate is passed; this is local readiness evidence only.
