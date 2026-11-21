# Gemini / Antigravity project entry point

Read README.md, AGENTS.md and docs/tasks/agent-handoff.md before taking action.
AGENTS.md and the owning requirements are authoritative; do not invent replacement
requirements or assume a handoff grants additional permissions.

Use the existing feature/irs-downloads branch for this handoff, preserving all
existing local changes. Never edit main, reset the working tree, remove
ignored data or let two agents write this checkout concurrently. Require user
review for consequential commands/external actions; do not enable unrestricted
terminal/browser access or automatic approval to work around limits.

Mark chose hidden password prompts in his own terminal. Do not read .env files,
environment secrets, password managers or credential files; never request a password
in chat or copy one into commands/logs/fixtures. Guide the operator steps, not an
agent credential session. Use synthetic fixtures and aggregate source reports;
do not paste raw IRS records/archives into model context or another service.

Current approved work is local connection setup/review/synthetic testing within
M01. The operator may follow docs/tasks/loader-connection-setup.md. No 2023 cloud
upload, policy widening, new download, production action or milestone advance is
approved. Do not rerun the first-three or next-thirty cloud trial scripts.

Before designing any NEW integration/tool/credential/permission/external side
effect, perform the read-only agent-safety preflight required by Mark's working
agreements. On this machine its instructions are at
C:/Users/markd/.codex/skills/agent-safety-preflight/SKILL.md. If unavailable, stop
that expansion and request the policy; local review/tests remain authorized.

Report actual changes, commands/results and pending gates. Never claim a hosted
check ran from local tests or treat an earlier owner's result as agent execution.
