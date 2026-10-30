# Kalam System Alignment Audit — 2026-10-11

Status: **INTERIM SOURCE AUDIT — NOT A PRODUCTION CERTIFICATION**

## Executive finding

Kalam has a substantial modular-monolith implementation and a traceable set of product capabilities. The backend has tenant-aware models and API dependencies, workflow tests, a dedicated worker, and explicit production safety checks. The source-level gateway mismatch has now been corrected for both existing browser API prefixes, and legacy unmounted SaaS finance CRUD code has been removed while preserving active endpoints. Kalam is still **not verified end to end or production ready**: the live gateway/web/database paths remain unresponsive, local file storage does not meet the production object-storage ADR, and full regression/browser/release gates remain open.

The requirements baseline is marked “Synthesized implementation baseline”; it is not evidence of approved, customer-validated business requirements. Therefore this audit can assess alignment to the repository’s current baseline, but cannot certify that the baseline itself fully represents Kalam’s business requirements or global-market fit.

## Scope and evidence

Reviewed backend routes and dependencies, ORM models, Alembic history, representative workflow tests, frontend routes and API calls, Next.js API route handlers, Nginx routing, deployment/storage ADRs, requirements traceability, and release acceptance documentation.

Read-only environment checks found:

- Windows had approximately 0.48 GB free RAM during the latest check. Docker Desktop processes own published ports, but Docker CLI/Compose status calls stall. This is consistent with severe runtime/resource pressure; it does not by itself identify a single cause.
- The local FastAPI liveness endpoint on port 8000 returns HTTP 200. Its readiness endpoint times out. The configured `127.0.0.1:55434/corplms` accepts TCP, but a bounded, read-only `SELECT 1` times out. Docker CLI/Compose status calls stall, as do gateway port 3100 `/proxy-health` and web port 3000 `/`.
- A read-only database query was attempted and timed out. No write query, migration, container restart, data cleanup, or database modification was performed. Source changes in this workstream cover gateway smoke checks, finance dead-code cleanup, route contract tests, and this report.
- Static checks before the latest edits: Ruff passed for API app/tests; 163 API tests collected; 24 database-independent tests passed. Latest targeted route-registry tests pass. The database-backed finance test and full suite remain unrun because tests write to a named database and its query path is unresponsive.
- Frontend typecheck, lint, production build, and browser journeys were not run; the host is under severe memory pressure and the application is unreachable.

## Backend and database

### Verified alignment in source

- FastAPI routers are registered centrally under `/api/v1`; authentication uses server-side session records and tenant/permission dependencies. Production settings reject insecure cookies, enabled API docs, development email sink, and private integration targets.
- The ORM contains 98 tables. Tenant ownership is explicit on principal business records; child/join entities often inherit scope through their parent. Reviewed course and assessment routes show tenant-filtered resource lookups and permission dependencies.
- The current Alembic source graph has one head. It contains branch/merge history, so the single head is useful but does not prove any running database is at that revision.
- Tests cover major journeys in source, including enrollment/progress/completion/certificate, assessment grading, compliance, capability evidence, saved reports, SaaS CRM and tenant boundaries. Test collection is not execution evidence.
- Worker code is a separate runtime for reminders, compliance, notifications, webhooks, scheduled reports, and renewal tasks, consistent with the deployment ADR.

### Gaps and risks

1. **Live schema and data state — UNVERIFIED / release blocker.** The configured database endpoint is unreachable. Several named database/container stacks have appeared in prior inventories; the canonical live instance and data equivalence cannot be established from the current engine state. No migration status, row-level integrity, backup, or restore claim should be made until a read-only connection to the explicitly selected database is restored.
2. **Local test isolation — HIGH risk.** `apps/api` settings load `apps/api/.env`, which currently targets `127.0.0.1:55434/corplms`; the main API tests use seeded records and include state-changing workflows. The CI workflow provisions a dedicated PostgreSQL service and seeds it, but a local `pytest` invocation can target the configured development database. Use an isolated test database explicitly before running the full suite.
3. **No database row-level security policies were found in the Alembic source.** Tenant enforcement is application-level. This is not by itself proof of a tenant leak, but it leaves database-level defense in depth absent and increases the importance of exhaustive query-scope testing and review.
4. **Storage implementation does not meet the production ADR.** `LocalStorage` is the only adapter; non-local `STORAGE_BACKEND` values raise an error. The production design calls for private S3-compatible storage. A local Docker volume is suitable for a single-host test, not a resilient multi-instance SaaS storage design.
5. **External integration depth is mixed.** xAPI statement receive/list exists, but SCORM/cmi5 checks validate manifests and LTI checks OIDC discovery; those checks alone do not establish full course launch, package import, runtime tracking, or LTI Advantage conformance. The UI explicitly marks SAML interactive sign-in unavailable. Treat these as partial/integration-readiness capabilities, not complete standards support.
6. **SaaS finance is an internal CRM ledger workflow.** Invoice/payment records and reconciliation exist, but no payment processor/checkout integration was found. If the requirement is automated subscriptions, card collection, tax, dunning, or recurring billing, that workflow is not established by the current implementation.

## Frontend-to-backend alignment

### API routing contract — SOURCE FIX APPLIED; RUNTIME NOT CONFIRMED

The production Nginx gateway now forwards both `/api/lms/*` (rewritten to `/api/v1/*`) and `/api/v1/*` directly to FastAPI. The generic Next.js `/api/lms` catch-all remains available for deployments where requests reach Next.js directly. This preserves the existing URL contracts while resolving the confirmed source-level gateway mismatch.

Browser-side client components use both prefixes. Server-rendered pages using `apiFetch`/`apiJsonResult` call internal `API_ORIGIN` and remain a separate path. The gateway smoke script now checks `/api/v1/health/live` and `/api/lms/health/live`, in addition to web and gateway health.

The code/config mismatch is fixed, but runtime confirmation is pending: the current gateway times out, so the updated Nginx config has not yet been proven loaded and forwarding successfully. After Docker is healthy, validate the config, reload Nginx, and run `infra/scripts/phase8-gateway-smoke.ps1` before closing this gate.

## Duplication and route ownership

- The legacy unmounted CRM contract/invoice/payment handlers were removed from `saas_finance.py`. Active mutations remain in `saas_commercial.py`; three finance query endpoints remain registered by `main.py` at their existing paths. Database-free OpenAPI contract tests protect those endpoints, active CRUD operation IDs, and password-reset compatibility paths. The existing finance workflow test now also asserts the finance overview response.
- API source analysis found no duplicate mounted method/path pairs. The `/api/lms` and `/api/v1` gateway aliases and dedicated auth BFF routes remain intentionally available; do not remove them until their callers and cookie behavior have parity-tested replacements.
- Exact source-content duplicates are limited to empty Python package markers and singular/plural instructor redirect pages. They are harmless and retained. Exact duplicates elsewhere in the worktree are concentrated in copied QA/browser artifacts and were not deleted.
- Alembic revision IDs and ORM table names were unique in source scans (67 migration files and 98 mapped tables).
- Historical task audit `KOGNIVON_TASK_17_BACKEND_API_INTEGRITY_2026-09-29.md` now includes a dated follow-up reconciling its finance-route notes with the current registry; its original dated findings remain historical.

### Workflow coverage from source

The repository’s traceability matrix maps identity, tenant isolation, course delivery, assessment/certification, L&D, compliance, skills, analytics, integrations, AI, and operations to tests. Several corresponding workflow tests exist, but the source audit did not execute them against a clean isolated PostgreSQL database or through the deployed browser. Accordingly, workflows are **implemented in source with test coverage**, not currently verified as operational end to end.

## Plan and business-requirement alignment

- The architecture plan and ADRs align on a modular monolith, web/API/worker topology, PostgreSQL, Redis-compatible queue/cache, and private object storage. Compose provides most of the service topology; object storage is the notable implementation mismatch.
- The release acceptance register remains **OPEN — production/commercial release not approved**, with open gates for target deployment, monitoring, off-host backups, restore verification, disaster recovery, independent security review, accessibility, performance, hosted CI, customer documentation, and legal review.
- Dated task audits and implementation-status documents are historical snapshots. Some statements are stale against this checkout (for example, prior migration heads and the claim that no Git remote is configured). They should not be treated as current runtime evidence.
- The requirements documents provide a useful synthesized capability baseline and traceability, but business-owner approval, customer validation, detailed role/workflow acceptance, and commercial/legal sign-off are not evidenced here. “Globally competitive” is a strategy goal, not a testable acceptance criterion as currently written.

## Audit disposition and next verification gates

**Disposition: NOT FULLY ALIGNED; NOT RUNNABLE/RELEASE-READY IN THE CURRENT ENVIRONMENT.** The gateway API-path source defect is fixed but not runtime-confirmed. Storage and advanced standards/payment integrations are product/deployment gaps depending on the approved release scope. Database integrity and broad workflow correctness remain unverified rather than presumed defective.

Recommended order:

1. Restore host/Docker capacity and the selected database endpoint without removing or resetting volumes; identify the authoritative database and take a verified backup before any migration.
2. Reconcile the selected database’s Alembic revision and schema against `r7s8t9u0v1w2` using read-only inspection first.
3. Create/use an isolated test database, seed it, and run the full API suite plus migration upgrade checks.
4. With Docker stable, validate/reload Nginx and pass the gateway smoke test for both API prefixes.
5. Run the finance integration test and full API suite against an isolated test database, then web typecheck/lint/build and role-based browser journeys across core workflows and tenant boundaries.
6. Decide and implement production object storage and the exact required payment/SCORM/LTI/SAML capabilities; do not mark connection checks as protocol completion.
7. Complete deployment-target security, accessibility, performance, backup/restore, monitoring, rollback, and approval gates before calling Kalam production-ready.

## Follow-up — QA/QC runtime recheck, 2026-10-11

The runtime-unresponsive finding above is a historical snapshot and is superseded for this recheck: `kalam-prod` gateway routes `/`, `/api/v1/health/live`, `/api/lms/health/live`, and `/api/v1/health/ready` returned HTTP 200, and the `kalam-prod` core services reported healthy. `kalam-tunnel` web/API/Postgres/Valkey also reported healthy. A separate `docker` project still has unhealthy `docker-api-1` and `docker-clamav-1`; it was not altered. Runtime responsiveness does not prove current uncommitted source is deployed or that workflows pass.

Fresh exact-worktree checks: frontend TypeScript and ESLint passed; focused database-independent API route-registry/storage-config/S3-adapter/AI-provider tests **21 passed**; Ruff passed on changed backend/test files; Alembic has one head and the knowledge-base migration generates offline SQL. Production Compose config and `nginx -t` on the running gateway passed. The migration was not applied, the full database-backed suite was not run, and no production build or browser journey was completed. The worktree remains dirty. Overall disposition remains **NOT PRODUCTION READY**.

## Follow-up — 2026-10-11

The storage environment mismatch identified during follow-up work is fixed: the API now honors the documented `FILE_STORAGE_ROOT` and `MAX_UPLOAD_BYTES` settings, while retaining compatibility with `STORAGE_ROOT` and `MAX_UPLOAD_MB`. The byte limit takes precedence when both size settings are supplied, and invalid non-positive limits are rejected. Ruff and eight database-free storage-config/route-registry tests pass.

Runtime remains blocked: FastAPI liveness returns 200, but readiness and Redis probes time out; the PostgreSQL read-only `SELECT 1` probe times out; ports 3100 and 3000 time out. Docker Desktop was started for verification, but its engine pipe still does not answer `docker version`; no containers, migrations, or database writes were run. Production object storage and other release gates above remain open.
