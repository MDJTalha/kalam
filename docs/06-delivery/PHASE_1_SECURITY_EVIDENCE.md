# Phase 1 Security & Authorization Evidence

## Scope
Phase 1 authorization hardening covers tenant isolation, RBAC permission enforcement, privileged administration, user/session lifecycle, and protection of governed file surfaces.

## Route-family review
Reviewed API route modules under `apps/api/app/api/routes`:
- admin
- assessments
- auth
- certificates
- compliance
- courses
- development
- files
- integrations
- intelligence
- interop
- notifications
- organization
- people
- programs
- reports
- search
- sessions
- skills
- webhooks

Public endpoints remain intentionally unauthenticated only where required for platform operation, including health checks, login, password-reset initiation/confirmation, invitation acceptance, and public certificate verification.

Self-service endpoints intentionally use the authenticated-user dependency rather than an administrative permission, including the authenticated profile, own sessions, own notifications, own learning progress, own development plan, own compliance actions, and own certificate view.

## Authorization hardening completed
1. Organization-unit listing now requires `users.read`.
2. File upload now requires `files.manage`.
3. File listing and download now require `files.read`.
4. Added `files.read` to the permission catalog.
5. Granted governed file permissions to Tenant Admin and HR/L&D Admin in the seed role matrix.
6. Tenant-scoped role-permission read/update remains protected by `tenant.manage`.
7. Tenant Admin cannot remove `tenant.manage` from its own role.
8. Unknown permission keys are rejected.
9. User lifecycle operations remain tenant-scoped and protect self-deactivation.
10. Role assignment/removal remains tenant-scoped and protects self-role removal.
11. Session management remains user-scoped and prevents revocation of the current session through the individual revoke endpoint.

## IDOR/BOLA controls verified
- Administrative user updates filter by target user ID and actor tenant ID.
- Role permission operations filter by role ID and actor tenant ID.
- Organization role assignment/removal resolves both user and role within the actor tenant.
- Course detail access is tenant-scoped.
- Compliance evidence/assignment operations resolve tenant-owned records.
- Assessment attempt management is permission-protected and tenant-scoped.
- File download resolves both file ID and actor tenant ID.
- Cross-tenant course access returns 404 in regression coverage.
- Cross-tenant resource-ID matrix now exercises course, assessment, role-skill, program and learning-path identifiers from the primary tenant against an isolated tenant; responses are restricted to 403/404 and never disclose the resource.

## Automated evidence
- API foundation suite: **28 passed**.
- Full API test suite: **28 passed**.
- Cross-tenant resource-ID matrix: **PASS** across 6 tenant-owned resource identifiers.
- Privileged endpoint negative-access matrix: **16 protected operations exercised as learner; all returned 403**.
- Permission catalog coverage test: **PASS** for all route-level permission keys currently used by the API.
- Frontend TypeScript check: **PASS**.
- Frontend ESLint: **PASS**.
- Next.js production build: **PASS**.
- Production build generated **43 application routes**.

## Phase 1 exit review
Phase 1 is **CLOSED — local evidence gate passed on 2026-09-24**.

Final evidence is retained in `docs/06-delivery/PHASE_1_EXIT_EVIDENCE.md`.

The closure decision is based on the completed permission reconciliation, negative-access matrix, cross-tenant and parameterized resource-family coverage, user/session lifecycle evidence, permission-aware frontend verification, and successful frontend/API validation gates.

## Change-control note
The bright-blue enterprise visual theme is already a controlled Phase 1 visual change and does not alter authorization or tenant-boundary controls.

## 2026-09-24 — Privileged Frontend Action Verification

Verified and hardened privileged frontend surfaces against the same backend permission model:
- Workspace navigation now consumes authenticated permission claims and hides permission-gated administration entries.
- Administration center gates tenant settings, organization-unit creation, invitations and role-permission updates.
- People administration gates user lifecycle editing/unlock, invitations, organization-unit creation and role assignment with `users.manage`.
- Read-only administration states remain usable for users who have read access but lack mutation permissions.
- Backend authorization remains authoritative; frontend gating is an additional UX/access-control layer, not the security boundary.
- The administration screen now uses the tenant-safe organization role listing for users.read-compatible role visibility.

Validation evidence:
- Frontend TypeScript: **PASS**.
- Frontend ESLint: **PASS**.
- Next.js production build: **PASS**.
- Production build generated **43 application routes**.
- Full API suite: **24 passed**.

## 2026-09-24 — Expanded Tenant/User-Boundary Regression

Added regression coverage for authenticated self-service resource identifiers:
- Learner enrollment/lesson completion cannot be driven with another tenant's enrollment and lesson identifiers.
- Development plan updates are restricted to the authenticated user's tenant and plan ownership.
- Compliance evidence submission rejects another tenant's assignment identifier.

Validation:
- Foundation API suite: **25 passed**.
- Existing cross-tenant resource-ID matrix remains **PASS**.
- Existing 16-operation privileged negative-access matrix remains covered.
- Frontend TypeScript, ESLint and production build remain **PASS** from the preceding frontend authorization increment.
