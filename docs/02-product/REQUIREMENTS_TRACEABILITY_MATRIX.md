# Corporate LMS — Requirements Traceability Matrix

Version: 0.2
Status: Phase 0 traceability baseline reconciled 2026-09-28

This matrix is the Phase 0 control that links the requirements baseline to delivery modules and verification evidence. A later phase may deepen a requirement, but it must not remove the requirement ID or its evidence obligation.

| ID | Capability | Module | Phase | Implementation / design reference | Verification evidence |
|---|---|---|---:|---|---|
| AUTH-001 | User login | Identity | 1 | auth API + login UI | `test_foundation_api.py`; protected-route/browser QA |
| AUTH-002 | Password reset | Identity | 1 | reset-token API + reset UI | foundation auth tests; reset expiry tests |
| AUTH-003 | Logout | Identity | 1 | logout route/session invalidation | foundation auth/session regression |
| AUTH-004 | Session expiry/security | Identity | 1 | session model + security sessions UI | foundation session tests |
| AUTH-005 | Account lock/rate limiting | Identity | 1 | auth policy/config | negative authentication tests |
| USER-001 | User profile | People | 1 | people/profile workspace | people API + authorization regression |
| USER-002 | Role assignment | RBAC | 1 | user administration/admin center | permission/role assignment tests |
| TEN-001 | Tenant isolation | Tenancy | 1 | tenant-scoped DB/API contract | cross-tenant denial suite |
| ORG-001 | Org hierarchy | Organization | 1 | organization units/reporting lines | CRUD + permission tests |
| RBAC-001 | Role management | RBAC | 1 | role/permission administration | allow/deny matrix |
| RBAC-002 | Permission enforcement | RBAC | 1 | server-side permission dependencies | API authorization suite |
| AUD-001 | Audit events | Audit | 1 | append-oriented audit trail | audit-event regression |
| CAT-001 | Course catalog | Catalog | 2 | catalog routes/components | course/catalog regression |
| CAT-002 | Categories/tags | Catalog | 2 | catalog taxonomy | category/tag authorization tests |
| CAT-003 | Prerequisites/visibility/ownership | Catalog | 2 | course governance fields | course governance tests |
| CONT-001 | Learning content | Content | 2 | modules/lessons/files | secure content access + scanner tests |
| COURSE-001 | Course player | Learning | 2 | learner course player | end-to-end learner test |
| COURSE-002 | Draft/publish lifecycle | Learning | 2 | Course Studio | publish/state-transition regression |
| ENR-001 | Enrollment | Enrollment | 2 | enrollment APIs/operations | enrollment workflow |
| ENR-002 | Progress/completion | Learning | 2 | progress/completion persistence | persistence/regression tests |
| ENR-003 | Due dates/reminders | Learning | 2 | due-date worker/notifications | worker + notification tests |
| ENR-004 | Capacity/waitlist | Learning | 2/4 | enrollment governance | waitlist/capacity regression |
| ASSESS-001 | Question bank | Assessment | 3 | assessment administration | CRUD + validation |
| ASSESS-002 | Scoring | Assessment | 3 | protected answer-key scoring | deterministic scoring tests |
| ASSESS-003 | Attempts/pass rules/time limits | Assessment | 3 | assessment runner | attempt-rule regression |
| ASSESS-004 | Manual grading/feedback | Assessment | 3 | audited grade override | grading/audit regression |
| CERT-001 | Certificate issue | Certification | 3 | certificate service/UI | certificate workflow |
| CERT-002 | Public verification/QR | Certification | 3 | verify route/code | public verification tests |
| CERT-003 | Expiry/renewal/revocation | Certification | 3 | credential lifecycle | credential lifecycle tests |
| LND-001 | Programs/cohorts | Corporate L&D | 4 | programs/cohort workspaces | program/cohort regression |
| LND-002 | Learning paths | Corporate L&D | 4 | learning-path editor | path CRUD/assignment tests |
| LND-003 | Instructor/session/attendance | Corporate L&D | 4 | session/instructor workspaces | facilitator/attendance regression |
| LND-004 | Manager team workflow | Corporate L&D | 4 | team/manager workspace | manager scope/assignment tests |
| LND-005 | Bulk assignment/equivalency | Corporate L&D | 4 | L&D operations | bulk/equivalency regression |
| COMP-001 | Mandatory training | Compliance | 5 | compliance requirements/assignments | assignment/completion tests |
| COMP-002 | Escalation | Compliance | 5 | compliance automation worker | scheduler/job tests |
| COMP-003 | Recurrence/expiry | Compliance | 5 | recurring requirements | recurrence lifecycle tests |
| COMP-004 | Exceptions/evidence | Compliance | 5 | evidence and exception workflows | compliance evidence tests |
| SKILL-001 | Skill taxonomy | Skills | 5 | skill framework | CRUD/authorization |
| SKILL-002 | Course-skill mapping | Skills | 5 | course/skill evidence mapping | evidence mapping tests |
| SKILL-003 | Role skill requirements | Skills | 5 | capability framework | role requirement regression |
| SKILL-004 | Learner skill profile/gaps | Skills | 5 | learner capability profile | gap/intelligence regression |
| DEV-001 | Development plans | Capability | 5 | development planner | plan/goal persistence tests |
| REPORT-001 | Executive analytics | Reporting | 6 | analytics workspace/reports API | `test_report_metrics.py` |
| REPORT-002 | Saved/scheduled reports | Reporting | 6 | reporting scheduler | `test_report_scheduler.py` |
| REPORT-003 | CSV/export evidence | Reporting | 6 | report export API | report export regression |
| INT-001 | REST API | Integrations | 6 | FastAPI/OpenAPI boundary | foundation/integration API tests |
| INT-002 | Webhooks | Integrations | 6 | webhook routes/service | `test_webhook_delivery.py`; `test_webhook_secrets.py` |
| INT-003 | Integration registry/test | Integrations | 6 | integrations API/UI | `test_integrations.py` |
| AI-001 | Governed AI gateway | AI | 7 | AI governance/service/UI | AI governance/security suites |
| AI-002 | Authorized retrieval/citations | AI | 7 | retrieval/grounding service | retrieval quality/security suites |
| AI-003 | Provider governance/budget | AI | 7 | provider/model/policy controls | provider/failover/budget tests |
| SEC-001 | Security verification | Security | 8 | security baseline + release gate | security regression evidence |
| A11Y-001 | WCAG 2.2 AA target | Accessibility | 8 | design system/accessibility plan | automated axe + manual review |
| OPS-001 | Backup/restore | Operations | 8 | operations runbooks | restore evidence |
| OPS-002 | Monitoring/readiness | Operations | 8 | monitoring probes/runbooks | monitor/readiness smoke evidence |

## Cross-cutting requirements

| ID | Requirement | Design / control | Verification |
|---|---|---|---|
| DATA-001 | Referential integrity and explicit statuses | domain model + database constraints | migration/model regression |
| DATA-002 | Duplicate prevention/idempotency | service/API design | duplicate-request regression |
| DATA-003 | Traceable bulk operations | audit + bulk operation design | audit/bulk regression |
| UI-001 | Responsive, consistent navigation | frontend design-system baseline | responsive/browser route QA |
| UI-002 | Keyboard/focus/labels/state messaging | WCAG 2.2 AA baseline | axe + keyboard/manual QA |
| UI-003 | Loading/empty/error/confirmation feedback | UI component baseline | component/workflow QA |
| GOV-001 | Material changes are controlled | change-control policy + ADR process | change record/ADR review |
| CI-001 | Reproducible quality gate | `.github/workflows/ci.yml` + Phase 0 validator | local validator + hosted CI run |

## Traceability rules

Every production feature must retain a requirement ID, implementation/design reference, test evidence and release evidence. A requirement without an evidence obligation is incomplete. New material scope must update this matrix before release acceptance.

## Phase 0 exit interpretation

The requirements baseline is now traceable to delivery modules and explicit verification families. Later phase exit documents provide the dated execution evidence for those requirements. Phase 0 establishes traceability; it does not claim later-phase functionality is complete.
