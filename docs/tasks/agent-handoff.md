# Codex -> Gemini / Antigravity handoff — 2026-11-21

## Open this exact working folder

`C:\Users\markd\github\nonprofit-business-intelligence`

Branch: feature/irs-downloads. Prior runner checkpoint: 1e1b764. Connection setup
and this handoff are versioned together in the subsequent owner-requested checkpoint.
Start with git log and git status; preserve any existing local changes. Ignored
IRS packages and the local virtual environment are not supplied by a fresh clone.
No need to install a Gemini API integration or create any cloud resource for this
handoff. Sign in/select Gemini in Antigravity yourself if necessary. Account/model
availability is separate from Codex's usage allowance and is not guaranteed here.

Official references: [Antigravity getting started](https://antigravity.google/docs/getting-started)
and [workspace rules](https://antigravity.google/docs/rules/). Root AGENTS.md and
GEMINI.md carry project instructions; no global account/settings files were edited.

## Read first

1. README.md, AGENTS.md, GEMINI.md.
2. docs/tasks/loader-connection-setup.md — exact operator instructions.
3. docs/delivery/RESTRICTED-CONNECTION-PREFLIGHT.md and PIPELINE-RUNNER-PREFLIGHT.md.
4. docs/requirements/02-data-ingestion.md, INDEX.md, and current entries in
   docs/delivery/DECISIONS.md, TEST-MATRIX.md and MILESTONES.md.

Do not read the archived original specification without a concrete requirement
conflict. Do not load raw ignored data or secrets into the model for orientation.

## Verified state

- Dedicated dev Supabase ref yxtslaaboriakfvpeedi; session pooler
  aws-1-us-east-2.pooler.supabase.com:5432, database postgres.
- Mark manually ran schema/role/policy and two public IRS trials. Last returned
  hosted counts: 33 organizations, 33 filings, 2 import runs, 33 provenance links.
  Loader was NOLOGIN. No agent has connected to Supabase or used a real password.
- At 17:29:55 UTC: DB 11,622,067 bytes, WAL 83,886,444, ingestion relations 352,256.
  These are HISTORICAL, not fresh capacity evidence for a future load.
- Persisted policy: max_rows 30; stop 1,500,000,000; reserve 268,435,456; max age 900s;
  payload 65,536; growth max(4x JSONB bytes, 65,536/filing); tax years 2023–2025.
  Keep all these unchanged. Raw archives stay outside Supabase.
- Local 2023 check: 13 actual TaxYr=2023 filings, OH 4 / KY 2 / IN 7, version
  2023v6.0, 91 direct source checks pass, one amendment. No completeness claim.
- Local runner prepared one 13-record package at
  data/irs-tax2023-pipeline-20261121-02/; plan digest
  4ace4f3b312512916af5b498c9d7e3d8eed5e1141a905e572cb02f4be0f36615.
  Its plan/payload hashes bind review; local canonical payload hash is not the DB
  JSONB run key. The 13-record import is NOT approved or performed.

## Current local connection implementation

- pyproject.toml optional loader dependency and uv.lock: psycopg[binary] 3.3.9.
  Installed in existing .venv; libpq 18.4. uv lock --check --offline passes.
  First sandbox lock check hit a cache-permission error; approved local-cache
  recheck passed. No dependency resolution failure remains.
- scripts/set_loader_password.ps1: USER-RUN cached Docker PostgreSQL 17 client,
  fixed owner endpoint, read-only client filesystem, public CA mounted read-only,
  hidden psql prompts, SCRAM, no history. Sets only disabled loader password.
  The agent must not run it or receive its passwords.
- supabase/setup/loader_login_activation.sql: OWNER-RUN guarded one-hour password
  validity/LOGIN, no new grants, no imports/settings/scope updates. NOLOGIN recovery
  blocks new sessions; neither expiry nor NOLOGIN kills an existing session.
- scripts/check_loader_connection.py: USER-RUN hidden loader prompt, pinned
  endpoint/custom role, verify-full CA/hostname, TLS/password-auth checks, read-only
  metadata query, rollback/close, no imports/retries, sanitized failure output.
- supabase/diagnostics/loader_connection_probe.sql and seven synthetic tests.
- data/connection/ directory exists. The CA certificate is NOT yet provided.
  No passwords have been read/stored/printed by the agent. Mark asked whether
  environment variables were agent-readable and AGREED to hidden prompts instead.

## Actual validation

82 Python tests pass:

```powershell
./.venv/Scripts/python.exe -m unittest discover -s tests
```

PowerShell password helper passes syntax parsing. Isolated PostgreSQL 17.12 tests
proved extra SELECT blocks activation, expected ACLs allow it, a restricted-role
session can run the metadata probe read-only, NOLOGIN recovery passes and imports
remain zero. The fixture used socket trust: it does NOT prove hosted password/TLS.
The task's network-none/tmpfs container was inspected and REMOVED. No cleanup pending.
Hosted setup and probe have not occurred. Python formatter API and whitespace
checks pass; avoid Black CLI here because it has hung in earlier sessions.

## Next task for Gemini

First REVIEW the connection setup files and run local tests. Report any actual
issue before changing scope. No need to request approval again for already-approved
local review/tests. Do not commit/push new work unless Mark requests it.

Then guide Mark through docs/tasks/loader-connection-setup.md:

1. He downloads the public project CA to data/connection/supabase-ca.crt.
2. He runs the password helper in his own terminal; owner and new loader passwords
   are entered only at hidden prompts. Never ask him to paste them into chat.
3. He reviews/runs guarded LOGIN SQL in the dev SQL Editor.
4. He runs the Python probe himself and returns ONLY sanitized JSON metadata.

Setup is authorized for this named operator workflow. Agent credential access is
not authorized. Do not run owner/loader connections through agent tools. Once
metadata arrives, document it accurately. Any later 13-record upload needs fresh
full-disk evidence, exact EIN-scope/settings review, verified live state, an approved
execution method and separate explicit batch approval. No automatic upload.

## Handoff safety preflight

READY for local Gemini routing/handoff files only. Objective: continue the same M01
task without broadening authority. Tools are repo reads, reversible local edits and
synthetic tests; external account sign-in/model selection is user-controlled.
No API key, remote model configuration, plugin, hook, browser permission, scheduler
or global configuration was added. Existing AGENTS and explicit task constraints
remain authoritative. Do not send source datasets or credentials to Gemini.

Failure controls: stale state -> git/status/owner read-back; conflicting instructions
-> stop and clarify; uncertain cloud commit -> inspect before retry; credential
request -> operator hidden prompt only; simultaneous writers -> stop one agent.
Local recovery is reverting only new routing/handoff files, preserving task changes.
Evaluation: verify file references exist, working tree preserved, tests run and no
new cloud effects. Account availability, model quota and hosted connection remain
unverified. Review-only handoff does not pass either milestone gate.

## Paste into a new Antigravity Gemini chat

```text
Continue this repo's M01 task. Read README.md, AGENTS.md, GEMINI.md and
docs/tasks/agent-handoff.md. Preserve any existing local changes.
First review those changes and run the synthetic tests. Then guide me through the
operator-only restricted connection setup in docs/tasks/loader-connection-setup.md.
Do not read credentials/environment secrets, connect to Supabase through agent
tools, upload data, expand privileges or rerun prior trial SQL. I will enter any
passwords myself at hidden terminal prompts. Report the current state and next
operator step before doing anything consequential.
```
