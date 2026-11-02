# Kalam Master Production Certification Plan

Candidate baseline: `main` at `5be4d6d52e9b01f3762a5a41b02bb742ffc44319` (observed 2026-11-02).
Status: **NOT CERTIFIED** — runtime, migration, operational, and independent-review evidence gates remain open.

This package operationalizes the Kalam production-certification standard. Certification is evidence-bound and candidate-bound. The candidate SHA must be re-established if `main` advances.

## Mandatory evidence chain

Requirement → implementation → test → execution → evidence → review → acceptance → certification.

## Gates

1. Candidate integrity and clean immutable checkout
2. Build and hosted CI on the candidate
3. Authentication/session lifecycle
4. RBAC and resource authorization
5. Cross-tenant isolation
6. Learning lifecycle persistence
7. Capability-gap recalculation
8. API/data integrity and invariants
9. Accessibility/WCAG 2.2 AA automated and manual review
10. Security and abuse-path assessment
11. Performance/10k+ scale
12. Backup freshness and restore
13. Migration forward-upgrade and rollback
14. DR/failover
15. AWS/staging TLS, secrets, migrations, health, monitoring, and rollback
16. Observability and failure recovery
17. Authenticated real-browser E2E
18. AI governance and provider activation controls (or verified disabled posture)
19. Independent review
20. Production smoke and rollback

## Automatic failures

Cross-tenant leakage, privilege escalation, broken authentication/authorization, material data corruption, critical security exposure, unrecoverable migration, unverifiable candidate identity, fabricated evidence, or materially broken core workflow.

## Evidence rules

- Source code and historical CI establish implementation confidence, not live operational readiness.
- Every result must name the exact candidate SHA, environment, command/workflow, timestamp, outcome, and retained artifact or log.
- PR #36 was merged as `5be4d6d52e9b01f3762a5a41b02bb742ffc44319`. Hosted PR run #520 passed on its PR head `5e4484d98c11eee884a00f8a9c1e3a441a0f194c` across `brand-governance`, `api`, `web`, and `release-config`. This is recorded as PR-head evidence, not a separately verified post-merge workflow run.
- The clean local mainline worktree at the merge commit passed `node qa/brand-contract-check.mjs`, scanning 485 web/public source and asset files. Dependencies were not installed in that worktree, so no local full application build is claimed.
- Earlier disposable PostgreSQL restore drills succeeded, but archives dated 2026-09-29 do not establish current backup freshness.
- The tested retained pre-phase8 snapshot failed forward migration due schema/Alembic-history drift (`users.preferences` existed while Alembic reported `b3c4d5e6f7g8`; a subsequent attempt encountered a pre-existing `support_cases` table). No blind Alembic stamp or speculative migration patch is accepted as a remedy. Fresh-database migration had previously reached Alembic head `s1t2u3v4w5x6`.

## Current blockers

Authenticated browser E2E, live RBAC and tenant-isolation matrices, learning/capability lifecycle runtime proof, manual accessibility, 10k+ performance, migration remediation and rollback, current backup/RTO/RPO, executed DR/failover, AWS/staging TLS/secrets/monitoring/rollback, observability failure recovery, AI governance review, and independent final approval.

## Certification decision

Until all mandatory evidence is tied to one immutable candidate and independently accepted: **NOT CERTIFIED**.
