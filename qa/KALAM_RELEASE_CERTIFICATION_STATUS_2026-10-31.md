# Kalam — Release Certification Status
Date: 2026-10-31
Candidate baseline: `592444df15df1aa666da8cf8a1fac731334c2ab4`

## Executive status

**Engineering-hardened / release-candidate pending runtime certification.**

This ledger deliberately distinguishes source implementation from independently executed runtime evidence. Kalam must not be labelled production-certified 9.99/10 until every hard gate below has evidence tied to the exact immutable candidate.

## Closed or substantially closed source gates

- Canonical tenant/SaaS role catalogue is merged into mainline with separation-of-duties boundaries.
- Cross-tenant regression coverage exists for governed files, capability/development data, reports, integrations and webhooks.
- Enrollment/completion persistence is implemented.
- Capability-gap recalculation is implemented.
- `requireUser()` correctly separates 401 sign-in, 403 access-denied, and service failure handling.
- `apiJsonResult()` preserves HTTP status and API error detail.
- Enterprise selectors/read paths have received pagination/bounding hardening, including webhook listing.
- Backup manifest, SHA-256/size verification and pg_restore catalog inspection are implemented.
- Main CI is configured for API, web and release-configuration validation.

## Hard release blockers

| Gate | Current state | Required evidence |
|---|---|---|
| Exact-candidate CI | NOT CERTIFIED | Fresh hosted API/Web/release-config run for the immutable candidate SHA. |
| Full API regression | NOT CERTIFIED | Complete suite result and artifact tied to the candidate. |
| Browser E2E | NOT CERTIFIED | Real authenticated role matrix covering admin, HR/L&D, manager, instructor, learner, auditor/compliance. |
| Tenant isolation | SOURCE + REGRESSION COVERAGE | Execute negative A→B access matrix in a live disposable/staging environment. |
| Learning lifecycle | IMPLEMENTED + REGRESSION COVERAGE | Browser/runtime proof: enrollment → learning → assessment → completion → capability update → gap recalculation. |
| Accessibility | PARTIALLY VERIFIED | Automated results plus manual keyboard/screen-reader/responsive review. |
| Scale | NOT CERTIFIED | Representative 10k+ employee load with p95/p99, DB, CPU, memory, concurrency and error evidence. |
| Backup restore | NOT CERTIFIED | Actual clean-database restore, integrity checks and measured recovery duration. |
| DR/failover | NOT CERTIFIED | Executed failover/recovery with measured RTO/RPO. |
| AWS production | NOT CERTIFIED | TLS, secrets, migrations, health checks, monitoring, integrations and rollback evidence. |
| API helper migration | PARTIALLY CLOSED | Review remaining generic `apiJson()` callers and migrate business-critical paths to status-aware handling. |
| Reference-data bounds | HARDENING INCOMPLETE | Finish audit of broad enterprise reference-data consumers and bound/search/paginate them. |
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

The connected Desktop Commander device **MDT** is currently offline in this session. Consequently, this ledger makes no claim that local PowerShell, Docker, PostgreSQL, browser, staging, AWS, backup/restore or DR commands have been executed here.

## Certification rule

No source-only assertion, historical CI run, or developer declaration substitutes for runtime evidence. **9.99/10 production certification remains blocked until every hard gate is evidenced for the exact candidate.**
