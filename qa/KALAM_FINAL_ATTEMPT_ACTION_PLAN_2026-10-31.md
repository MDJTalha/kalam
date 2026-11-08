# Kalam — Final Attempt Action Plan & Execution Control

Date: 2026-10-31
Target: enterprise production readiness
Status: ACTIVE — execution initiated

## Mandate

This program converts Kalam from engineering-hardened/release-candidate pending runtime certification into an evidence-bound production release.

The certification subject is one immutable candidate. No production certification is issued from source inspection alone.

## Current baseline

- Repository: MDJTalha/kalam
- Main candidate observed at program start: 2a26dd18ad57c024d99be5216db77eb76781ca8a
- Existing exact-application-tree hosted evidence: PR #30, run #470 / run ID 41214013410
- Existing local restore evidence: retained PostgreSQL dump restored successfully into a disposable database
- Current blockers: authenticated browser E2E, live tenant-isolation matrix, manual accessibility, 10k+ performance, migration rollback, staging/AWS, DR/failover, observability, AI certification/disablement decision, independent approval

## Execution order

1. Candidate integrity and repository reconciliation.
2. Automated API/web/release regression.
3. Authentication/session and role matrix.
4. Tenant isolation negative matrix.
5. Learning lifecycle persistence.
6. Capability-gap recalculation.
7. Accessibility.
8. Security and abuse-path validation.
9. Performance and 10k+ scale.
10. Backup/restore and RPO/RTO.
11. Migration rollback/forward recovery.
12. Staging deployment and exact-artifact verification.
13. Observability and failure injection.
14. DR/failover.
15. Enterprise identity/integration readiness.
16. AI governance or explicit production disablement.
17. Independent review.
18. Immutable production deployment and smoke.
19. Hypercare and certification refresh schedule.

## Evidence rule

Each gate records:

- exact candidate SHA;
- environment;
- command/test;
- timestamp;
- operator;
- result;
- artifact/evidence;
- reviewer;
- status.

Allowed statuses:

CERTIFIED / PARTIAL / BLOCKED / FAILED / NOT CERTIFIED / DEFERRED.

## Automatic blockers

Authentication bypass, authorization bypass, cross-tenant leakage, privilege escalation, material data corruption, critical security exposure, unrecoverable migration failure, broken core workflow, unverifiable artifact, failed recovery control, fabricated evidence, or failed critical production smoke.

## Current execution constraint

The connected Windows development checkout at C:\Projects\Kalam is not a Git repository; it contains the application tree but does not contain apps/api. Therefore local execution against that checkout must not be represented as exact-candidate certification. GitHub remains the authoritative source for the candidate until a clean certification checkout is established.

## Definition of done

Kalam is production-certified only when every mandatory gate has current evidence tied to the same immutable candidate and the independent release decision is recorded.

Until then the authoritative status remains NOT CERTIFIED.
