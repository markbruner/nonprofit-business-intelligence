# Restricted development connection — operator steps

Target: nonprofit-business-intelligence development project `yxtslaaboriakfvpeedi`.
Mark requested this connection setup and chose hidden password prompts instead of
environment variables. The agent has not used credentials or connected to Supabase.
These steps configure/test a connection only: no scope/capacity change or import.

## 1. Download the public CA certificate

In this project's Supabase dashboard, open Database Settings -> SSL Configuration
and Download Certificate. Save it as:

`C:\Users\markd\github\nonprofit-business-intelligence\data\connection\supabase-ca.crt`

This is a public trust certificate, not a password/key. Do not disable certificate
validation if the connection fails. The scripts use the approved session-pooler
host `aws-1-us-east-2.pooler.supabase.com`, port 5432, database postgres.
See [Supabase SSL connection instructions](https://supabase.com/docs/guides/database/psql)
and [custom-role/session-pooler naming](https://supabase.com/docs/guides/database/connecting-to-postgres).

## 2. Set the dedicated loader password securely

From your own PowerShell terminal in the repository root, with Docker Desktop running:

```powershell
./scripts/set_loader_password.ps1 -CaCert ./data/connection/supabase-ca.crt
```

The helper uses the cached PostgreSQL 17 client in a temporary, read-only container
with the public certificate mounted read-only. It makes one owner connection to the
named dev pooler, checks the target and disabled role, and runs only password setup.
No image pull, scope/grant/data change or import. It prompts for:

1. The existing **project database password**, for `postgres.<project-ref>`.
   This is not your Supabase account password or publishable/API key.
2. A distinct new `nb_loader_dev` password, twice. Generate/save it in your password
   manager yourself; the agent does not receive it. LOGIN stays disabled at this step.

The helper uses psql `\password` with SCRAM encryption and disables client history.
PostgreSQL documents this as avoiding cleartext password exposure in command history
and server logs: [psql password command](https://www.postgresql.org/docs/17/app-psql.html).
Do not put passwords in command arguments, SQL literals, environment variables,
files or chat; do not record/transcribe this terminal. A hidden prompt reduces
incidental exposure, but is not isolation from other processes under your account.
If it errors, share only the error category; do not activate or retry blindly.

## 3. Activate a one-hour login window

Review `supabase/setup/loader_login_activation.sql`, then run the entire script
in this development project's SQL Editor. It refuses unexpected role/membership/
schema/table privileges or policy, enables LOGIN and sets password validity to
one hour from execution. It adds no grants and changes no storage limits or data.
Expected output: nb_loader_dev, login_enabled=true, connection_limit=1 and a
future password_valid_until. Share that metadata if needed; never the password.

Expiry prevents new password authentication; it does not terminate sessions already
open. A `NOLOGIN` role also needs explicit reactivation after any later recovery.
Only run a new window as part of separately authorized setup, never auto-renew it.

## 4. Test the actual restricted connection

The optional pinned driver is already installed in this workspace. On a fresh
checkout install it with `uv sync --extra loader`.

```powershell
./.venv/Scripts/python.exe -m scripts.check_loader_connection --ca-cert ./data/connection/supabase-ca.crt
```

Enter only the **loader password** at the hidden prompt. The probe pins the role,
host/port/database, certificate/hostname verification, read-only transactions and
timeouts, and disables prepared statements. It rejects password-echo fallback or
noninteractive operation. It reads only metadata, rolls back and closes; no import
function is called. TLS and password authentication must both be in use.

Expected result: restricted_connection_verified, tls_in_use=true,
password_auth_used=true, sslmode=verify-full and records_imported=0. The returned
metadata must show nb_loader_dev, read_only=true, can_execute=true and all direct
table/admin/create/SET/executor/owner access false. Share only this JSON result.
The probe prints error type only and never retries or prints a DSN/driver message.

## Recovery and next step

To block new connections, use the owner SQL Editor:

```sql
alter role nb_loader_dev nologin;
```

Close the probe/any client yourself. NOLOGIN/expiry do not forcibly terminate an
existing session. No row deletion or down migration is needed for this setup.
Do not reset the project, widen privileges or disable TLS to fix a failed probe.

The thirteen-record 2023 import remains unapproved. Before loading: verify live
counts, review its exact plan, seed its specific EIN scope as owner, refresh full
capacity evidence and approve the named batch. This setup does not perform those
steps or authorize automatic refreshes, uploads or future credential use by the agent.
