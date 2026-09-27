# Kognivon — Customer Administrator Guide (release candidate)

Status: Product documentation draft for customer/UAT review. It does not certify a production deployment.
Audience: Tenant administrators, L&D operations, compliance owners, managers and auditors.

## Before onboarding

- Confirm the customer tenant, public URL, organization owner, allowed domains and support contacts in the target environment.
- Establish user roles and the least access each role requires. Tenant administrators assign roles; business owners approve access to compliance, reporting and AI administration.
- Import or create users and organization structure only after checking departments, locations, teams and reporting relationships. Test a small sample before bulk changes.
- Agree on employee-data purposes, retention, export and deletion processes with the customer's privacy and legal teams before importing real records.
- Use the demo organization only for development or UAT. Do not seed demo data into a customer production tenant.

## Signing in and access

1. Open the customer-approved HTTPS address and sign in with your assigned organization identity.
2. If you cannot sign in, use the password reset flow or contact your tenant administrator. Account lockout and session expiry are security controls.
3. Use the profile and sign-out controls when leaving a shared device. Administrators can review session controls and authorized role assignments.
4. If a page or action is unavailable, have an administrator verify your role and tenant scope. Do not share a privileged account to bypass a missing permission.

## Configure the organization

1. In **Organization** and **People**, confirm business units, departments, locations, teams, managers and active user status.
2. Invite or update a small pilot group; verify each user lands in the right tenant and sees only the permitted organization scope.
3. Assign administrator, L&D, compliance, manager, instructor, report and learner access according to duties. Record who approved elevated access.
4. Review inactive users, reporting lines and permissions after imports and personnel changes.
## Publish learning

1. Use **Course Studio** to create a draft course, choose the owner, category and visibility, and add modules, lessons and authorized files.
2. Confirm learning content, file scan status, prerequisites, enrollment rules, capacity and intended audience before publishing.
3. Publish the version approved by the content owner. Test the learner view with a non-administrator account and confirm access, progress and completion evidence.
4. Use the audited content history and restore controls if a published change must be reversed. Verify learners' existing evidence after a restore.
5. Use **Programs**, **Learning Paths**, **Sessions** and **L&D Operations** for structured assignments, cohorts, attendance and follow-up.

## Assessments and credentials

- Create questions and assessments with explicit pass thresholds, attempt limits and time rules. Check answer keys and feedback with an authorized reviewer before assigning learners.
- Review attempts and manual grade changes through the authorized assessment workspace; record the business reason for an override.
- Configure certificate templates, issue and renewal rules, then verify a sample certificate through the intended verification flow. Review revocations and expiry evidence.
- Confirm that course completion, assessment outcome and certificate status agree before using them in a compliance decision.

## Compliance and capability

1. In **Compliance & Readiness**, define the requirement owner, audience, due date, recurrence, qualifying learning and evidence rules.
2. Preview applicability on a pilot audience before assigning broadly. Monitor overdue items, exceptions and evidence decisions; document reasons for overrides or rejection.
3. In **Skills & Capabilities**, maintain skill definitions, proficiency levels, role requirements and course mappings. Review development plans with the employee and manager.
4. Validate dashboard and report filters against a known sample before using readiness or skill-gap metrics in executive communications.

## Reports and integrations

- Use **Reports** and **Analytics** with authorized filters; distinguish persisted records from derived measures and AI narrative. Export only to an approved destination.
- Review saved reports, scheduled delivery and recipient permissions. Check schedule-run history after changing a report or audience.
- Configure third-party connections and webhooks only with approved endpoints and credentials. Run the connection check, verify a real provider exchange and review delivery failures/retries.
## Governed AI

- AI features are optional and tenant governed. Enable only approved use cases, providers, models, prompts and budgets through authorized administration.
- Check source citations and human review outcomes. AI text is assistance; learning completion, grades, compliance and employment decisions require the system's authoritative records and human process.
- Do not paste sensitive data into an AI workflow unless the tenant policy and provider agreement permit it.

## Daily operating checks

- Confirm gateway availability, API readiness, database and queue health, worker processing, upload scanning, delivery failures and certificate/backup status.
- Escalate suspected cross-tenant exposure, unexpected privileged access, data corruption or a failed restore as release-blocking incidents.
- Keep an off-host database and file backup with verified restore evidence. A successful backup job alone does not establish recoverability.
- For application rollback, use the approved runbook and previous known-good images; never assume a database schema downgrade is safe.

## Support and change requests

Capture the tenant, affected role, route, time and request ID for a support case. Avoid attaching passwords, raw tokens or unnecessary employee records. For access incidents, preserve logs and follow the customer's incident channel. Product changes enter change control with an owner, requirement, test and release evidence.

## Release and service boundaries

This guide describes the locally implemented product workflows. The current evidence does not establish a public production SLA, regional data residency, legal compliance, independently audited accessibility, live SSO, external email delivery or any specific third-party integration. Customer acceptance requires target-environment tests and written commercial/legal terms. See `PHASE_8_RELEASE_ACCEPTANCE.md` and `PHASE_8_RELEASE_RUNBOOK.md`.
