# Kognivon Task 15 — RBAC and Tenant Isolation

Date: 2026-09-29
Status: Complete

## Audit scope

- Workspace navigation permission filtering for People, Learning, Course Studio, Capability Framework, Assessments, Certificates, Compliance, reporting, and SaaS CRM.
- API permission guards for administration, courses, assessments, certificates, compliance, AI, and SaaS CRM routes.
- Tenant scoping for representative LMS resources and the SaaS CRM operations surface.

## Findings

- `WorkspaceNav` and `SaaSCrmNav` remove navigation groups and items when the session does not include the item permission.
- Protected API handlers use `require_permission(...)` for read and management operations rather than relying on UI visibility.
- SaaS CRM access is restricted to the configured operations tenant, with the explicit demo CRM exception. CRM account, plan, offer, subscription, contract, invoice, payment, task, and related queries include the authenticated operations tenant scope.
- Resource lookup helpers reject IDs belonging to another operations tenant. Managed customer-tenant linking also validates provenance and prevents linking operations or demo tenants.
- Existing regression coverage includes cross-tenant data isolation, cross-tenant resource ID rejection, admin lifecycle isolation, permission-catalog coverage, protected file/organization surfaces, CRM permission checks, and marketing inquiry queue isolation.

## Implementation decision

No production code change was required for this task. The audited controls and existing regression suite cover the requested RBAC and tenant-isolation boundaries; adding a duplicate test would not improve the current protection.

## Verification

- `pnpm --filter web typecheck` — passed during the Task 14 verification cycle.
- `git diff --check` — completed with exit code 0; the repository still reports pre-existing line-ending normalization warnings.
- API test collection remains unavailable in this checkout because the environment is missing the `joserfc` dependency.
- Browser smoke verification remains unavailable because no browser surface is exposed in the current computer-use environment.
