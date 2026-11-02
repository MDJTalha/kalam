# Kalam Master Production Certification Plan

Candidate baseline: 0846b2b15e3c6ec64458804f4b35e30b43d07d0e
Status: NOT CERTIFIED — runtime evidence gates remain open

This package operationalizes the Kalam production-certification standard. Certification is evidence-bound and candidate-bound.

## Mandatory chain
Requirement → implementation → test → execution → evidence → review → acceptance → certification.

## Gates
1. Candidate integrity
2. Build and hosted CI
3. Authentication/session
4. RBAC/resource authorization
5. Tenant isolation
6. Learning lifecycle
7. Capability-gap recalculation
8. Data/API integrity
9. Accessibility/WCAG review
10. Security assessment
11. Performance/10k+ scale
12. Backup/restore
13. Migration rollback
14. DR/failover
15. AWS production/TLS/secrets/monitoring
16. Observability
17. Real-browser E2E
18. AI governance (or explicitly disabled)
19. Independent review
20. Production smoke/rollback

## Automatic failures
Cross-tenant leakage, privilege escalation, broken authentication/authorization, material data corruption, critical security exposure, unrecoverable migration, unverifiable candidate identity, fabricated evidence, or materially broken core workflow.

## Evidence rule
Source code and historical CI may establish implementation confidence, but cannot replace live browser, staging/AWS, scale, recovery, rollback, accessibility, or independent-review evidence.

## Current known evidence
- Hosted PR application-tree regression evidence exists: PR #30 run #470, API 182 passed / 0 failed, with Web/release-config and production-image runtime smoke.
- PR #33 hardened legacy evidence pagination and passed hosted run #478.
- Local disposable PostgreSQL restore has been executed successfully.
- Current main is 0846b2b15e3c6ec64458804f4b35e30b43d07d0e.

## Current blockers
Browser E2E, live tenant-isolation matrix, manual accessibility, 10k+ performance, migration rollback, production AWS/TLS/observability, executed DR/failover, AI certification if enabled, and independent final approval.

## Certification decision
Until all mandatory evidence is tied to one immutable candidate: NOT CERTIFIED.
