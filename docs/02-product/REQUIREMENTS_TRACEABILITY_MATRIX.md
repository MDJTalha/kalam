# Corporate LMS — Requirements Traceability Matrix

Version: 0.1

| ID | Capability | Module | Phase | Acceptance evidence |
|---|---|---|---:|---|
| AUTH-001 | User login | Identity | 1 | valid/invalid auth tests |
| AUTH-002 | Password reset | Identity | 1 | token expiry and reset tests |
| TEN-001 | Tenant isolation | Tenancy | 1 | cross-tenant denial suite |
| ORG-001 | Org hierarchy | Organization | 1 | CRUD + permission tests |
| RBAC-001 | Role management | RBAC | 1 | allow/deny matrix |
| RBAC-002 | Permission enforcement | RBAC | 1 | API authorization suite |
| AUD-001 | Audit events | Audit | 1 | event evidence |
| CAT-001 | Course catalog | Catalog | 2 | create/publish/search tests |
| CONT-001 | Learning content | Content | 2 | secure content access |
| COURSE-001 | Course player | Learning | 2 | end-to-end learner test |
| ENR-001 | Enrollment | Enrollment | 2 | enrollment workflow |
| ENR-002 | Progress/completion | Learning | 2 | persistence/regression tests |
| ASSESS-001 | Question bank | Assessment | 3 | CRUD + validation |
| ASSESS-002 | Scoring | Assessment | 3 | deterministic scoring tests |
| CERT-001 | Certificate issue | Certification | 3 | certificate workflow |
| CERT-002 | QR verification | Certification | 3 | public verification tests |
| COMP-001 | Mandatory training | Compliance | 5 | assignment/completion tests |
| COMP-002 | Escalation | Compliance | 5 | scheduler/job tests |
| SKILL-001 | Skill taxonomy | Skills | 5 | CRUD/authorization |
| SKILL-002 | Course-skill mapping | Skills | 5 | evidence mapping tests |
| REPORT-001 | Executive analytics | Reporting | 6 | metric reconciliation |
| INT-001 | REST API | Integrations | 6 | OpenAPI/API tests |
| INT-002 | Webhooks | Integrations | 6 | signing/replay tests |
| AI-001 | Governed AI gateway | AI | 7 | policy/tenant isolation tests |
| SEC-001 | Security verification | Security | 8 | security test evidence |
| A11Y-001 | WCAG 2.2 AA target | Accessibility | 8 | automated/manual review |
| OPS-001 | Backup/restore | Operations | 8 | restore evidence |

## Traceability rules

Every production feature must add:
1. requirement ID;
2. design/reference;
3. implementation location;
4. tests;
5. release evidence.

A requirement without test evidence is incomplete.

A test without a business requirement or technical rationale should be reviewed for value.
