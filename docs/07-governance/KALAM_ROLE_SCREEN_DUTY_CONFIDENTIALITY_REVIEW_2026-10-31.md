# Kalam Role, Screen, Duty and Confidentiality Review

**Review date:** 31 October 2026  
**Repository:** `MDJTalha/kalam`  
**Work branch:** `work/kalam-complete-role-catalog-2026-10-31`  
**Review approach:** product architecture, HR/L&D operating model, SaaS operations, access-control engineering, internal audit and privacy-by-design.

## 1. Executive assessment

Kalam has a meaningful role-based foundation, but the review found gaps between job responsibilities, dashboard navigation, API enforcement and data scope. The work on this branch makes those boundaries more explicit.

The design uses three distinct security domains:

1. **Customer tenant workspace:** the tenant's own workforce, learning, capability and compliance data.
2. **Kalam SaaS operations workspace:** internal SaaS business, customer lifecycle, finance and team administration.
3. **Engineering/support workspace:** Platform Developer access, with a separate time-limited and audited customer support context.

A role is considered operational only when its job scope is represented by all of the following: a route/screen, an appropriate permission, a server-side authorization check, a tenant/resource filter, and a tested workflow. A role row or a hidden menu item alone is not evidence of end-to-end completion.

## 2. Tenant role catalogue and workspace mapping

| Role | Primary job and responsibilities | Main screen / work areas | Report and data boundary |
|---|---|---|---|
| **Tenant Owner** | Organizational stewardship, oversight of learning and compliance outcomes, governance escalation. | `/dashboard` owner overview; `/dashboard/reports`; `/dashboard/audit`; aggregate analytics. | Aggregate tenant measures and audit visibility. No employee directory, profile editing or bulk personal-data exports by default. |
| **Tenant Administrator** | Tenant configuration, user lifecycle, organization structure, role assignment, integration and access governance. | `/dashboard/admin`; People Administration; Organization; Integrations; Audit; Reports; compliance and capability administration where granted. | Tenant-scoped employee records. Sensitive workforce, learning and compliance exports are separately granted and audited. |
| **HR / People Administrator** | Employee records, joiner/mover/leaver processes, manager and org-unit data, people-related compliance coordination. | `/dashboard`; `/dashboard/people`; `/dashboard/people/admin`; `/dashboard/team`; `/dashboard/organization`; compliance coordination. | Tenant workforce records within their HR remit. Has explicit people and learning export permissions plus separately governed compliance export access. |
| **L&D Administrator** | Learning strategy and operations, course authoring, curricula, assessments, certificates, skills and development programmes. | `/dashboard`; `/dashboard/ld-operations`; Course Studio; Learning Catalog; Assessments Administration; Certificates; Skills/Capabilities; Capability Gaps/Risk; Reports. | Tenant learning/capability operations. Can export employee-linked learning records; workforce-wide people exports remain an HR/tenant-admin duty. |
| **Manager** | Direct-report performance support, learning follow-up, team capability and development actions. | **Dedicated** `/dashboard/manager`; `/dashboard/team`; `/dashboard/development`; scoped capability gap/risk and team assessment work. | Direct reports only. Manager role no longer receives tenant-wide `users.read` or `reports.read`; capability-risk calculations use the authorized population, not tenant-wide denominators. |
| **Instructor** | Prepare and deliver assigned sessions, manage attendance and assess learners on courses they teach. | **Dedicated** `/dashboard/instructor`; `/dashboard/sessions`; `/dashboard/sessions/{id}` attendance register; `/dashboard/assessments`; `/dashboard/assessments/review/{id}`. | Assigned sessions/courses only. Instructor grading permission is separate from assessment authoring/admin; attendance roster contains learners enrolled in that course. |
| **Learner / Employee** | Complete assigned learning, take assessments, maintain own development goals and compliance evidence. | `/dashboard` My Learning; Catalog; Learning Paths; Programs; Assessments; Certificates; own Development Plan; own Compliance and Profile. | Own records and assigned learning. Cannot browse team, tenant people data or employee-wide exports. |
| **HR Business Partner** | Support assigned workforce relationships, advise managers and coordinate development interventions. | **Dedicated** HRBP overview on `/dashboard`; `/dashboard/team`; `/dashboard/development` for direct reports. | Direct reports only until a governed business-unit/portfolio assignment model exists. No broad people directory or tenant-wide HR analytics grant. |
| **Quality & Compliance** | Manage compliance obligations, evaluate evidence and exceptions, maintain audit-ready decisions. | **Dedicated** Quality dashboard; `/dashboard/compliance/admin`; `/dashboard/evidence/admin`; `/dashboard/audit`. | Compliance assignment/evidence/exception records and audit trail. No general people directory or broad workforce reports. Has explicit compliance export grant. |
| **Auditor** | Independently inspect evidence, files and audit events; identify control exceptions. | **Dedicated** Auditor overview; `/dashboard/audit`; governed Files and Evidence read-only surfaces. | Read-only evidence and audit scope. No people exports, grading, compliance approvals or operational changes. |
| **Regional Executive** | Regional leadership and regional workforce outcomes. | **Not enabled yet.** | Role has no grants until region-to-org-unit assignment and row-level filters exist consistently across people, reports, capability and compliance APIs. This avoids an unsafe tenant-wide substitute for regional visibility. |
| **Global Executive** | Enterprise oversight of workforce and learning performance, organization-level trends and assurance. | **Dedicated aggregate-only** Executive dashboard; Reports; Analytics; Audit. | Aggregate population, learning, compliance and organization outcomes. Individual employee profile access, employee-level capability gaps and personal exports are removed from this role. |

## 3. SaaS platform roles and workspace mapping

| Role | Primary job and responsibilities | Main screen / work areas | Deliberate exclusions |
|---|---|---|---|
| **SaaS Super Admin** | Highest commercial platform authority: manage plans, pricing, tenant lifecycle, platform roles, internal team, subscriptions, customer access, revocations and audit. | `/dashboard/saas`; Pricing; Tenants; Customer Users; Team; Tenant Role Governance; Billing; Contracts; Subscriptions; Onboarding; Trials; Audit. | Distinct from Platform Developer. Cannot assign or alter the Platform Developer identity; last active Super Admin safeguards apply. |
| **SaaS Administrator** | Operate internal SaaS access, team lifecycle and operational platform configuration. | `/dashboard/saas/team`; platform certifications/settings and authorized internal team administration. | Cannot create custom platform roles, access finance management, or act as the Super Admin by role-name equivalence. |
| **SaaS Business Owner** | Read commercial, pricing, finance, customer-success and platform performance at business level. | `/dashboard/saas`; read-only business/financial/customer-success overview pages. | No internal employee roster, customer employee directory, financial mutations or general role administration. |
| **Sales Operations** | Manage prospects, accounts, contacts, opportunities, pipeline, sales tasks and approved sales exports. | `/dashboard/saas/pipeline`; Clients; Leads & Inquiries; Tasks; Pricing read; limited Sales Team owner pool. | No invoices/payments/contracts, tenant employee directory, customer onboarding administration or customer tenant user access. |
| **Sales Viewer** | Read approved sales pipeline, client and pricing context. | `/dashboard/saas/pipeline`; Clients; Pricing. | Read-only. No exports, edits, internal team roster, customer user records, trials, billing or finance. |
| **SaaS Finance Administrator** | Administer subscriptions, contracts, invoices, payments, renewals and pricing context. | `/dashboard/saas/billing`; Contracts; Subscriptions; Financial Forecast; Renewals; Pricing read. | No sales opportunity management, customer employee directory or general customer profile access. |
| **Customer Success Manager** | Customer onboarding, trials, tenant lifecycle and approved customer user access/support. | `/dashboard/saas/tenants`; Trials; Onboarding; Customer User Access; read-only sales/pricing context. | No finance mutation or internal SaaS employee directory. Custom role definitions remain Super Admin authority. |
| **Platform Developer** | Engineering/support, technical troubleshooting, platform-level development, integrations and audited time-limited customer support mode. | Platform administration, developer support tenant selector, system/technical support and audit surfaces. | Separate engineering identity. SaaS Super Admin cannot provision, modify or revoke this role. Support access is time-limited and audited. |

## 4. Report and export policy

Dashboard/report viewing and bulk download are separate capabilities.

| Data/report type | Required grant | Intended roles |
|---|---|---|
| Aggregate reports, engagement, trends and organization outcomes | `reports.read` | Tenant Owner, Tenant Administrator, HR/People, L&D and approved executives. |
| Employee-identifiable people register | `reports.export.people` | Tenant Administrator and HR / People Administrator. |
| Employee-linked learning/enrollment register | `reports.export.learning` | Tenant Administrator, HR / People Administrator and L&D Administrator. |
| Employee-linked compliance register | `reports.export.compliance` | Tenant Administrator, HR / People Administrator and Quality & Compliance. |
| SaaS CRM account CSV | `saas.sales.export` | Sales Operations and SaaS Super Admin. |
| Audit log | `audit.read` / `saas.audit.read` | Tenant governance, Quality, Auditor, approved executive and SaaS governance roles. |

Sensitive people, learning and compliance exports record an audit event with the actor, export type and record count. Export metadata does not copy the exported personal rows into the audit event.

## 5. Segregation of duties

The following combinations are deliberately separated:

- **Assessment authoring vs grading:** L&D/tenant administrators hold `assessments.manage`; instructors hold `assessments.grade_assigned` only for courses with live sessions assigned to them.
- **Evidence submission vs evidence approval:** evidence records retain `submitted_by`; the reviewer cannot verify or reject an item they submitted, including evidence submitted on behalf of another employee.
- **Exception request vs exception decision:** exception records retain `requested_by`; the requester cannot approve or reject their own request. Approval and rejection actors/timestamps are retained.
- **Sales vs finance:** Sales roles do not receive invoice, payment, contract or finance forecast permissions; finance roles do not receive sales pipeline mutations.
- **Sales vs Customer Success:** Sales can manage opportunities and accounts but not customer onboarding, tenant status or customer-user access. Customer Success owns those operations.
- **Internal SaaS team vs customer employee administration:** internal team membership is separate from customer-tenant user management.
- **SaaS Super Admin vs Platform Developer:** Super Admin is the highest commercial/operations authority; Platform Developer remains a separate engineering/support identity.
- **Built-in vs custom roles:** tenant built-in roles are protected from rename/delete/permission changes through the custom-role workflow; custom roles cannot be deleted while assigned.
- **Last administrator safeguards:** the last active SaaS Super Admin and last active tenant owner/administrator cannot be removed or deactivated through the guarded pathways.

## 6. Confidentiality, transparency and workflow rules

### Confidentiality
- Every tenant-bound query must include the tenant/resource boundary; SaaS data is confined to the operations workspace.
- Managers and HRBPs see direct reports, not the tenant-wide directory.
- Customer employee data is separate from internal SaaS employee records.
- Financial, sales, customer-success and platform data are different permission domains.
- Export permissions are explicit and narrower than general report access.
- Do not place secrets, access tokens, passwords or credential values into screen content, logs or audit metadata.

### Transparency
- Role assignment, removal, invitation, user changes, account deactivation, role/permission changes, tenant lifecycle actions, evidence decisions, exception decisions and sensitive exports create audit records.
- UI status must distinguish **read**, **manage**, **approve**, **export** and **revoke** permissions.
- A restricted or unavailable report must display a clear access/data-availability state rather than silently showing misleading zeroes.

### Workflow streamlining
- Dashboards should prioritize each job's own queue: overdue tasks, upcoming sessions, evidence awaiting review, customer onboarding blockers, renewals and unresolved access events.
- Use one primary work queue per role and link to the relevant detail screen.
- Avoid exposing controls that are guaranteed to receive a 403 from the API.
- Keep read-only roles visibly read-only; make destructive actions require confirmation and show session/access revocation effects.
- Prefer task-specific screens with clear ownership, status, due date, next action and audit history.

## 7. Screen-level review findings and corrections on this branch

| Review finding | Correction made on this branch |
|---|---|
| Manager role exposed broad employee-directory and report grants. | Manager now uses `team.read`; People team API and Manager workspace are direct-report scoped. |
| Development plan endpoints used generic `users.read` checks. | Direct-report/tenant-admin/authorized HR-L&D plan scope is checked server-side for plan, milestone and feedback actions. |
| Instructor shared assessment-admin permission. | Added `assessments.grade_assigned`; list, detail, attempts, grade and analytics are limited to sessions assigned to that instructor; learner attempts are limited to enrolled courses. |
| Instructor had no clear attendance work route. | Added session detail, enrolled learner roster and attendance status update UI; server rejects a learner not enrolled in the session course. |
| Global Executive had individual employee permissions despite an aggregate leadership purpose. | Removed individual user/capability-gap/capability-risk grants and added an aggregate-only executive dashboard. |
| Regional Executive had no enforceable regional data scope. | Role is intentionally disabled until region-to-org-unit mapping and row filters are implemented. |
| Sales, finance and Customer Success reused broad CRM permission. | Split API dependencies and screen actions into sales, pricing, finance, customer-success, customer-user and platform permissions. |
| Sales client detail could include financial and trial data unnecessarily. | Financial records are only queried/returned for finance-read users; trial details are only queried/returned for Customer Success readers. |
| Customer-user access existed at API level without a complete work screen. | Added tenant customer-user management page for Customer Success/Super Admin; only Super Admin can assign/remove customer roles. |
| Compliance exception request attribution was missing. | Added requester/reviewer fields; self-approval/rejection is blocked and reviewer identity/time is recorded. |
| Sensitive exports were controlled by generic report access. | Dedicated people, learning and compliance export grants; exports are audit-logged. |
| Custom SaaS platform roles were not assignable after creation. | Added Super Admin role CRUD and allowed Super Admin to assign/remove constrained custom platform roles. |

## 8. Remaining acceptance gates

The source changes are committed to the feature branch, but the following must still be verified before describing role integration as production-complete:

1. Apply all new Alembic migrations to an isolated test database and verify the full migration chain.
2. Run the complete API test suite, lint/type checks and web build on the exact branch head.
3. Complete authenticated browser acceptance for each role, including denied direct URLs, menu visibility and persisted workflows.
4. Verify tenant A cannot retrieve tenant B's users, roles, evidence, reports, invoices or sessions by changing IDs.
5. Verify Manager and HRBP direct-report filtering for list, details, development, capability gaps/risk and exports.
6. Verify instructors cannot see answer keys before submission, assess courses not assigned to them, or grade their own attempts.
7. Verify evidence and exception self-review protections in a live database-backed test.
8. Verify Sales Viewer cannot mutate records or export; Sales Operations cannot access finance/customer-user routes; Finance cannot access sales mutations; Customer Success cannot access internal SaaS team records.
9. Verify last-administrator safeguards, lockout, session revocation, audit log contents and password onboarding.
10. Confirm accessibility, mobile layout, empty/error states, report definitions and business-owner sign-off.

**Release statement:** This document describes the intended role model and code changes on the feature branch. It is not a claim that all screens have passed browser acceptance, that migrations have run in staging/production, or that every role has been certified against live tenant data.
