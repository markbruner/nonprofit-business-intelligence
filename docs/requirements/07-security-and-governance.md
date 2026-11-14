# 07 — Authentication, authorization, privacy, governance

**Status:** Must be met before a usable shared portal. **Applies:** M02 onward and any earlier cloud/database work.

## Requirements

- **SEC-001** Portal is private; unauthenticated users cannot read organization enrichment, contacts, tasks, opportunities, business notes, or app data via UI, API, or database.
- **SEC-002** Initial role model: **Administrator** and **Business Manager**; both manage approved business workflows, only Admin manages users, security, permissions, ingestion/screening configuration and infrastructure.
- **SEC-003** Enforce server-side authorization for each mutation and data-access action; use Supabase/PostgreSQL RLS and least-privilege grants. Hidden buttons are not an authorization control.
- **SEC-004** Test RLS policies for signed-out, manager, admin, and inactive account states, including direct calls that bypass the UI.
- **SEC-005** Require MFA for admin access; assess whether manager MFA should be mandatory before shared launch.
- **SEC-006** Keep service-role secrets exclusively in authorized server-side contexts; never expose them in a frontend bundle, code repository, fixture, logs, or agent prompt.
- **SEC-007** Maintain separate code repository and infrastructure/credentials from Greenspace Guardians, Hamilton County, and unrelated client or personal projects.
- **SEC-008** No collection, upload, model processing, or transmission of private client, donor, volunteer, employee or business records without explicit approval, appropriate authority and defined data boundaries. Only approved public research and minimal professional contact data in v1.
- **SEC-009** Log administrative changes, security-relevant configuration updates, financial-screen overrides, and opportunity stage transitions without unnecessarily collecting sensitive content.
- **SEC-010** Do not permit agent-initiated outreach, payment, publication, user permission changes, destructive edits, or production deployments.
- **SEC-011** Use separate local, preview/test and production configuration; keep preview credentials and data isolated as practicable. Production changes need an explicit promotion decision.
- **SEC-012** Document data retention, export/deletion procedure, backup/recovery expectations, and incident handling before live partner use.
- **SEC-013** Review dependencies and source/API terms before integration; apply rate limits and operational cost safeguards to imports and research.
- **SEC-014** Business Manager financial-record access is approved **in principle** for eventual finance module, but specific business finance categories and formal partner invitation require separate approval before provisioning.

## Role behavior summary

| Capability | Admin | Business Manager |
|---|---|---|
| View/research nonprofit and manage contacts, tasks, opportunities | Yes | Yes |
| Review/override individual financial screening with reason | Yes | Yes |
| Edit screening rule definitions / import configuration | Yes | No |
| Manage users, roles, secrets and system settings | Yes | No |
| Business finance records in future module | Yes | Planned, access specifics unapproved |

## Required threat/test scenarios

- Unauthorized user cannot access a known record ID directly.
- Manager cannot call admin-only mutation even by manipulating API request.
- Inactive member cannot access data.
- Service-role key never appears in client bundle or public logs.
- Failed ETL cannot silently publish corrupt curated data.
- Imported public source text cannot issue instructions to code/research agent.

## Official references

- https://supabase.com/docs/guides/database/postgres/row-level-security
- https://vercel.com/docs/deployments/environments
