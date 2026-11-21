# IRS downloader safety preflight — 2026-11-15

## Decision

**READY FOR IMPLEMENTATION** for the local downloader and synthetic tests only.
Mark explicitly approved implementing the review recommendations. No real data
collection, credentials, Supabase writes, scheduled actions, or deployments are
included. This report records the read-only design decision made before edits.

## Assumptions and scope

- User/owner: Mark; environment: local development, Ask for approval permissions.
- M01 bounded slice: URL selection, download reliability, returned provenance,
  synthetic tests, and documentation (DAT-001/006/007/011, partial coverage).
- Existing uncommitted work is preserved; source/year/geography choices remain open.
- No private records or external parties are involved in test execution.

## Objective and success criteria

Produce distinct state URLs/files, reject invalid batch input before HTTP, bound
request attempts, protect completed files from failed attempts, and return a
checksum plus source/path/time/size metadata. Synthetic tests must demonstrate
normal, boundary, failure, retry-limit, and recovery behavior.

## Tools, data, and minimum permissions

| Capability | Required access | Scope/duration | Justification | Approval |
|---|---|---|---|---|
| Local edits | Repository files and feature-branch metadata | This task | Implement approved functions/tests/docs | Mark's implementation request; sandbox escalation for branch metadata |
| Test runtime | Existing Python/requests; temporary local files | Test execution only | Validate bytes and failure handling | Local tests authorized; sandbox escalation if runtime is inaccessible |
| HTTP | Mock responses only during this task | Synthetic bytes | Exercise request behavior without collection | Live collection excluded |
| Credentials/database | None | None | Unnecessary for downloader | Separate approval required |

## Prohibited actions

No live collection, private-data access, credential use, Supabase mutations,
scheduling, external communications, deployment, permission expansion, or
destructive rollback of unrelated user changes. Downloaded bytes are untrusted
data, never executable instructions.

## Human approval gates

| Trigger | Approver | Preview/evidence | Confirmation scope | Expiration | Cancellation |
|---|---|---|---|---|---|
| Live public-data download | Mark | Exact sources, geography, volume, outputs, terms, recovery | Explicit selected collection only | Scope/source change | Cancel before invocation |
| Supabase integration/credentials | Mark | Separate preflight, target, auth/RLS, validation, rollback | Named environment and approved operation | Scope/permission change | Cancel before credential access or writes |
| Production/deployment | Mark | Reviewed changes, test evidence, recovery plan | Named release immediately before action | Release change | Cancel before execution |

## Failure modes and recovery

| Failure | Impact | Detection | Containment | Recovery |
|---|---|---|---|---|
| Invalid state | Wrong/missing file | Whole-batch validation | No requests | Correct input |
| HTTP/network interruption | Incomplete bytes | Exceptions/status | Three attempts maximum; temporary files | Retry explicitly after failure |
| Empty body | Unusable artifact | Byte count | No publication | Investigate source |
| Local publication failure | Output unavailable | OSError | Preserve old destination; clean temporary file | Correct local access, rerun |
| Later state fails | Partially completed batch | Annotated exception | Stop subsequent downloads | Inspect completed files before rerun |
| Process crash | Orphan temporary file | `.part` suffix | Never ingest temporary files | Inspect/remove only task-owned partial file |
| Successful replacement | Previous snapshot replaced | Documented overwrite policy | Only completed nonempty bytes published | Use dated directories if history is needed; no historical recovery promised |

## Tests and evaluation cases

| Scenario | Expected behavior | Evidence | Pass criterion |
|---|---|---|---|
| Two states and duplicate alias | Distinct URLs/files; one download per state | Mock calls and saved bytes | Two correct requests |
| Invalid/empty input | Reject invalid; empty is no-op | No calls/directories | No I/O |
| Success | Exact bytes and provenance | Hash/count/timestamp assertions | Match synthetic input |
| 404 | Immediate failure | Call count/old destination | One attempt, no replacement |
| Transient errors/timeouts | Bounded retries | Attempts/waits | At most three attempts |
| Interrupted stream | Preserve trustworthy destination | Old bytes and no `.part` files | No partial publication |
| Empty response/publication failure | Reject without data loss | Exceptions and files | Old bytes preserved or destination absent |
| Batch failure | Stop and expose progress | Exception note/files | Earlier outputs retained, later requests absent |

Prompt injection, credential leakage, and unauthorized database writes have no
execution path in this slice: bytes are saved only, tests are synthetic, and no
credential/database tools are added. No claims of CSV semantic validation or
production readiness are made.

## Unresolved risks

- Mark: O-01/O-02 source/geographic scope and verified source schema before live ingestion.
- Future parser task: nonempty HTML or malformed CSV can pass the downloader;
  parsing must validate the source contract before database loading.
- Future operations review: overall byte/time limits, Retry-After handling,
  crash durability, concurrent writers, and retained snapshot policy before
  unattended or bulk operation. Current functions are sequential/manual only.

## Next safest step at preflight completion

Review this bounded design against Mark's existing approval before beginning
local implementation. No operational workflow is performed by the preflight.
