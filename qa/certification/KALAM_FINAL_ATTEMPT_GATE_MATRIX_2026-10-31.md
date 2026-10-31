# Kalam Final Attempt — Gate Matrix

Date: 2026-10-31
Candidate at program start: 2a26dd18ad57c024d99be5216db77eb76781ca8a

| Gate | Status | Evidence required |
|---|---|---|
| C0 Candidate integrity | OPEN | Clean certification checkout, exact SHA, dependency/build manifest |
| C1 Hosted CI | PARTIAL | Exact immutable candidate workflow evidence |
| C2 Authentication/session | NOT CERTIFIED | Real browser login/session matrix |
| C3 RBAC/resource authorization | NOT CERTIFIED | Positive and negative role/action matrix |
| C4 Tenant isolation | NOT CERTIFIED | Live A→B negative access matrix |
| C5 Learning lifecycle | NOT CERTIFIED | Browser + persistence + completion evidence |
| C6 Capability intelligence | NOT CERTIFIED | End-to-end recalculation and reporting evidence |
| C7 API/data integrity | PARTIAL | Clean-candidate full regression plus integrity checks |
| C8 Accessibility | NOT CERTIFIED | Automated + manual WCAG 2.2 AA review |
| C9 Security | NOT CERTIFIED | Final security/abuse-path assessment |
| C10 Scale | NOT CERTIFIED | 10k+ representative load evidence |
| C11 Backup/restore | PARTIAL | Current backup freshness + restore + measured RTO/RPO |
| C12 Migration safety | NOT CERTIFIED | Forward migration + rollback/forward-recovery drill |
| C13 DR/failover | NOT CERTIFIED | Executed failover with measured RTO/RPO |
| C14 AWS/staging | NOT CERTIFIED | Exact artifact, TLS, secrets, migrations, health, rollback |
| C15 Observability | NOT CERTIFIED | Failure→alert→diagnosis→recovery evidence |
| C16 Browser E2E | NOT CERTIFIED | Critical-path role matrix |
| C17 AI governance | NOT CERTIFIED | Provider/safety/tenant/audit evidence or explicit disablement |
| C18 Independent review | NOT CERTIFIED | Independent reviewer decision |
| C19 Production smoke/rollback | NOT CERTIFIED | Immutable production deployment + smoke + rollback readiness |

## Release rule

No production deployment while any mandatory gate is FAILED or NOT CERTIFIED.

PARTIAL is not equivalent to CERTIFIED.

A DEFERRED gate requires explicit owner acceptance, risk, mitigation and review/expiry date.

## Current known evidence

- Hosted PR #30 run #470 / run ID 41214013410 passed API/Web/release-config for the exact application tree later squash-merged to main.
- The complete API suite in that run passed 182/182.
- A retained PostgreSQL recovery dump was physically restored into a disposable database and verified.
- Current local Windows checkout is not a Git repository and must not be used as exact-candidate evidence.

## Required certification package

Release manifest, exact SHA, workflow artifacts, browser matrix, RBAC matrix, tenant isolation matrix, accessibility report, security report, scale report, backup/restore evidence, migration evidence, DR evidence, staging/AWS evidence, observability evidence, AI decision, independent review, owner approval, production smoke and rollback record.
