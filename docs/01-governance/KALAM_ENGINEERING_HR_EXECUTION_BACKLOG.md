# Kalam Engineering and HR Strategy Execution Backlog

**Status:** Initial evidence-based backlog  
**Branch:** `work/kalam-engineering-hr-audit`  
**Prepared:** 2026-10-26  
**Purpose:** Coordinate technical reliability, enterprise security, and HR/L&D domain quality. This backlog records verified repository observations separately from items that still require validation.

## Product direction

Kalam is an enterprise Learning and Capability Platform, not merely a course-delivery LMS. Its core lifecycle is:

**Learning → Skills → Capability → Assessment → Credentials → Evidence → Readiness → Analytics**

Product decisions should connect learning activity to demonstrated capability and evidence, while preserving clear human accountability for employment, performance, promotion, and workforce decisions.

## Evidence reviewed

- The latest inspected CI run, commit `fc872e50b2007cc0f365d7acba0d18dfd928ac7a`, reported successful API, web, and release-configuration jobs.
- The inspected staging deployment run for that same commit failed. The available job summary did not expose a reliable root cause; diagnose logs and the next deployment before claiming resolution.
- The API uses FastAPI, SQLAlchemy, Alembic, tenant-aware role/permission checks, session records, and a time-limited developer support context.
- The production Compose configuration includes PostgreSQL, Valkey, ClamAV, migration, API, worker, web, and Nginx gateway services.
- Product identity is mixed across user-facing and technical identifiers (Kalam, Corporate LMS, `corplms`). Preserve legacy identifiers until compatibility and migration implications are tested.

## Priority 0 — Release reliability

1. Diagnose the failed staging deployment using the exact run and job logs; record the root cause, fix, and verification evidence.
2. Deploy the exact commit that passed CI; confirm API readiness, web availability, gateway health, migration completion, and worker health.
3. Compare the staging workflow's Compose file and environment contract with the production release configuration. Confirm that the deployment target, image tags, environment variables, database volume, and health checks agree.
4. Add or confirm a post-deployment smoke test that exercises login, an authorized tenant-scoped read, and a basic learner/administrator journey without relying on production customer data.
5. Never run destructive migrations, reset persistent volumes, or alter production data as a debugging shortcut.

**Exit criteria:** staging deployment succeeds from a known commit; all services are healthy; smoke tests pass; deployment and rollback steps are documented.

## Priority 1 — Security and tenant boundaries

1. Build a route/resource authorization matrix for tenant administrators, HR/L&D administrators, managers, instructors, learners, and Kalam platform support.
2. Test horizontal and vertical authorization: cross-tenant IDs, nested resources, exports, search, evidence, reports, attachments, integrations, and background tasks.
3. Review platform-developer privileges and support-context behavior. Verify explicit authorization, tenant scoping, expiry, revocation, audit logging, and prevention of privilege escalation.
4. Verify session lifecycle, cookie attributes, lockout, reset flows, CSRF/origin controls, and production configuration fail-closed behavior.
5. Test upload scanning, webhook signing/secret encryption and rotation, integration URL/SSRF defenses, and failure handling.
6. Run dependency and secret scans; classify findings by exploitability and business impact.

**Exit criteria:** no unresolved critical/high-risk authorization defect; negative tests prove cross-tenant access is denied; privileged support actions are auditable.

## Priority 2 — HR and capability domain integrity

1. Define a canonical domain model and lifecycle for skills, capabilities, proficiency levels, assessments, evidence, credentials, role requirements, gaps, readiness, and development plans.
2. Separate learning completion from demonstrated proficiency. Course attendance/completion alone must not be represented as proof of job competence.
3. Require evidence provenance: source, owner, timestamp, method, assessment rubric/version, reviewer, validity period, and correction/appeal history where applicable.
4. Establish configurable job/role capability frameworks; do not hard-code one organization's job architecture or proficiency language.
5. Make assessment scoring explainable and versioned; support accommodations and human review. Do not silently convert uncertain AI inferences into authoritative employee records.
6. Define data minimization, retention, access, correction, and export controls for employee capability records.
7. Design analytics to distinguish participation, learning gain, verified proficiency, readiness, and business outcomes. State limitations and avoid unsupported causal claims.
8. Validate workflows with representative HR/L&D administrators, managers, instructors, and learners before treating screens as complete.

**Exit criteria:** each core workflow has documented business rules, permissions, audit events, validation, error states, and automated tests.

## Priority 3 — Operational readiness

1. Prove clean-database install and supported upgrade paths; verify migration head and recovery procedures.
2. Test backup restoration, persistent file storage, queue retry/deduplication, email delivery, webhook retry behavior, and scanner/provider outages.
3. Add structured logs, request/correlation IDs, actionable health checks, and alerts for worker failures and repeated integration errors.
4. Confirm configuration parity across local, CI, staging, and production without committing real secrets.
5. Ensure CI checks are deterministic, report test counts, preserve useful failure artifacts, and exercise the same release image/configuration that is deployed.

## Priority 4 — Kalam product identity and experience

1. Use **Kalam — Enterprise Learning & Capability Platform** for the product-facing identity.
2. Audit visible legacy AIVON/CorpLMS/Corporate LMS labels in UI, metadata, emails, docs, seed/demo content, and support screens.
3. Keep internal package names, database identifiers, volume names, and cookie names unchanged unless a tested migration/compatibility plan explicitly approves changes.
4. Verify every navigation item leads to a working, permission-appropriate screen; document routes that are planned versus implemented.
5. Provide accessible, responsive, consistent UI states: loading, empty, error, unauthorized, and success.

## Working rules

- Treat source-code inspection as evidence of implementation, not proof of runtime behavior.
- Treat a green CI run as evidence for that commit and those checks only.
- Do not claim security, compliance, deployment, HR outcome, or feature completion without testable evidence.
- Prefer small, reviewable changes with tests and a pull request; do not push speculative broad refactors to `main`.
- Record each finding with severity, affected component, reproduction, expected behavior, test, fix commit, and closure evidence.

## Immediate next actions

- [ ] Retrieve the failed staging job's logs and identify the actual failure step.
- [ ] Compare staging and production Compose/workflow configuration.
- [ ] Verify the newest CI and staging runs after the last inspected commit.
- [ ] Reproduce the failure in a safe environment and make the smallest tested correction.
- [ ] Begin tenant-boundary and HR capability-lifecycle test matrices.
