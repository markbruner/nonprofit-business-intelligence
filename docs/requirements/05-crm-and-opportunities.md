# 05 — Relationships, CRM, opportunities

**Status:** Confirmed, implemented in M03 (not M01/M02). **Milestone:** M03.

## Requirements

- **CRM-001** One canonical organization may have **zero or many contacts** and a relationship record without a paid opportunity.
- **CRM-002** Track professional contacts and roles, sourced business contact methods where appropriate, ownership, and update history; contact records are not evidence of permission for automated outreach.
- **CRM-003** Relationships track owner, outreach/engagement status, last interaction, next action, and next action due date separately from opportunities.
- **CRM-004** Record interactions (meeting/call/email/manual note) with occurred-at, author, associated organization/contact where applicable, and summary. Do not ingest email contents automatically in v1.
- **CRM-005** Support manually created follow-up tasks with owner, due date/time, status, description, and optional organization/opportunity links.
- **CRM-006** Show upcoming and overdue tasks on Business Overview; define overdue using user-selected local date/time and stored timezone-safe timestamps.
- **CRM-007** Support **multiple service-specific opportunities per organization** with service type, owner, optional estimated value, next step, and its own stage.
- **CRM-008** Create an opportunity only when a plausible specific service engagement is identified; importing or screening an organization must not auto-create one.
- **CRM-009** Support opportunity stages `identified`, `discovery`, `proposal`, `negotiation`, `won`, `lost`, `deferred` (subject to product review). Distinguish terminal and paused outcomes.
- **CRM-010** Retain immutable opportunity stage transitions with actor, before/after, timestamp; never overwrite history during edits.
- **CRM-011** Support separate organization-relationship owner and individual opportunity owner; admin and business manager can work the CRM under authorized permissions.
- **CRM-012** Keep estimated pipeline value optional and sourced to a real opportunity, not derived from counts of financially qualified nonprofits.

## Workflow scenarios to test

- Research/qualify an organization, create a contact and follow-up, **without** creating an opportunity.
- One organization receives an impact-reporting opportunity and later a distinct GIS storytelling opportunity.
- Manager logs a call and completes a task; the overdue dashboard updates.
- Changing from proposal to won/lost/deferred produces an audit event and preserves past stages.
- Manager cannot change user roles or administrative rules through UI **or direct API**.

## Out of scope

Bulk email sending, email/calendar integrations, automated follow-up messages, public sharing, invoice generation, signed contracts, contact enrichment from opaque brokers.
