# Kalam Certification Matrix

| ID | Gate | Required proof | Current disposition |
|---|---|---|---|
| C0 | Candidate integrity | immutable SHA/tag + clean candidate | OPEN |
| C1 | Hosted CI | exact-candidate CI evidence | PARTIAL / PR-tree evidence |
| C2 | Auth/session | real browser login/session/logout/expiry | NOT CERTIFIED |
| C3 | RBAC | role allow/deny matrix through UI + API | NOT CERTIFIED |
| C4 | Tenant isolation | live A→B negative matrix | NOT CERTIFIED |
| C5 | Learning | enrollment→learning→assessment→completion persistence | NOT CERTIFIED |
| C6 | Capability | completion→capability→gap recalculation | NOT CERTIFIED |
| C7 | API/data | full regression + invariants + bounded reads | PARTIAL / strong CI evidence |
| C8 | Accessibility | automated + manual WCAG review | NOT CERTIFIED |
| C9 | Security | automated/manual security assessment | NOT CERTIFIED |
| C10 | Scale | 10k+ representative load + p95/p99 | NOT CERTIFIED |
| C11 | Backup | production backup freshness + restore + RTO/RPO | PARTIAL / local restore |
| C12 | Rollback | executed migration rollback drill | NOT CERTIFIED |
| C13 | DR | executed failover/recovery | NOT CERTIFIED |
| C14 | AWS | TLS, secrets, migrations, health, monitoring, rollback | NOT CERTIFIED |
| C15 | Observability | failure injection + logs/metrics/alerts | NOT CERTIFIED |
| C16 | Browser E2E | Admin/Manager/Learner and critical roles | NOT CERTIFIED |
| C17 | AI | provider/grounding/safety/override/audit or disabled | NOT CERTIFIED |
| C18 | Independent review | separate final approval | NOT CERTIFIED |
| C19 | Production smoke | exact candidate post-deploy verification | NOT CERTIFIED |

A gate is CERTIFIED only when execution evidence exists for the exact immutable release candidate. IMPLEMENTED and CI PASS are not equivalent to CERTIFIED.
