# Restricted connection setup preflight and evidence — 2026-11-21

## Decision and scope

READY FOR IMPLEMENTATION for the requested local setup artifacts, optional driver
installation and synthetic tests. Mark requested restricted connection setup after
commit/push and explicitly agreed to hidden prompts rather than environment vars.
Read-only safety review preceded implementation. Permission mode: Ask for approval.
M01 SEC-003/006, DAT-012 and ARC-005, partial; no milestone release.

Live prerequisites are user-supplied public CA and user-entered credentials, not
agent collection of secrets. User will run the guarded setup/probe, as with prior
manual cloud actions. The agent must not read environment passwords or launch the
password helper/probe against Supabase. No browser control, import or scope setup.

## Objective and success

Configure existing nb_loader_dev without widening its grants, set a password through
a hidden local prompt, activate a one-hour validity window and prove the actual
session uses verified TLS/password authentication, correct role and read-only access.
Success must include zero imported records and no direct table/admin/create access.

## Tools, data and minimum permissions

| Capability | Access / duration / purpose | Authority |
|---|---|---|
| Optional driver | Pinned psycopg[binary] 3.3.9 in existing venv, locked dependency | Requested connection implementation |
| CA | User downloads public certificate for this project, ignored local storage | No private key or secret needed |
| Password helper | User-run temporary cached PostgreSQL client; owner session only for fixed role password | Requested setup; passwords hidden and never passed to agent |
| Activation | User-run owner SQL; fixed role, guarded existing policy/ACLs, one-hour password expiry | Concrete reviewable setup; no new grants |
| Probe | User-run nb_loader_dev connection, fixed pooler, read-only metadata, ten-second connection/query bounds | Connection verification only |
| Local evaluation | Isolated network-none PostgreSQL 17.12 and fictional roles | No external credentials/data |

## Prohibited actions and approval gates

No environment/password/DSN logging, secret files/fixtures, raw ALTER PASSWORD
literals, TLS fallback, new grants/roles, disk/policy expansion, scope/capacity seed,
data load, automatic retry/renewal, browser access or production action. Environment
variables are readable by processes that inherit them; they are not a secret boundary.

| Trigger | Approver / preview | Boundary |
|---|---|---|
| Password and LOGIN setup | Mark requested setup; reviews fixed helper/SQL and enters credentials himself | Only nb_loader_dev in named dev project; cancel before operator execution |
| Agent use of credentials | Mark; named access and secret-handling method | Not approved or needed here |
| Thirteen-record cloud import | Mark; exact plan, scope/settings, fresh capacity and live verification | Separate batch approval; setup alone is insufficient |
| Recovery involving sessions/data | Mark; active-state read-back and exact recovery | No automatic termination/deletion/reset |

## Failures, containment and recovery

| Failure | Detection / containment | Recovery |
|---|---|---|
| Missing/untrusted CA or TLS mismatch | verify-full; no downgrade | Stop; confirm certificate/host, no secret output |
| Wrong owner/role/project metadata | Fixed host/users and SQL project/disabled-role guards | Stop before changing password/activation |
| Extra memberships/table/schema privileges | Activation/probe fail closed | Review ACLs; no silent revocation or grant widening |
| Password prompt cannot be hidden | Noninteractive/echo fallback blocked | User runs in own interactive terminal |
| SQL/connection failure or uncertain outcome | Transaction rollback / sanitized error; no retry | Read back role status before another setup attempt |
| Expired window | Authentication/probe rejects | Close clients; separately authorized new window only |

Recovery for new logins is owner ALTER ROLE nb_loader_dev NOLOGIN. Existing sessions
are not killed by NOLOGIN or password expiry; probe closes its own session. No data
rollback applies. Local code/dependency changes may be reverted without touching
source snapshots or cloud records; no automatic package uninstall.

## Tests and actual evidence

- Seven synthetic probe tests: pinned endpoint/verified TLS/read-only options,
  missing certificate, successful metadata-only probe with rollback/close and no
  commit, missing TLS, wrong role/expired window/extra privilege, noninteractive
  rejection, sanitized driver failure without retry. Full Python suite 82 passed.
- Password helper passes PowerShell parser validation; never executed with real
  credentials. Pinned driver installed, libpq 18.4 available, lock updated. No
  environment secret read, owner password, new password or Supabase connection.
- Network-none PostgreSQL 17.12 fixture: extra direct SELECT blocks activation;
  after revocation activation passes; actual nb_loader_dev session executes probe
  SQL read-only with expected metadata; NOLOGIN recovery passes, import count zero.
  This does not validate hosted TLS/password auth (local fixture uses socket trust).
- Local test container inspected and removed. User downloaded public CA and executed
  operator setup. Hosted probe executed successfully: `restricted_connection_verified`,
  `tls_in_use=true`, `sslmode=verify-full`, `password_auth_used=true`, `records_imported=0`.
  Metadata verified role `nb_loader_dev`, `read_only=true`, `can_execute=true`, and all 13
  administrative, table-access, and membership checks `false`. Role subsequently returned
  to `NOLOGIN`. Zero records imported. Live thirteen-record import remains gated.
- Existing 33 hosted filings remain untouched by the agent.

## Sources, unresolved risks and next safest step

[Supabase psql/CA guide](https://supabase.com/docs/guides/database/psql),
[Supabase connection modes/custom role naming](https://supabase.com/docs/guides/database/connecting-to-postgres),
[PostgreSQL psql password command](https://www.postgresql.org/docs/17/app-psql.html),
[Psycopg installation](https://www.psycopg.org/psycopg3/docs/basic/install.html).

User must download the correct public CA, review/run the operator steps, then return
only sanitized probe metadata. Live password/TLS/Supavisor compatibility is not yet
verified. This setup does not assert a server SSL-enforcement setting or change it.
Scope/capacity and a live thirteen-record run need separate evidence/approval.
See ../tasks/loader-connection-setup.md for exact commands and recovery.
