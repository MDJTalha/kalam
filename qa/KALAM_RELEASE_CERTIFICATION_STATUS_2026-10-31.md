# Kalam — Release Certification Status
Date: 2026-10-31
Current main candidate observed: `637f6b7481fb6b2b8ca43719e5c4ee924720a465`

## Executive status

**Engineering-hardened / release-candidate pending runtime certification.**

This ledger distinguishes source implementation from independently executed runtime evidence. Kalam must not be labelled production-certified 9.99/10 until every hard gate below has evidence tied to one exact immutable candidate.

## Closed or substantially closed source gates

- Canonical tenant/SaaS role catalogue is merged into mainline with separation-of-duties boundaries.
- Cross-tenant regression coverage exists for governed files, capability/development data, reports, integrations and webhooks.
- Enrollment/completion persistence is implemented.
- Capability-gap recalculation is implemented.
- `requireUser()` separates 401 sign-in, 403 access-denied, and service-failure handling.
- `apiJsonResult()` is the canonical status-aware server API contract. The legacy generic `apiJson()` compatibility helper is removed on the certification branch. All application callers identified by the repository code search were migrated to `apiJsonResult()` with explicit success/null handling; no compatibility helper remains in `server-api.ts`.
- Business-critical Compliance, People, and L&D Operations pages use status-aware API handling.
- Enterprise selectors/read paths have received bounding hardening. Current main also bounds compatibility organization unit/role lists to a validated maximum of 100 and includes regression coverage.
- Backup manifest, SHA-256/size verification and pg_restore catalog inspection are implemented.
- Main CI is configured for API, web and release-configuration validation.

## Hard release blockers

| Gate | Current state | Required evidence |
|---|---|---|
| Exact-candidate CI | MERGE-EQUIVALENT TREE VERIFIED | Hosted PR run #466 passed API/Web/release-config against the exact pre-merge tree; the squash merge preserves that tree. A separate push-triggered run for the merge SHA is not surfaced by the connector. |
| Full API regression | NOT CERTIFIED | Complete suite result and artifact tied to the candidate. |
| Browser E2E | NOT CERTIFIED | Real authenticated role matrix covering admin, HR/L&D, manager, instructor, learner, auditor/compliance. |
| Tenant isolation | SOURCE + REGRESSION COVERAGE | Execute negative A→B access matrix in a live disposable/staging environment. |
| Learning lifecycle | IMPLEMENTED + REGRESSION COVERAGE | Browser/runtime proof: enrollment → learning → assessment → completion → capability update → gap recalculation. |
| Accessibility | PARTIALLY VERIFIED | Automated results plus manual keyboard/screen-reader/responsive review. |
| Scale | NOT CERTIFIED | Representative 10k+ employee load with p95/p99, DB, CPU, memory, concurrency and error evidence. |
| Backup restore | NOT CERTIFIED | Actual clean-database restore, integrity checks and measured recovery duration. |
| DR/failover | NOT CERTIFIED | Executed failover/recovery with measured RTO/RPO. |
| AWS production | NOT CERTIFIED | TLS, secrets, migrations, health checks, monitoring, integrations and rollback evidence. |
| API helper migration | CLOSED | Legacy `apiJson()` helper removed and all identified application callers migrated; merged to main and covered by successful hosted PR CI #466. |
| Reference-data bounds | SUBSTANTIALLY HARDENED / AUDIT OPEN | Compatibility organization lists are now bounded; finish systematic audit for any remaining broad enterprise consumers. |
| AI activation | NOT CERTIFIED | Provider, grounding, safety, tenant isolation, human override and audit evidence before enabling real-provider AI. |

## Exact evidence package

1. Immutable candidate SHA and release tag.
2. Hosted CI run and artifacts for that SHA.
3. Disposable-database full regression output.
4. Browser role matrix, including mobile/responsive checks.
5. Cross-tenant negative matrix.
6. Accessibility automated and manual sign-off.
7. Performance/scale report.
8. Migration forward/rollback evidence.
9. Backup integrity plus actual restore evidence.
10. DR/failover evidence with measured RTO/RPO.
11. Production TLS/security/monitoring smoke evidence.
12. AI certification record if AI is enabled.
13. Independent release approval.

## Environment constraint

The previously connected Desktop Commander device **MDT** is not available for runtime execution in this session. Consequently, this ledger makes no claim that local PowerShell, Docker, PostgreSQL, browser, staging, AWS, backup/restore or DR commands have been executed here.

## Current mainline evidence

- Merged certification candidate: `637f6b7481fb6b2b8ca43719e5c4ee924720a465`.
- PR #29 was merged after hosted CI run #466 (`41213279219`) completed successfully against the exact pre-merge tree: API, Web, and release-config all passed, including production-image runtime smoke.
- The merge commit is a squash of the certification branch; its diff contains the same application migration/removal changes that were exercised by the successful CI candidate.
- The GitHub connector exposes PR-triggered runs only; no separate push-triggered run is currently surfaced for the merge SHA.

## Certification rule

No source-only assertion, historical CI run, or developer declaration substitutes for runtime evidence. **9.99/10 production certification remains blocked until every hard gate is evidenced for the exact immutable candidate.**
