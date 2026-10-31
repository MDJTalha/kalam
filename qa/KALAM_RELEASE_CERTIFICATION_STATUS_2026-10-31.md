# Kalam — Release Certification Status
Date: 2026-10-31
Current main candidate observed: `0846b2b15e3c6ec64458804f4b35e30b43d07d0e`

## Executive status

**Engineering-hardened / release-candidate pending runtime certification.**

This ledger distinguishes source implementation from independently executed runtime evidence. Kalam must not be labelled production-certified 9.99/10 until every hard gate below has evidence tied to one exact immutable candidate.

## Closed or substantially closed source gates

- Canonical tenant/SaaS role catalogue is merged into mainline with separation-of-duties boundaries.
- Cross-tenant regression coverage exists for governed files, capability/development data, reports, integrations and webhooks.
- Enrollment/completion persistence is implemented.
- Capability-gap recalculation is implemented.
- `requireUser()` separates 401 sign-in, 403 access-denied, and service-failure handling.
- `apiJsonResult()` is the canonical status-aware server API contract. The legacy generic `apiJson()` compatibility helper is removed. All identified application callers were migrated with explicit success/null handling.
- Business-critical Compliance, People, and L&D Operations pages use status-aware API handling.
- Enterprise selectors/read paths have received bounding hardening. Current main also bounds compatibility organization unit/role lists to a validated maximum of 100 and includes regression coverage.
- Backup manifest, SHA-256/size verification and pg_restore catalog inspection are implemented.
- Main CI is configured for API, web and release-configuration validation.

## Hard release blockers

| Gate | Current state | Required evidence |
|---|---|---|
| Exact-candidate CI | MERGE-EQUIVALENT TREE VERIFIED | Hosted PR run #477 (ID `41215669267`) passed API/Web/release-config for the final certification-evidence tree; the application tree remained unchanged from the exact PR #30 application tree. PR #33 then passed hosted run #478 (ID `41215769207`) for the evidence-collection bound hardening before merge. |
| Full API regression | CERTIFIED FOR EXACT APPLICATION TREE | Hosted PR #30 run #470 (ID `41214013410`) executed the complete API suite against the exact application tree that was subsequently carried forward; the API job completed successfully with **182 passed, 0 failed**, one dependency deprecation warning, in 80.06 seconds. PR #33 run #478 (ID `41215769207`) also passed after adding bounded legacy evidence collection reads and regression coverage. |
| Browser E2E | NOT CERTIFIED | Real authenticated role matrix covering admin, HR/L&D, manager, instructor, learner, auditor/compliance. |
| Tenant isolation | SOURCE + REGRESSION COVERAGE | Execute negative A→B access matrix in a live disposable/staging environment. |
| Learning lifecycle | IMPLEMENTED + REGRESSION COVERAGE | Browser/runtime proof: enrollment → learning → assessment → completion → capability update → gap recalculation. |
| Accessibility | PARTIALLY VERIFIED | Automated results plus manual keyboard/screen-reader/responsive review. |
| Scale | NOT CERTIFIED | Representative 10k+ employee load with p95/p99, DB, CPU, memory, concurrency and error evidence. |
| Backup restore | LOCAL RESTORE VERIFIED / PRODUCTION RECOVERY OPEN | A retained recovery-drill PostgreSQL dump was restored successfully into a disposable local database and removed afterward. Production backup freshness, off-host retention, measured RTO/RPO and candidate-tied recovery remain open. |
| DR/failover | NOT CERTIFIED | Executed failover/recovery with measured RTO/RPO. |
| AWS production | NOT CERTIFIED | TLS, secrets, migrations, health checks, monitoring, integrations and rollback evidence. |
| API helper migration | CLOSED | Legacy `apiJson()` helper removed and all identified application callers migrated; covered by successful hosted PR CI #470. |
| Reference-data bounds | HARDENED FOR IDENTIFIED LEGACY EVIDENCE GAP / AUDIT OPEN | PR #33 bounds `GET /api/v1/evidence` to 1–100 records with validated offset pagination and regression tests; continue systematic audit for any remaining broad enterprise consumers. |
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

## Latest execution evidence

See `qa/KALAM_FINAL_CERTIFICATION_EXECUTION_2026-10-31.md`.

Verified during the current execution window:

- Desktop Commander device MDT was online.
- Local PostgreSQL, Valkey and ClamAV containers were healthy/running.
- Development and production Compose validation passed.
- The installed `C:\Projects\Kalam` checkout is not the GitHub certification checkout and lacks `apps/api`; the release preflight therefore stopped instead of generating false API certification evidence.
- The installed local web application returned HTTP 200 for `/login`.
- A retained PostgreSQL recovery dump was actually restored into disposable database `kalam_restore_verify_20261031`; restore exit code was 0.
- The restored database contained 99 public tables and the dump inventory contained 99 TABLE DATA entries.
- The disposable restore database was dropped after verification.
- AWS CLI authentication is expired; active Kubernetes context is `docker-desktop`. No cloud production certification is claimed.

## Current mainline evidence

- Current main candidate: `0846b2b15e3c6ec64458804f4b35e30b43d07d0e`.
- PR #30 hosted run #470 (`41214013410`) completed successfully against the exact application tree: API, Web and release-config, including production-image runtime smoke. PR #32 run #477 (`41215669267`) and PR #33 run #478 (`41215769207`) also passed before their respective merges.
- No separate push-triggered workflow run for the merge SHA is exposed by the available GitHub connector; hosted PR evidence is tied to the exact pre-merge trees.

## Certification rule

No source-only assertion, historical CI run, or developer declaration substitutes for runtime evidence. **9.99/10 production certification remains blocked until every mandatory gate is evidenced for the exact immutable candidate.**
