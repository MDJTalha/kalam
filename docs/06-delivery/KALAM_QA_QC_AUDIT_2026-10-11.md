# Kalam QA/QC Audit — 2026-10-11

Disposition: **NOT READY FOR PRODUCTION — functional coverage is partial and full-system acceptance is unverified.**
Audited checkout: branch `main`, HEAD `fc872e50b2007cc0f365d7acba0d18dfd928ac7a`; worktree contains many pre-existing and active uncommitted changes.
Scope: current working tree, safe static checks, database-independent regressions, read-only local runtime probes, and existing dated delivery evidence. No live database writes, migrations, container changes, or deployments were performed.

## Summary

Kalam has substantial frontend/backend implementation and several passing targeted checks. That is not equivalent to proving that all required workflows work. **3 of the 16 release-acceptance checks in the frontend brief have fresh evidence for this checkout (about 19% of the release checklist).** This is verification coverage, not a feature-completion percentage.

The live local `kalam-prod` gateway and core services currently respond and report healthy. A separate `kalam-tunnel` stack is also healthy. Two containers in a separate `docker` stack (`docker-api-1`, `docker-clamav-1`) report unhealthy. The working source is dirty and has not been built into the running web/API images, so runtime checks below do not validate the exact source candidate.

## Checks executed

| Area | Result | Evidence / limit |
|---|---|---|
| Frontend TypeScript | PASS | `npm run typecheck` in `apps/web`, after current login/navigation edits. |
| Frontend lint | PASS | `npm run lint` in `apps/web`, after current login/navigation edits. |
| Focused backend regression | PASS | `python -m pytest tests/test_route_registry.py tests/test_storage_config.py tests/test_storage_s3.py tests/test_ai_provider_adapter.py -q`: **21 passed**; database-independent with mocked S3/provider clients. |
| API static analysis | PASS | Ruff on changed API modules and test files. |
| Alembic graph | PASS | Single head: `k1b2c3d4e5f6`. |
| Migration SQL generation | PASS, offline only | Knowledge-base migration SQL generated from `r7s8t9u0v1w2` to head; migration was not applied. |
| Diff whitespace check | PASS | `git diff --check`; Git emitted line-ending conversion warnings only. |
| Local gateway | PASS, runtime only | `GET /`, `/api/v1/health/live`, `/api/lms/health/live`, `/api/v1/health/ready` on `127.0.0.1:3100` returned **200**. |
| Production Compose configuration | PASS, configuration only | `docker compose -f infra/docker/docker-compose.app.yml config --quiet` with CI validation-only values. No services were started or changed. |
| Running Nginx configuration | PASS, runtime only | `docker exec kalam-prod-gateway-1 nginx -t` reports syntax valid. |
| Main/tunnel Docker services | PASS, health only | `kalam-prod` web/API/gateway/Postgres/Valkey/ClamAV and `kalam-tunnel` web/API/Postgres/Valkey report healthy; worker is running. |
| Separate `docker` stack | FAIL / investigate ownership | `docker-api-1` and `docker-clamav-1` report unhealthy. No container was stopped or changed. |

The browser inventory exposed no browser or tab. Free physical memory was 0.56 GB during runtime checks and about 0.45 GB afterward. Therefore no production build or browser journey was attempted for the exact current source. The deployed containers use existing image IDs and are not evidence for uncommitted source changes.

## Release checklist score

Freshly substantiated checks: **3 / 16 = 18.75%, reported as 19%**:

1. TypeScript check — pass.
2. ESLint — pass.
14. `git diff --check` — pass.

The other 13 checks are open or not evidenced against this exact candidate, including production build, complete route/browser smoke, login/session/logout and password recovery, role journeys, conversion workflows, core end-to-end tasks, negative tenant authorization, viewport/accessibility checks, provider-backed file/integration behavior, browser diagnostics/screenshots, artifact/secret sweep, and owner disposition of remaining limitations.

The focused API test and runtime health probes add useful QA evidence, but they do not satisfy the corresponding end-to-end release checks.

## Material release blockers

1. **Candidate provenance:** the current tree is uncommitted and has not been built or deployed as one identifiable release artifact. Docker health checks refer to existing images.
2. **Authentication and authorization journeys:** no current-source browser proof for developer/super-admin login, cookie persistence, `/auth/me`, logout, recovery, role routing, or cross-tenant denial.
3. **Database-backed workflow suite:** knowledge-base and session integration tests and the full API suite were not run in this audit. Prior 174-test evidence is historical and predates the latest edits. Offline SQL generation is not a migration test against an isolated database.
4. **Frontend workflow acceptance:** no current-source browser run for sales/evaluation submission and CRM readback, or for learner, manager, L&D, compliance, instructor, and executive journeys.
5. **Accessibility/responsive acceptance:** static semantics and previous historical scans are not a current browser/keyboard/screen-reader audit. WCAG 2.2 AA is not certified.
6. **Production operations/integrations:** provider-backed private object storage, end-to-end file scanning/isolation, off-host backup/restore, production TLS/monitoring, performance, external provider certification, UAT, and legal/release approvals remain open in the existing readiness reports.
7. **Runtime hygiene:** investigate the two unhealthy containers in the separate `docker` stack only after ownership/dependency mapping. They were not changed during this audit.

## QA findings from the current implementation increment

The public menu now has click/touch and keyboard disclosure behavior; login tenant discovery now clears stale tenant/SSO state and ignores stale responses; and the no-password/no-SSO state now gives an accurate recovery message. These source fixes pass TypeScript and ESLint, but their browser regressions remain unverified.

## Next audit sequence

The gated execution order, owners/dependencies, safety constraints, and pass criteria are tracked in `KALAM_REMAINING_QA_EXECUTION_PLAN_2026-10-11.md`.

1. Establish adequate memory and a browser session; build the exact current source and record its artifact/image identity.
2. Use an isolated disposable database and run the full current-source API/integration suite, including migration upgrade and tenant-boundary tests. Never use the live customer database.
3. Run authenticated browser E2E for login, session lifecycle, password reset, and the six baseline roles plus tenant/platform-owner separation.
4. Run public conversion and major product workflows with backend persistence/readback, negative authorization, and failure/retry cases.
5. Run the full responsive and accessibility matrix, inspect screenshots, then security/performance/integration/backup acceptance.
6. Re-score only from the requirement-to-test evidence matrix and obtain owner acceptance for any explicitly excluded dependencies.

No deployment approval or “100% complete” endorsement is made by this audit.
