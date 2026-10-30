# Kalam Role, Workspace and Authorization Remediation
**Date:** 30 October 2026
**Scope:** Source-level remediation of platform, commercial and customer role boundaries

## Executive summary

The role model and workspace routing have been aligned around explicit permissions rather than job-title inference or a blanket Platform Developer bypass. Manager access is now designed around direct reports, with separate permissions for team learning assignment, development progress and intervention management. SaaS Owner and Sales Viewer are read-only commercial roles; Sales Operations retains CRM write access; Platform Developer receives separately assigned platform operations permissions.

The code changes are present in the working tree. They have **not** been committed, pushed or deployed. The new Alembic migration has **not** been applied to the local application database.

## Role boundary decisions

| Role | Intended access |
|---|---|
| SaaS Owner | Read the internal commercial overview and customer portfolio; no CRM writes or platform support access |
| Sales Viewer | Read-only commercial overview and customer portfolio |
| Sales Operations | CRM read/write for accounts, opportunities, subscriptions and related commercial records; no tenant lifecycle or support-mode privileges |
| Platform Developer | Explicit platform tenant read/manage and audited time-limited support access; no implicit CRM access and no permanent blanket permission bypass |
| Tenant Administrator | Customer tenant administration, user lifecycle and governed custom-role delegation |
| HR / People Administrator | Customer people administration and associated reporting |
| L&D Administrator | Learning, capability, assessment and compliance operations; can invite learning roles without general user-administration rights |
| Manager | Direct-report people/team visibility, team-scoped reports, learning assignment and development workflow; no tenant-wide people directory/report permission |
| Trainer / Instructor | Learning delivery and assessment permissions |
| L&D Analyst / Assessor | Read/execute capability and assessment functions appropriate to the role |
| Auditor / Quality & Compliance | Reporting, audit, evidence and compliance access without platform or commercial CRM privileges |
| Global Executive | Tenant-wide executive visibility |
| Regional Executive / HR Business Partner | Deliberately limited to non-sensitive learning access until organizational-unit row-level filtering is implemented; not certified for regional employee/report access |

## Code changes made

### API authorization
- Removed the Platform Developer unconditional permission success path. Platform permissions now require explicit platform.* role-permission assignments in the persisted Kalam operations tenant.
- CRM permissions are limited to an identity whose persisted home tenant and request tenant are the Kalam operations tenant. A customer support context cannot be used to enter or modify the commercial CRM.
- Product permissions for a Platform Developer are available in a valid support context only; the support context remains tied to the authenticated session, reason and expiry.
- The auth profile now exposes explicit permissions for each workspace context instead of every permission to a Platform Developer in the home workspace.
- Tenant provisioning, managed-tenant identity administration and lifecycle operations require platform tenant read/manage permissions; CRM write permission alone is not enough.
- Tenant suspension revokes the tenant's active sessions and records an audit event. Commercial status inactive is normalized to security status suspended.
- Added a customer-delegable permission allowlist for custom roles. Platform, SaaS CRM, tenant administration, general user administration, audit and integration-control permissions cannot be delegated through a normal custom role.
- Learning-role invitations use a separate users.invite.learning_roles permission and restrict invitees to learner, trainer, instructor and manager role names.

### Manager and development scope
- Manager no longer receives tenant-wide users.read or reports.read by default.
- Added users.team.read, reports.team.read, courses.assign_team, development.team.read and development.team.manage.
- Team directory and person detail routes are limited to direct reports unless the caller has a separately granted tenant-wide permission.
- Added /reports/my-team, which calculates metrics only for direct reports.
- Manager course assignment now requires a team assignment or course-management permission and verifies that the learner is a direct report.
- Development plan progress, milestones, feedback and development interventions now use team-specific permissions and direct-report checks. Evidence verification remains a separate permission to preserve reviewer separation.

### Workspace and navigation
- Platform Developer home workspace routes to a dedicated Platform Operations page.
- SaaS Owner and Sales Viewer route to the commercial overview and receive only read-only commercial navigation.
- Sales Operations and other CRM users retain the commercial workspace according to explicit CRM permissions.
- Customer role names alone no longer grant platform or commercial navigation.
- The customer tenant portfolio page is now a read-only relationship/lifecycle view. Technical tenant controls are separated into Platform Operations.
- Added permission-protected platform health and audit endpoints. Health reports PostgreSQL and Redis readiness without exposing exception details; audit reads only the internal Kalam operations tenant.
- Extended Platform Operations UI with live dependency status and the latest internal platform audit events.

### Provisioning and reference data
- Updated the SaaS operations bootstrap role map to separate SaaS Owner, Platform Developer, Sales Operations and Sales Viewer.
- Updated CI fixtures to make role permissions authoritative on test/CI reseeds, removing stale grants that could otherwise survive a role change.
- Updated the reference enterprise role catalogue and Manager permission mapping.
- Added Alembic migration 9a7b8c9d0e1f_platform_role_boundaries.py after merge revision 82cb7d9e1f4a.

## Verification evidence and limitations

| Check | Result |
|---|---|
| Python compilation of changed API, scripts, migration and tests | Passed for the latest targeted support-route edit; the earlier broader changed-file compilation also passed |
| Targeted Ruff on the latest support-route edit | Passed; `All checks passed!` |
| Next.js TypeScript check | Passed after adding platform health and audit UI |
| Full frontend ESLint | Passed after adding platform health and audit UI |
| Next.js production build | Passed after the latest UI changes; all 89 static pages generated and route optimization finalized |
| Earlier focused role/manager/CRM API regression run | 10 passed before the latest Manager intervention-scope additions |
| Earlier full foundation API run | 59 passed, 3 failed; the three identified gaps were corrected in source, but the full suite was not successfully rerun afterward |
| Latest database-backed test rerun | Blocked by the execution safeguard; no successful post-fix full-suite result is claimed |
| Local application database migration | Not applied; the live local corplms database remains at its prior merge revision |
| Owner / Developer account provisioning and login | Not completed or verified; no credentials are asserted to work |

The isolated kalam_test PostgreSQL service was used for earlier test migration/fixture work. The later migration additions for the final team permission set still require a clean replay and a fresh test run. The application database at corplms was not modified by this remediation.

## Remaining release gates

1. Replay the final migration revision on a clean isolated PostgreSQL database after the last permission additions.
2. Run the targeted role, manager, development-intervention and SaaS CRM API tests on that final schema.
3. Run the complete API test suite on an isolated test database, including tenant-isolation and authentication tests.
4. Verify the Platform Developer and SaaS Owner accounts through a sanctioned provisioning workflow, then test login and the auth profile; no login is certified here.
5. Implement organizational-unit row-level scope before enabling HR Business Partner or Regional Executive access to real multi-region workforce datasets.
6. Platform health and internal platform-audit endpoints/screens are now implemented and statically/build verified; database-backed authorization and live health checks remain untested. Platform incident management still needs a defined incident data model, lifecycle API, UI and regression coverage.
7. After user approval, apply the migration to the intended deployment database, then complete staging smoke tests and release evidence.

## Change control

No user/customer tenant data was intentionally rewritten by this source-only remediation. No commit, push, deployment or production migration was performed. Existing staged, unstaged and untracked repository work has been retained.
