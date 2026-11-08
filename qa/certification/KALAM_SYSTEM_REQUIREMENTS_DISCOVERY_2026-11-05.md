# Kalam — System Requirements Discovery and Current-State Audit

**Audit date:** 2026-11-05  
**Repository:** https://github.com/MDJTalha/kalam  
**Local checkout inspected:** C:\Projects\Kalam-final-certification  
**Inspected branch / HEAD:** work/final-production-readiness-2026-10-31 / 01fb327d73d8508be295fffc705912c62090e6d6  
**Scope:** Product, architecture, functional requirements, identity/authorization, data, UX/brand, integrations, runtime, QA evidence and release readiness.

> This is an evidence-bound requirements and current-state audit, not a production certification, independent security opinion, legal opinion, or claim that every route has passed authenticated manual review. Local working-tree observations below describe the checkout at inspection time on 2026-11-05.

## 1. Executive assessment

Kalam is an **Enterprise Workforce Capability Platform**, not only a conventional learning management system. It connects workforce identity and organization, learning, assessments, credentials, compliance, skills and capability, employee development, analytics, integrations, governed AI and internal SaaS operations.

The engineering foundation is substantial and uses a modular-monolith architecture. The candidate contains broad product functionality and multiple layers of test evidence. However, the local checkout was heavily modified, the candidate branch had diverged from main, and material security, authenticated workflow, browser, reliability and production-operation gates remained open.

**Release disposition at audit time: NO-GO for production.** This is based on open and failed evidence gates, not on an estimate of how much code has been written.

## 2. Repository and candidate boundary

- Local branch: work/final-production-readiness-2026-10-31.
- Local HEAD at inspection: 01fb327d73d8508be295fffc705912c62090e6d6.
- GitHub PR #38 pointed to the same HEAD and remained open, draft, unmerged and mergeable=false.
- PR #38's own description says it is not approved for merge or production deployment.
- Branch comparison at inspection: 14 commits ahead and 3 behind main; merge base 0846b2b15e3c6ec64458804f4b35e30b43d07d0e; main tip 598813b10065a29ff398a4ea24f2573c43e10db6.
- Local working tree at inspection: 201 changed paths, including 118 untracked entries. There were both staged and unstaged changes.
- Hosted GitHub Actions run #518 / 41316033724 was recorded as successful for the exact committed HEAD. This is CI evidence only; it does not validate later uncommitted changes or production deployment.

**Preservation rule:** Do not reset, clean, stash, bulk-stage, commit, push, pull, rebase, merge, overwrite or deploy the dirty checkout until all existing changes have been inventoried and a reviewed integration plan exists. Many untracked files are QA scripts, logs and evidence; they must not be assumed disposable.

A root-level untracked Developer.txt contained plaintext account credentials. The values are intentionally not reproduced here. Rotate affected passwords through the authorized account process, review/revoke sessions as appropriate, and remove the file only after its legitimate non-secret contents are safely preserved. Do not commit that file.

## 3. Product mission and personas

### 3.1 Product promise

Kalam connects **Expectation → Capability → Evidence → Action → Readiness**. It should help an organization understand role requirements, what employees have demonstrated, where gaps and compliance obligations exist, what action is required, and which persisted records support the current position.

The product supports accountable human decisions. It must not claim that software independently certifies competence, guarantees regulatory compliance, or replaces accountable management decisions.

### 3.2 Personas

1. Learner / Employee — assigned and discoverable learning, progress, assessments, credentials, skills and development.
2. Manager — authorized team visibility, learning assignment, overdue/at-risk signals and follow-up.
3. L&D Administrator — catalog/course authoring, programs, paths, cohorts, enrollment, delivery, instructors and reporting.
4. HR / People Administrator and HR Business Partner — authorized workforce records, organization and development signals.
5. Compliance / Quality & Compliance / Auditor — requirements, applicability, assignment, evidence, expiry, exception, audit and export. Auditor access is purpose-limited and read-only.
6. Instructor / Facilitator — assigned sessions, rosters, attendance, grading and feedback.
7. Executive — appropriately aggregated workforce capability, compliance risk, readiness and trends.
8. Tenant Owner / Tenant Administrator — customer-tenant configuration and administration.
9. Kalam SaaS operations — internal customer lifecycle, sales, pricing, finance, platform and support.
10. Platform Developer / Support Operator — controlled engineering/support access that must not turn customer context into platform privilege.

### 3.3 Critical journeys

- Learner: authenticate → dashboard/catalog → enroll/access assignment → lessons/content → assessment → persisted completion → credential → skills/development evidence.
- Manager: authenticate → authorized team view → identify signal → inspect learner → assign/recommend action → monitor persisted result.
- L&D: create course → author/version → approve/publish → define audience → enroll/assign → deliver → monitor → report.
- Compliance: define requirement → applicability/recurrence → assign → evidence/completion → exception/escalation → auditable report/export.
- Instructor: assigned sessions → roster → attendance → grading/feedback → completion.
- Tenant admin: users/org/roles/integrations/settings → audit and reporting inside tenant and authorized organization scope.
- SaaS operations: client/lead → opportunity/offer/pricing → contract/subscription/invoice/payment → onboarding/provision tenant → lifecycle/renewal → support/audit.
- Executive: trusted aggregate indicators → authorized drill-down → accountable decision. No implied unrestricted row-level access.

## 4. Functional requirement map

| Domain | Required capabilities | Main acceptance conditions |
|---|---|---|
| Identity and accounts | Login/logout, password reset, invitations, account lifecycle, sessions/devices, lockout, MFA and OIDC SSO | Correct session lifecycle; privileged MFA policy; safe recovery; audit |
| Tenant and organization | Tenant lifecycle, business units, departments, locations, teams, org-unit tree and reporting lines | Every query/write scoped server-side; missing/invalid scope fails closed |
| RBAC and governance | Roles, permissions, assignment, explicit allow/deny, tenant/resource/org scope and support context | API/query authorization; UI visibility is never the security boundary |
| People / HR | Profiles, directory, manager relationships, provisioning, status and exports | Purpose/role-limited identity fields; manager scope enforced |
| Catalog and content | Courses, categories, tags, ownership, objectives, prerequisites, modules, lessons, files, versions and publish lifecycle | Valid transitions; secure upload/download; malware scan |
| Learning delivery | Enrollment, approvals, capacity, waitlists, cohorts, paths, programs, lessons, progress, attendance, due dates and reminders | Idempotent transitions; persisted progress/completion; no fabricated completion |
| Assessment | Question banks, attempts, time limits, scoring, thresholds, feedback and manual grading | Protected answer keys; attempt rules; audited overrides |
| Credentials | Templates, issue, expiry, renewal, revocation, QR/public verification and history | Authentic verification and auditable lifecycle |
| Compliance | Requirement catalog, applicability, assignment, recurrence, due dates, expiry, evidence, exceptions, escalation and reports | Evidence-backed status; secure tenant/org scope |
| Skills and capability | Taxonomy, competencies, proficiency, role expectations, evidence, gap/risk intelligence and reassessment | Metric provenance; persistent evidence; scoped access |
| Development | Plans/goals, interventions, milestones, recommendations and manager feedback | Owner/manager scope; progress persistence and audit |
| Delivery operations | Instructors, sessions, attendance, workshops, equivalencies and bulk assignment | Assignment/grading within authorized course/session scope |
| Communications | In-app/email, templates/preferences, digests, reminders, alerts and retry state | Observable delivery; idempotency/retry; security notices protected |
| Search and reporting | Global search, saved reports, filters/sorts/pages, schedules, exports and dashboards | Server-side scope/pagination; runs audited; metric provenance |
| Integrations | REST/OpenAPI, webhooks, CSV, HRIS, OIDC, email, calendar, LTI/xAPI and SCORM/cmi5 adapter boundary | Real handshake, mapping, failure/retry, privacy and delivery evidence |
| Governed AI | Q&A, retrieval/citations, recommendations, summaries, assisted authoring and capability explanations | Optional/disabled by default; source/tenant policy; provenance; human review for consequential actions |
| Internal SaaS operations | CRM, sales, pricing, finance, contracts, subscriptions, invoices, payments, renewals, onboarding, customer users, tenant provisioning, team and audit | Strict internal home-tenant boundary; domain grants; redaction; privileged controls |
| Platform operations | Health/readiness, jobs, monitoring, backups, restore, deployment, rollback and DR | Observable environment evidence, not only runbooks |

### 4.1 Implementation surface discovered

API route groups include health, auth, courses/equivalencies, assessments, certificates, compliance, skills, capabilities/domains/gaps/risk, evidence, reports/report library, people, admin, organization, programs, sessions, notifications, support, development/intelligence/execution, search, files, integrations, webhooks, interoperability, AI, marketing and SaaS commercial/finance.

The web application includes public/authentication routes and a broad dashboard covering admin/support, AI, analytics, assessments, audit, capability/gaps/risk, catalog/course studio, certificates, compliance/evidence, development, files/help, instructor/sessions, integrations, L&D operations, learning paths, manager/team, notifications, organization/people, programs, reports, SaaS CRM/finance, search, settings, skills and webhooks.

This is a module/route inventory, **not proof that every screen, control, role path or persisted workflow has passed acceptance**.

## 5. Non-functional and cross-cutting requirements

### 5.1 Security and privacy
- Argon2id password hashing; secure HTTP-only server-managed sessions; lockout, expiry and revocation.
- MFA for privileged roles; password and OIDC flows must converge on the same session-issuance policy.
- OIDC validates issuer, audience, nonce, expiry and identity linkage; external identity never bypasses local authorization.
- Least privilege and tenant/resource scope on every API read/write, export, aggregate, indirect join, background task and file/object operation.
- Secret injection, encryption-key separation/lifecycle and no credentials in source, logs or audit payloads.
- CSRF/origin/host controls, rate limits, abuse protection, safe errors, dependency scans and secure file handling/malware scanning.
- Durable audit for privileged/business actions; minimize personal data in logs.
- AI cannot bypass permissions or manufacture authoritative completion/compliance/certification evidence.

### 5.2 Data integrity
- PostgreSQL is the system of record; tenant-owned business rows have explicit tenant ownership.
- Foreign keys, unique constraints, indexes and state transitions protect correctness.
- Critical commands require idempotency/duplicate protection where appropriate.
- Migrations must be reproducible and have an approved recovery strategy; no blind Alembic stamps or ad-hoc production schema edits.
- Reports distinguish persisted measures, derived metrics, estimates and AI narrative.
- Demo/seed data must never be mistaken for production customer data.

### 5.3 Performance and scalability
- Server-side pagination/filtering/sorting for high-volume records.
- Bounded queries, suitable indexes, deliberate cache invalidation and asynchronous heavy work.
- Measure realistic API p95/p99, error rate, concurrency, DB utilization, worker throughput, report latency and frontend runtime before claiming performance.
- Cache is never authoritative for authorization, completion, grading, certification or compliance.

### 5.4 UX, accessibility and brand
- Kalam Navy/Blue/Tech/Ice/Gold palette; Geist Sans/Mono; shared tokens/components; canonical K+alam lockup.
- Responsive and keyboard-usable interfaces, visible focus, labels, meaningful loading/empty/error/success/restricted states and safe destructive flows.
- WCAG 2.2 AA target; automated scans plus manual contrast, keyboard, screen-reader and workflow review.
- Evidence-led, globally appropriate copy; no unsupported customer, certification, legal, regulatory or security claims.
- Every screen should explain the task, the evidence/state behind the information and the next accountable action.

### 5.5 Reliability and operations
- Structured logs, request/correlation IDs, metrics, readiness/liveness, worker heartbeat/job visibility and alerting.
- Durable job status, idempotency and retry/backoff.
- Isolated dev, QA, UAT and production environments.
- Off-host DB and file/object backup; restore proof; measured RPO/RTO.
- Exact build artifacts, migrations, health, TLS/secrets, smoke, rollback and release approval required for deployment.

## 6. Architecture and accepted technical decisions

Kalam is a **modular monolith**. Do not split into microservices without measured scale or team-boundary reasons.

| Layer | Current technology / boundary |
|---|---|
| Web | Next.js 16.4.3, React 19.2.8, TypeScript |
| API | Python 3.11, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic |
| System of record | PostgreSQL |
| Cache / supporting infrastructure | Valkey / Redis-compatible service |
| Worker | Separate Python worker for reminders, compliance automation, email/webhooks, scheduled reports and SaaS renewals |
| File safety | Upload validation, ClamAV scanning boundary and S3-compatible production storage abstraction |
| Edge | Gateway/reverse proxy and web/API origin controls |
| External contracts | REST under /api/v1, OpenAPI, signed webhooks and OIDC first |
| AI | Optional policy gateway/provider abstraction, retrieval, prompt/model provenance and safety gates |
| Delivery | Docker Compose baseline, hosted CI and environment-specific secrets/config |

Accepted ADRs cover session-based authentication, explicit tenant ownership, PostgreSQL/Alembic, Redis-compatible worker boundary, abstracted object storage, versioned REST, audit/webhook/learning-event separation, OIDC SSO, production container topology, content-standard adapters and governed AI.

## 7. Authorization and role decisions

### 7.1 Tenant roles
The catalogue includes Tenant Owner, Tenant Administrator, HR / People Administrator, L&D Administrator, Manager, Instructor, Learner / Employee, HR Business Partner, Quality & Compliance, Auditor, Regional Executive and Global Executive. Domain permissions do not remove the need for object/query-level scope in each handler.

### 7.2 Internal SaaS roles
- **SaaS Super Admin:** broad operational grants for CRM, sales, pricing, finance, customer success, customer users, tenant provisioning, role governance, internal team, access revocation and audit.
- **SaaS Administrator:** narrower platform, internal team, customer-success status, audit and integration administration. It is not equivalent to SaaS Super Admin.
- **SaaS Business Owner:** commercial/platform visibility with read-oriented grants.
- **Sales Operations / Sales Viewer / SaaS Finance Administrator / Customer Success Manager:** targeted domain scopes.
- **Platform Developer:** separate engineering/support exception requiring a verified Kalam home account and constrained support context.

Every saas.* permission is internal-only. The persisted home tenant must be the Kalam operations tenant; customer-tenant users must not acquire SaaS rights through stale permission rows. CRM payloads are redacted unless matching domain permissions exist.

### 7.3 Regional / Global Executive
The decision is to use the existing tenant OrgUnit tree, not a second geographic hierarchy. Regional root plus descendants must be tenant-bound, cycle-safe and fail-closed. The helper exists and some People/Organization/Reports surfaces have filters. Regional Executive and Global Executive remain blocked until every other route, aggregate, export, worker, service, file/object and direct lookup path is consistently enforced and database-backed negative tests pass.

## 8. MFA and privileged recovery

The local candidate contains TOTP/recovery services, challenge/lockout/rate-limit work, step-up checks and a candidate API dual-approval reset flow. MFA encryption supports key IDs/key-ring configuration. The reset flow requires a separate requester/approver and invalidates sessions/challenges; it is not a unilateral MFA-disable endpoint.

Still requiring governance and operational evidence:
- Production key provisioning and rotation.
- Resumable ciphertext re-encryption, key-ID/row validation and backup restore with the new key ring.
- Deployed password/OIDC challenge enforcement against the exact candidate.
- Acceptance of the independent-approver policy and offline break-glass ownership.
- Operational reset rejection/cancellation/contact flows and admin UI as required.
- Real provider and browser evidence.

Do not disable MFA or create a privileged-account bypass.

## 9. Local runtime and worker boundary

At the 2026-11-05 inspection:
- Kalam web, API, gateway, PostgreSQL, Valkey and ClamAV containers were running; the first six reported healthy.
- The running worker was still using docker-worker:latest, created 2026-11-01, and had no Docker health check.
- A newer kalam-worker-candidate:20261105 image built and passed module/one-shot heartbeat smoke, but it had **not** been deployed into the running Compose worker.
- One-shot worker output showed an empty cycle. This proves a successful empty cycle/heartbeat, not a persisted business-job side effect or full worker certification.
- Local web and API probes on ports 3000 and 8000 returned HTTP 200; the gateway did not expose the API readiness path tested, which returned 404. This does not establish API outage because direct API readiness returned 200.

## 10. Evidence reconciliation — 2026-11-05

### 10.1 Passing results to reuse within their exact scope

| Evidence | Recorded result | Limitation |
|---|---:|---|
| Capability-gap DB integration | 5 passed | Selected Phase 4 capability/gap tests |
| Tenant-isolation DB tests | 3 passed | Selected Phase 8 DB scope, not full live certification |
| Learner enrollment/completion workflow | 2 passed | Selected targeted journey |
| Manager scope workflow | 2 passed | Selected targeted journey |
| Role catalogue/permission regression | 21 passed | Catalogue/matrix test scope |
| Worker regression | 3 passed | Targeted worker regression |
| Worker image build | exit 0 | Candidate worker image only |
| Worker import/heartbeat one-shot | exit 0 | Empty cycle; no external delivery evidence |
| Dashboard route matrix | 20 checks, 0 failures | Routes/viewports in that matrix only |
| Catalog browser check | 2 checks, 0 failures | Catalog only |
| Hosted CI run #518 | success | Committed HEAD CI, not dirty worktree/deployment |

Do not rerun these to create duplicate logs. First compare source/environment changes and execute only invalidated or uncovered checks.

### 10.2 Current findings requiring correction or qualification

1. **Manifest typing:** local TypeScript check found that apps/web/src/app/manifest.ts used an invalid compound purpose value "any maskable". The local file was corrected to a supported "maskable" value for the 512px icon, and the 192px icon retained "any". The focused local typecheck then exited 0. That correction is now published in this PR branch.
2. **Web lint:** the 2026-11-05 lint log showed zero errors and two unused-import warnings in dashboard-visuals.tsx. A separate earlier exit marker is abnormal; use the detailed lint log as the diagnostic.
3. **Worker static validation:** Ruff reported five findings: import ordering in worker files, an obsolete noqa directive, and broad Exception catches in per-item webhook/report loops. The catches isolate individual failures and allow the batch to continue, so do not narrow them blindly; inspect transaction/rollback behavior and use justified exception types. git diff --check also reported a trailing blank line in an unrelated test file.
4. **Browser responsive evidence:** a full 20-check run initially had 9 failures, mostly profile/account-menu overflow. A later rerun reduced it to one mobile /dashboard/admin overflow (document width 987 vs viewport 743). A separate 20/20 dashboard matrix and a focused people/team 4/4 pass cover different routes/runs and do not invalidate that remaining finding.
5. **Role/capability regression:** a run recorded 23 passed / 3 failed because asyncpg could not authenticate PostgreSQL user test at 127.0.0.1:5432. This is a test-environment credential failure, not proof of three product assertion defects. Use the dedicated isolated test DB with confirmed credentials before retesting.
6. **Worker deployment:** the newer worker image was built, but the running container remains on the old image with no healthcheck. Do not replace it until isolated Compose deployment, dependency/migration readiness and controlled side-effect testing are complete.
7. **Migrations:** retained snapshot/restore evidence exists for disposable PostgreSQL archives, but does not prove the currently running DB is at the current candidate Alembic head or staging is safe. Prior PR evidence documented schema/Alembic-history drift. Verify actual runtime revision against the exact DB before deployment.

### 10.3 Gates not certified

- Full authenticated role-based browser journeys for Super Admin, tenant admin, HR/L&D, manager, instructor, learner, compliance and auditor.
- Live A→B tenant isolation across APIs, browser, exports, object access, reports and async jobs.
- Full learning lifecycle from content access through assessment, completion, certificate and skills evidence with persisted state.
- Live OIDC/JWKS, live rate limiting, real SMTP mailbox receipt, live webhook receiver and deployed ClamAV evidence.
- MFA key lifecycle, production provisioning/rotation/restore and independent reset governance.
- Complete Regional Executive boundary across every data surface; restricted executive roles remain fail-closed.
- Manual accessibility/screen-reader/keyboard review and authenticated visual sign-off.
- Representative load/concurrency and measured p95/error/resource profile.
- Off-host DB and file backups, restore, measured RPO/RTO and executed DR/failover/rollback.
- Target staging deployment with TLS, secrets, migrations, monitoring, alerts and rollback validation.
- Independent security/abuse review, legal/brand claim review, customer UAT and signed release authorization.
- Production smoke and actual rollback record.

## 11. Brand and UI/UX governance

The active brand direction is documented in KALAM_GLOBAL_ENTERPRISE_BRAND_SYSTEM_2026-09-29.md: “Build Capability. Drive Performance.” / “Prove Readiness.”; Kalam is an Enterprise Workforce Capability Platform. The canonical palette is Navy #08243D, Blue #0878C9, Tech #3EA9DD, Ice #EAF5FC, Gold #C99732, Canvas #F4F8FC, white surfaces and accessible ink/muted/border tokens. Geist Sans/Mono and a shared K+alam lockup are prescribed.

The brand audit manifest records an original local-checkout inventory of 593 rows, 92 routes, 83 reusable components, 280 public assets and 97 documentation items. Automated inventory, route, axe and responsive/keyboard scans are useful discovery evidence, but the manifest itself says substantial manual review remains: 200 active surfaces for brand/visual review, 177 terminology, 190 accessibility and 94 content-claim review. In its cited axe scan, 78 protected-route requests resolved to login. Automation therefore does not establish authenticated role coverage or a 9.9 score.

## 12. Requirements governance gaps

1. The original requirements traceability matrix predates the full internal SaaS CRM/finance role model and later MFA dual-control and org-scope changes. Those requirements are documented separately but need first-class IDs linked to implementation and tests.
2. A role catalogue and endpoint matrix exist, but a full role × route × object × data-scope acceptance register is still needed.
3. Regional authorization is a partial implementation/design and not an enabled product role.
4. Integration requirements need per-provider/per-environment handshake and failure evidence, not a generic implemented label.
5. The brand inventory/manual review register must link each active surface to persona, owner, review state, defect and evidence.
6. Evidence must identify exact commit, dirty-tree state, database revision and image digest; local changes, hosted CI, isolated DB and running containers are distinct scopes.

## 13. Optimization principles

- Preserve the modular monolith; do not split into microservices for appearance.
- Consolidate duplicated policy only after identifying every consumer and confirming identical semantics.
- Prefer shared typed contracts and permission helpers while keeping resource-specific scope explicit.
- Tune SQL from query plans and data shape, not speculative indexes.
- Keep Valkey/cache as supporting infrastructure, never the system of record.
- Keep worker jobs idempotent, observable and safe under retry.
- Remove code/assets/packages only after reference/build checks prove safe.
- Use baseline → change → targeted measurement; don't rerun passing suites without invalidation.
- Never weaken MFA, tenant scope, audit, data integrity or recovery to improve performance.

## 14. Expert workstreams

| Workstream | Immediate focus |
|---|---|
| Product / enterprise architecture | Consolidate SaaS, LMS and security requirements into one traceability model |
| Backend / platform | Route-to-requirement and route-to-permission coverage |
| IAM / security | Exact password/OIDC MFA paths, privileged recovery and abuse cases |
| Data architecture / DBA | Actual database revision/schema and migration graph |
| Frontend / UX / brand | Manifest correctness, account-menu responsive defect and route/task quality |
| QA / accessibility | Reconcile existing evidence; cover full critical journeys without duplicate suites |
| DevOps / SRE / integrations | Worker image mismatch, secrets, provider handshakes, monitoring and DR |
| AI governance | Keep disabled by default until provider, source/tenant and safety gates pass |

## 15. Ordered execution

### Priority 0 — Preserve and inventory
- Archive Git status, staged/unstaged diffs, untracked inventory and existing logs.
- Reconcile local/remote refs and PR #38.
- Classify untracked files as source, tests, evidence, generated output, secrets or accidental artifacts.
- Rotate credentials exposed in Developer.txt and remove it safely after preserving legitimate non-secret content.

### Priority 1 — Low-risk quality defects
- Keep the validated manifest icon-purpose correction.
- Verify the remaining account-menu overflow at the exact tablet/mobile width in an isolated browser.
- Remove only truly unused imports.
- Resolve worker Ruff findings with explicit exception/transaction reasoning.
- Run only typecheck, target lint/browser, and worker checks affected by the changes.

### Priority 2 — Security and data correctness
- Verify actual current DB revision/schema in the isolated test DB.
- Prove password and OIDC MFA/session assurance with DB-backed tests.
- Complete approver governance and key lifecycle/restore plan; no production key changes before compatible rollout and restorable backup.
- Inventory all Regional Executive data surfaces; keep role blocked until full acceptance.
- Verify SaaS endpoints against the route matrix and real DB-backed role assignments.

### Priority 3 — Product acceptance
- Run authenticated browser journeys for each major persona and prove persistence.
- Prioritize learner lifecycle, manager scope, L&D publish/enroll, assessment/certificate, compliance evidence/escalation, report execution/export, tenant admin and SaaS tenant/onboarding/finance.
- Prove integrations in a configured target with real handshakes and failure/retry paths.
- Complete manual accessibility and brand/claims surface review.

### Priority 4 — Operations and release
- Deploy candidate worker only to isolated staging; prove heartbeat freshness and a controlled job with persisted side effects.
- Measure load and DB query behavior on representative data before optimizing.
- Verify DB and object/file backup, restore, RPO/RTO, DR/failover, monitoring and alert acknowledgement.
- Reconcile branch changes in a separate clean worktree/review branch, produce an immutable candidate and fresh hosted CI, independent review, owner approvals, staging smoke and rollback evidence.
- Production remains blocked until mandatory gates pass and the authorized release owner signs.

## 16. No-repeat test policy

| Existing result | Decision |
|---|---|
| 5 capability-gap DB tests; 3 tenant-isolation DB tests; 2 learner workflow tests; 2 manager workflow tests; 21 role-catalogue tests | Reuse within exact tested scope; rerun only if covered code/environment changes |
| 20-check dashboard matrix; 2-check catalog test | Reuse for those routes/viewports only; retain separate remaining admin-mobile failure |
| 3 worker tests; worker image build; one-shot import/heartbeat | Reuse for those scopes; not proof of real business side effects |
| Web lint log | Reuse as zero errors/two warnings; typecheck was rerun after manifest correction and passed |
| Role/capability 23 pass / 3 DB credential failures | Do not rerun against invalid credentials; repair isolated DB config first |
| Older full API, security and migration suites | Retain within their documented commit/environment; no blanket reruns |

## 17. Session update and repository publication boundary

- The local discovery report was written additively to qa/certification/KALAM_SYSTEM_REQUIREMENTS_DISCOVERY_2026-11-05.md.
- The local manifest correction was verified with npm --workspace apps/web run typecheck (exit 0).
- A tablet browser regression attempt did not produce a valid result artifact; account-menu responsive verification remains pending.
- A CSS correction for the local account-menu layout was applied to the local working tree, but it was not published by this repository update because the remote branch snapshot did not contain the corresponding local account-menu implementation and the workstation was offline during publication.
- The manifest correction and this requirements audit are published to the existing draft PR branch. PR #38 remains draft and is not approved for merge or production deployment.
- The local checkout has not yet been synchronized to the new remote commits. Preserve its dirty working tree and reconcile the remote commits deliberately when the workstation reconnects.
- No credentials, Developer.txt, database contents, secrets, worker runtime changes or unrelated local changes were published by this update.

**Audit conclusion:** Kalam has broad and substantial functionality, but remaining work is not simply “more development.” The critical task is to close traceability, security enforcement, authenticated end-to-end operation, current-candidate defects and production operational proof without losing or repeating the work already completed.
