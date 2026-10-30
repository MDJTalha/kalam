# Kalam Production Readiness — Step 1 Baseline

Date: 2026-10-11
Repository HEAD: `fc872e50b2007cc0f365d7acba0d18dfd928ac7a` (`main`)
Working tree: contains pre-existing and active uncommitted changes; this evidence applies to that working tree and is not a release/commit certification.

## Verification

- API tests: **174 passed** against a uniquely named disposable PostgreSQL database. The database was created on the separate `kalam-tunnel-postgres-1` service, migrated to head, seeded with test-only fixtures, and dropped after testing. The live `kalam-prod` database was not used. Redis DB 9 was reserved for the test run and reported zero remaining keys.
- ClamAV: the clean-file scan returned `(True, "clamd")` through the healthy Kalam API-to-ClamAV network. This was a separate scanner test; an end-to-end upload through the API with the cloud storage provider is still pending.
- API static checks: Ruff passed for `app` and `tests`; mypy passed for 65 application source files.
- Web checks: TypeScript passed; ESLint passed; Next.js production build passed and generated 88 pages/routes using a separate ignored build directory. The generated `tsconfig.json` path additions were removed after the build.
- Compose configuration: development and production Compose files validated. Gateway proxy health and API readiness returned HTTP 200; database and Redis readiness were healthy.
- Storage-specific checks: 9 focused storage/scanner tests passed, including fake-client S3 staging, tenant-key path validation, configuration guards, and upload limits.
- `git diff --check` passed. No source changes were committed.

## Remaining baseline caveats

- The full API suite was run with the standalone ClamAV test excluded because its test runner was on a separate Docker network; the scanner itself passed separately against the running ClamAV service. Actual API-upload-to-ClamAV integration with the future S3 provider remains a Step 3 test.
- The repository preflight script initially omitted its required `NEXT_PUBLIC_SITE_URL` setup. That script was corrected to save, set, and restore the value. Its migration-head check still cannot connect from this Windows host to the database URL in the local API environment. Alembic upgrade-to-head did succeed on the disposable database used for the full suite.
- Pytest emitted one Starlette/httpx deprecation warning. `npm ci` warned that the workspace policy did not approve the `unrs-resolver` install script; frontend lint, typecheck, and production build nevertheless passed.
- The production storage provider is not configured. The running stack still uses local storage; no real S3-compatible upload test or off-host recovery proof has been performed.

## Gate decision

The code/test baseline is established for the current working tree. Do not tag or deploy it as a production release yet: the tree is uncommitted, host migration preflight is not green, provider-backed file workflows and off-host restore are open, and later plan gates remain incomplete.

## Runtime follow-up — 2026-10-11

- Docker Engine is responsive. The `kalam-prod` Compose project has seven running services and one completed migration service; its API, web, worker, PostgreSQL, Valkey, ClamAV, and gateway were present. The tunnel project runs separately with its own PostgreSQL volume.
- `infra/scripts/phase8-gateway-smoke.ps1` passed against `http://127.0.0.1:3100` using the `kalam-prod` API, worker, and migration containers. Gateway and homepage returned HTTP 200; `/api/v1/health/live` and `/api/lms/health/live` returned HTTP 200; expected gateway security headers passed; API readiness reported database and Redis ready; worker was running; migration exited 0; and migration/API image IDs matched. The smoke output recorded the API, web, and worker image digests in the execution transcript.
- This is a local runtime smoke, not an externally reachable or release certification. No containers, database records, migrations, or volumes were changed during this follow-up.
- Multiple Compose projects exist. `corplms-postgres` and `docker-postgres-1` are exited and reference the same named PostgreSQL volume mounted by the running `kalam-prod-postgres-1`; they are not concurrent database processes. `kalam-tunnel-postgres-1` uses a distinct volume. The separate `docker-api-1` and `docker-clamav-1` report unhealthy, while their `kalam-prod` counterparts report healthy. Do not remove or stop the inactive projects/containers until their ownership and data/volume use are explicitly reconciled.
- The source tree remains uncommitted and the production storage configuration still needs an actual private S3-compatible provider and end-to-end upload/download/tenant-isolation verification. Off-host backup and isolated restore, external TLS/monitoring, security review, performance, accessibility, business UAT, and legal approval remain open.

## Backend settings audit follow-up — 2026-10-11

- A focused settings-test rerun found that explicit `APP_ENV="production"` construction was ignored because the setting lacked the `APP_ENV` alias. Added the alias so the production safety validator is exercised consistently.
- The same tests found that the legacy `STORAGE_ROOT` alias overrode `FILE_STORAGE_ROOT` when both were present. Split the legacy field and now apply it only when the canonical setting is absent.
- Focused route/storage test group: **12 passed** after the fixes. Ruff passed for the changed settings module and tests.
- A first broader static-check attempt was interrupted because several parallel analyzers were stalled while the host had about 0.5 GB free memory. Do not count those interrupted checks as passes. The already-completed API Ruff check passed; full re-verification should be serialized after host resources are available.
