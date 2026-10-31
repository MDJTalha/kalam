# Kalam — Release Certification Status
Date: 2026-10-31
Candidate baseline: `592444df15df1aa666da8cf8a1fac731334c2ab4`

## Purpose

This document is the release-gate ledger for the current mainline candidate. A gate is only marked **CERTIFIED** when repository evidence or an independently reproducible runtime result exists. Source implementation is not treated as runtime certification.

## Current evidence

| Gate | Status | Evidence / required closure |
|---|---|---|
| Canonical tenant/SaaS role catalogue | IMPLEMENTED | Role catalogue is merged into mainline; separation-of-duties boundaries are encoded in the role/permission model. |
| Tenant object isolation | IMPLEMENTED + REGRESSION COVERAGE | Cross-tenant coverage exists for governed files, capability/development data, reports, integrations and webhooks. |
| Capability → development lifecycle | REGRESSION COVERAGE | Persisted lifecycle regression exists; live disposable-database execution remains a runtime gate. |
| Enrollment/completion persistence | IMPLEMENTED | Learning persistence path exists; live browser/runtime proof remains required for release certification. |
| Capability-gap recalculation | IMPLEMENTED | Recalculation is integrated into governed evidence/development flows; live lifecycle proof remains required. |
| Authentication 401/403 semantics | SOURCE CLOSED | `requireUser()` maps 401 to sign-in and 403 to access-denied; service/network failures fail closed to service-unavailable. |
| API error semantics | PARTIALLY CLOSED | `apiJsonResult()` preserves HTTP status and error details and has been adopted by critical screens; generic `apiJson()` callers remain and require continued migration/review. |
| Large-list safety | HARDENED | Multiple enterprise selectors/read paths are paginated or bounded. Webhook listing is now explicitly capped at 100. Remaining broad reference-data consumers require continued audit. |
| Backup integrity evidence | IMPLEMENTED | Backup manifest, SHA-256/size verification and pg_restore catalog inspection are implemented. Actual restore/failover execution is still an operational certification gate. |
| CI static/build/release gates | CONFIGURED | Main CI includes API dependency/migration/fixture/static/type/test gates, web type/lint/build, production compose/Nginx/image/runtime smoke validation. A fresh successful run for this exact merge candidate must be archived before release certification. |
| Authenticated browser E2E | NOT CERTIFIED | Requires a live disposable/staging environment and role accounts. |
| Full API regression | NOT CERTIFIED LOCALLY | Historical local runtime instability prevented a clean full-suite certification. CI evidence must be tied to the exact candidate. |
| Accessibility certification | PARTIALLY VERIFIED | Automated accessibility coverage exists; final role/screen responsive review and release sign-off remain required. |
| 10k+ scale certification | NOT CERTIFIED | Requires representative resource-sized infrastructure and measured p95/CPU/memory/query/payload/concurrency evidence. |
| Production AWS verification | NOT CERTIFIED | Requires production-authorized evidence for TLS, migrations, secrets, integrations, monitoring, backups, restore, DR and rollback. |
| AI provider activation | NOT CERTIFIED | AI remains fail-closed/disabled by default; provider handshake, policy, grounding, safety and tenant-isolation tests are required before activation. |

## Hard release blockers

1. No clean authenticated browser run covering the role matrix on the release candidate.
2. No independently archived full API/web regression result tied to the exact candidate.
3. No production-authorized AWS/TLS/migration/observability/rollback evidence.
4. No executed backup restore/failover evidence demonstrating recovery objectives.
5. No representative 10,000+ employee performance/scale report.
6. Remaining generic `apiJson()` callers must be reviewed and business-critical callers migrated to status-aware result handling.
7. Remaining unbounded enterprise reference-data consumers must be closed or explicitly bounded with searchable/paginated alternatives.
8. AI provider certification must remain a prerequisite to enabling real-provider AI.

## Certification rule

Kalam must not be labelled **production-certified 9.99/10** while any hard blocker above is unresolved. The correct state is **engineering-hardened / release-candidate pending runtime certification**.

## Required evidence package

- Exact candidate SHA and immutable release tag.
- Hosted CI run URL and all job results.
- Disposable-database full regression artifact.
- Browser role matrix with desktop/mobile evidence.
- Cross-tenant negative matrix results.
- Accessibility automated + manual review record.
- Performance/scale report.
- Migration forward/rollback evidence.
- Backup integrity + restore evidence.
- DR/failover evidence with measured RTO/RPO.
- Production TLS/security/monitoring smoke evidence.
- AI provider certification record, if AI is enabled.
- Independent release approval.

## Important environment constraint

The connected Desktop Commander device `MDT` is currently offline in this session. Therefore this document intentionally does not claim that local PowerShell, Docker, browser, database, AWS, backup-restore or staging commands were executed from this session.
