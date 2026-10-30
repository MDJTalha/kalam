# Kalam — Canonical Delivery Roadmap

Version: 1.0 — reconciled 2026-10-27

This document is the single authority for delivery phase numbering. Historical filenames and earlier notes may retain old labels; where they conflict, this roadmap and `PHASE_NUMBERING_AND_ACCEPTANCE_RECONCILIATION_2026-10-27.md` govern.

## Phase 0 — Baseline and repository foundation
**Scope:** requirements, architecture, security/QA baselines, traceability, ADRs, Git/monorepo, environment templates and CI.
**Exit criteria:** documented baseline is internally consistent; local validation passes; hosted CI evidence is recorded for the exact candidate before release.

## Phase 1 — Identity, tenancy and core platform
**Scope:** tenant/org lifecycle, users, authentication/password reset, RBAC, permission checks, sessions, audit events, navigation/settings and migrations.
**Exit criteria:** authn/authz, negative-access, tenant-isolation and migration-safety tests pass.

## Phase 2 — Course and learner core
**Scope:** categories, courses/modules/lessons, content authoring/publishing, enrollment, learner dashboard/player, progress/completion, due dates and notifications.
**Exit criteria:** learner journey and progress persistence pass; duplicate enrollment and content authorization are verified. External SMTP remains a separate provider gate.

## Phase 3 — Assessments and credentials
**Scope:** question bank, assessment authoring/attempts/scoring/manual grading/feedback, certificates, QR verification, expiry and revocation.
**Exit criteria:** scoring/attempt rules, certificate integrity and verification security pass.

## Phase 4 — Corporate L&D
**Scope:** programs, curricula, learning paths, cohorts, manager dashboards, instructor workflows, attendance, bulk assignment, calendar and waitlists.
**Exit criteria:** learner/manager/instructor journeys, assignment rules and tenant authorization pass.

## Phase 5 — Compliance, skills and development execution
Phase 5 is the capability-development workstream and contains two explicit subphases. They are not separate top-level phases and must not shift the canonical Phase 6–8 numbering.

### Phase 5 — Core compliance and skills
**Scope:** compliance requirements/assignment/recurrence/exceptions/escalation/audit reports; skills taxonomy; competencies and role requirements; learner capability profiles; development plans and capability gaps.
**Exit criteria:** governed capability requirements and gap calculations are tenant-scoped, evidence-backed, reproducible and tested.

### Phase 5A — Development Intelligence
**Scope:** multi-modal recommendations for learning, coaching, mentoring, experiential/stretch assignments and evidence-building; provenance, explainable rationale, priority/timeframe, acceptance and stale-recommendation supersession.
**Exit criteria:**
- recommendations originate from current governed gaps and have traceable rationale/provenance;
- user/manager/tenant scopes and permission denials are tested;
- accepting learning recommendations performs the supported enrollment action;
- accepting non-learning recommendations creates the supported executable development action/goal;
- prior learning, urgency, evidence confidence/freshness and criticality influence ranking as specified;
- no actionable recommendation survives after its source gap is superseded or closed.

### Phase 5B — Coaching, Mentoring and Experience
**Scope:** intervention ownership/lifecycle, coaching/mentoring/experiential interactions, evidence capture and verification, capability evidence linkage, gap recalculation and reassessment.
**Exit criteria:**
- a controlled representative-tenant journey proves gap → recommendation → acceptance → intervention → interaction → evidence submission → verification → capability evidence → recalculated gap → reassessment;
- verified evidence and reassessment are auditable, tenant-scoped and cannot be self-approved where separation of duties is required;
- baseline and final levels/gaps, evidence count, improvement and lifecycle states are asserted;
- focused authorization, invalid-state and regression tests pass;
- rendered employee/manager/admin browser and accessibility checks pass before the phase is declared fully accepted.

## Phase 6 — Reporting, analytics and integrations
**Scope:** executive/L&D/manager/compliance dashboards, reports/exports, REST API, webhooks, integration adapters, SSO/OIDC boundary, LTI/xAPI boundaries and scheduled reports.
**Exit criteria:** metric consistency, filtering/pagination, tenant scoping, export/report scheduling, worker execution and webhook signature/replay protections pass locally. External HRIS/IdP/LTI/xAPI/SCORM/cmi5, SMTP and receiver handshakes require actual target credentials and remain explicit external gates.

## Phase 7 — Governed AI
**Scope:** AI gateway, content assistance, summaries, recommendations, authorized-content Q&A, skill-gap explanations, evaluation, human review and audit/observability.
**Mandatory rules:** no permission bypass; no unsupported authoritative claims; no hidden consequential employment decisions; fail closed for missing/invalid provider configuration; source provenance and citation validation for grounded answers.
**Exit criteria:** tenant/role isolation, prompt-injection and citation/grounding controls, evaluation corpus, provider failure/failover, audit/telemetry and human-review workflow pass. Third-party production provider/billing/SLA evidence remains deployment-dependent.

## Phase 8 — Commercial and production release readiness
**Scope:** production deployment, monitoring/alerts, backups and restore, disaster recovery, security, accessibility, performance, customer documentation, legal review, release/rollback and hosted CI/CD.
**Exit criteria:** all applicable gates in `PHASE_8_RELEASE_ACCEPTANCE.md` are PASS for the exact immutable candidate, with evidence links, target/environment, timestamp and named reviewer/approver. Local checks do not substitute for target evidence.

## Global acceptance and release policy
1. A phase is **implemented** when code and documentation exist; it is **locally accepted** only when its explicit local tests/evidence pass; it is **release accepted** only when all applicable target/external gates pass.
2. A release candidate must be tied to an exact commit/tag and API/web/worker image digests. Tests, review and deployment evidence must identify that same candidate.
3. No commit, tag, merge, push, production deployment or commercial-release approval is implied by a green local test.
4. Do not mark an external provider, production TLS, monitoring alert, off-host recovery, rollback, performance/SLA or legal review PASS without real evidence from the applicable target and an accountable reviewer.
5. Any Critical/High security defect, tenant-isolation regression, unverified recovery path or missing mandatory approval is a release no-go.

## Change control
New scope records a requirement ID, business reason, impacted modules, security/testing/architecture impact and release target.
