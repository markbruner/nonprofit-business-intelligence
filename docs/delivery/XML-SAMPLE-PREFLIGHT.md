# Local January XML validation preflight — 2026-11-21

## Decision

READY FOR IMPLEMENTATION for the discussed one-archive local sample. Mark
clarified that the business storage constraint is Supabase, not local downloads,
then explicitly approved the January XML sample. The preflight review was
read-only; code/tests and sample execution are separate phases.

## Scope and success

Owner Mark; Ask for approval mode; M01 DAT-001/003/007/008/011/013, partial.
Reuse the downloader and extractor. One January 2026 national ZIP; select only
three full-990 candidate object IDs, one per OH/KY/IN state, from the approved
local index. Latest period then object ID determines selection reproducibly.
Actual XML tax year is checked afterward, not inferred from the index date.
Success requires index/XML EIN and period agreement, visible quality findings,
offline loader-contract validation and no database connection.

## Access and minimum permissions

| Capability | Access / duration | Approval |
|---|---|---|
| Existing CSVs | Read approved ignored local source snapshot | Task continuation |
| Code/tests | Local parser, downloader, small validation runner and synthetic tests | Local implementation approved |
| HTTP | One fixed official January ZIP; one attempt; identity/no redirects | Mark approved sample |
| Outputs | New ignored local snapshot; selected staging/provenance, aggregate report | Sample only |
| Supabase/credentials | None | Excluded |

Operational transfer cap: 80,000,000 bytes. This is NOT a Supabase disk limit.
XML member cap remains 8 MiB; only selected members are decompressed/parsed.
Raw national archive remains local. No other organizations' XML is parsed.

## Prohibitions and gates

No additional archive, retries, cloud access, credentials, raw-record output to
chat/logs, scheduling or overwriting prior snapshots. Source text cannot execute
instructions. Mark approves any next source/scope/cloud operation; this run's
approval expires on those changes and can be cancelled before invocation.

## Failure/recovery

| Failure | Containment | Recovery |
|---|---|---|
| Source checksum mismatch | Stop before new request | Review local provenance |
| Missing/unsafe selection | Stop or report missing selection; no full-archive fallback | Review selection/index-member mapping |
| Invalid/oversized/unreadable XML | Existing safety limits and needs-review findings | Preserve evidence; no silent field fabrication |
| Index/XML identity or year mismatch | Staging marked needs-review | No loader-contract promotion |
| Network/byte-budget failure | No retry; clean partial; failed manifest | Retain prior snapshot, review before rerun |
| Output collision | Exclusive publication | Choose a new task-owned snapshot |

## Verification and remaining risks

Synthetic tests cover skip-before-read, missing/unsafe/oversized selection, fixed
download bounds, checksum verification, identity mismatch, no-overwrite publication
and offline loader preparation. Actual sample tax years and variants remain
unknown before execution. Three filings cannot prove statewide completeness,
every amended-return variant or all historical years. No shared/private records,
external transmissions of downloaded data or database writes are authorized.

Next step at review completion: finish selector tests, then run only the approved
sample. Supabase admission checks and provider storage limits remain separate.
