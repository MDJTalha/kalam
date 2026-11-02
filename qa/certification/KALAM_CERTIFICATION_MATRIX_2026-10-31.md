# Kalam Certification Matrix

Candidate baseline: `main` at `5be4d6d52e9b01f3762a5a41b02bb742ffc44319` (observed 2026-11-02). A clean local mainline worktree was verified at this SHA. No production release tag is asserted.

| ID | Gate | Required proof | Current disposition |
|---|---|---|---|
| C0 | Candidate integrity | immutable commit identity + clean candidate checkout | CERTIFIED for source identity only; no release tag or production release approval |
| C1 | Hosted CI | hosted checks on the candidate | PARTIAL; PR #36 head run #520 passed all four jobs; no separate post-merge run on merge SHA is recorded here |
| C2 | Auth/session | real browser login/session/logout/expiry | NOT CERTIFIED |
| C3 | RBAC | role allow/deny matrix through UI + API | NOT CERTIFIED |
| C4 | Tenant isolation | live tenant A-to-B negative matrix | NOT CERTIFIED |
| C5 | Learning | enrollment-to-learning-to-assessment-to-completion persistence | NOT CERTIFIED |
| C6 | Capability | completion-to-capability-to-gap recalculation | NOT CERTIFIED |
| C7 | API/data | full regression + invariants + bounded reads | PARTIAL; strong historical/PR CI evidence, not full live workflow certification |
| C8 | Accessibility | automated + manual WCAG 2.2 AA review | NOT CERTIFIED; manual authenticated-screen review remains open |
| C9 | Security | automated/manual security and abuse-path assessment | NOT CERTIFIED |
| C10 | Scale | 10k+ representative load + p95/p99 | NOT CERTIFIED |
| C11 | Backup | current backup freshness + restore + measured RTO/RPO | PARTIAL; historical disposable restore only; archives are dated 2026-09-29 |
| C12 | Migration safety/rollback | forward upgrade of retained snapshots + executed rollback drill | FAILED for the tested retained pre-phase8 snapshot forward-upgrade path due schema/Alembic-history drift; rollback drill NOT EXECUTED |
| C13 | DR | executed failover/recovery | NOT CERTIFIED |
| C14 | AWS | TLS, secrets, migrations, health, monitoring, rollback | NOT CERTIFIED |
| C15 | Observability | failure injection + logs/metrics/alerts + recovery | NOT CERTIFIED |
| C16 | Browser E2E | authenticated Admin/Manager/Learner and critical workflows | NOT CERTIFIED |
| C17 | AI | provider/grounding/safety/override/audit or verified disabled posture | NOT CERTIFIED for this mainline certification package; no real-provider activation authorized |
| C18 | Independent review | separate final approval | NOT CERTIFIED |
| C19 | Production smoke | exact candidate post-deploy verification and rollback | NOT CERTIFIED |

A gate is CERTIFIED only when execution evidence exists for the exact immutable release candidate. IMPLEMENTED, source scans, and PR-head CI are not equivalent to full production certification. C0 is limited to source identity and clean-checkout provenance; it does not certify release readiness.
