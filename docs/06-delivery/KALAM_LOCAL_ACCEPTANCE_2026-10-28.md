# Kalam local acceptance evidence — 2026-10-28

## Scope and change control

- Repository: `MDJTalha/kalam` (private).
- Local working copy: `C:\Projects\Kalam`.
- Branch: `work/kalam-local-changes-2026-10-26`.
- Base HEAD: `a1073cb34bc88e4e2b8cb6a41b622c908e104518`.
- The working tree contains pre-existing staged, unstaged, and untracked changes. No reset, merge, commit, or push was performed during this acceptance pass.
- All test credentials and database credentials were kept out of this report.

## Local gates passed

### API and database

- Isolated PostgreSQL test database: dedicated local container `corplms-postgres-test`, mapped to loopback port `15432`.
- Full API suite: **191 passed, 0 failed** in 160.79 seconds.
- Ruff: passed.
- mypy: passed — 65 source files, no issues.
- Python dependency integrity (`pip check`): passed.
- Production dependency vulnerability audit (`pip-audit -r requirements-prod.txt`): **no known vulnerabilities found**.
- Migration-head check: passed at the current merged migration head.
- Test bootstrap is now explicit: the API test harness requires `KALAM_TEST_DATABASE_URL`; the local preflight rejects non-loopback database hosts to avoid running destructive/fixture tests against shared or production databases.
- SaaS commercial tests now create their minimum operations tenant, role, and permission fixtures when starting from a clean isolated test database.

### Frontend

- TypeScript check: passed.
- ESLint: passed.
- Next.js production build: passed after the accessibility corrections below.
- Public brand blue was darkened to improve text contrast; the capability/readiness heading was corrected to preserve heading order; the affected muted note color was darkened.
- Current-candidate accessibility smoke: **4 routes, 4 axe-core runs, 0 violations, 0 mobile horizontal-overflow findings**. Routes: `/`, `/dashboard/catalog`, `/dashboard/learning-paths`, `/dashboard/development`.
- Browser role/lifecycle acceptance on the production build at the configured origin `http://127.0.0.1:3000`: no reported failures. Administrator login and capability-gap recalculation passed; same-origin API proxy returned HTTP 200; manager filtering passed; learner catalog returned HTTP 200; course/module/lesson creation and publishing passed; enrollment returned HTTP 200; course completion returned HTTP 200 with 100% progress and mapped skill evidence updated.
- The QA scripts now return a non-zero process exit when their report contains failures. The accessibility script default origin is aligned with the configured local web origin.

### Deployment packaging

- Development and production Docker Compose configurations: validated.
- API, web, and worker images built successfully.
- Image runtime smoke: **passed**.
  - API liveness: HTTP 200.
  - API readiness without database/Redis dependencies: HTTP 503, as expected.
  - Production API docs: HTTP 404, as expected.
  - Web routes `/`, `/login`, and `/dashboard`: HTTP 200.
  - Worker job entry points were present.
  - Containers ran as non-root users (`app` / `nextjs`).
- Image digests:
  - API: `sha256:dae397e361f8d0ffde7b4d877378d3b0813b697e15bc786b181df0601e4435dd`
  - Web: `sha256:d56bafe19f35f09fad5f82de1a70c297e72d14571b3a8d04b55231ce8132ee33`
  - Worker: `sha256:2f35b75c414efe17a4523905b5b85c1f29b07d55c1723e1732fe4edfed59ccd3`
- The prebuilt Next standalone runtime stage no longer installs the full development dependency tree. Its traced standalone dependencies are packaged into the runtime image; image smoke verifies that the server starts and serves the expected routes.

## Evidence files

- `qa/full-api-suite-20261028-rerun.log`
- `qa/api-ruff-20261028.log`
- `qa/api-mypy-20261028.log`
- `qa/web-typecheck-final-20261028.log`
- `qa/web-lint-final-20261028.log`
- `qa/web-build-final-20261028.log`
- `qa/web-build-docker-runtime-20261028.log`
- `qa/docker-api-build-20261028.log`
- `qa/docker-web-build-20261028.log`
- `qa/docker-worker-build-20261028.log`
- `qa/pip-audit-verbose-20261028.log`
- `qa/authenticated-role-interactions-20261028.json`
- `qa/candidate-accessibility-smoke-20261028.json`
- `qa/phase8-image-runtime-smoke-20261028.log`

## Release gates still open

These are not local-code claims and cannot be certified by local unit tests or container smoke tests:

1. Hosted GitHub CI must run against the exact reviewed candidate commit; the current local changes are not committed or pushed.
2. A staging deployment must run the same image digests and demonstrate database migration, readiness, ingress/reverse-proxy behavior, and the full authenticated journey.
3. Real deployment credentials and external integrations must be configured and tested in the target environment: object storage, SMTP, identity/OIDC, HRIS, webhook delivery, and outbound egress policy.
4. Backup restore, recovery/rollback, observability and alerting, performance/load testing, and a manual keyboard/screen-reader acceptance pass still require recorded evidence.
5. The integrated deployment certification remains **false** until the above gates are completed and reviewed.

A local green build is evidence of local correctness, not proof that the hosted release is production-ready.


## Follow-up execution pass — 2026-10-28

### Verified in this follow-up
- Reconnected to the local Windows development machine and captured repository state. Existing staged, unstaged, and untracked work was preserved; no reset, commit, push, or merge was performed.
- Local API liveness returned HTTP 200 and readiness returned HTTP 200 with database and Redis both reported ready.
- Isolated PostgreSQL test container `kalam-phase2-pgtest` is bound to loopback port `127.0.0.1:5433`, separate from the installed PostgreSQL service on port 5432.
- Alembic migration to head passed; migration-head check reported `82cb7d9e1f4a` as the merged head.
- Demo seed completed against the isolated test database.
- Ruff passed for the strengthened capability-gap regression test; Python compilation passed.
- Frontend TypeScript check, ESLint, and production build passed. The build used `NEXT_DIST_DIR=.next-kalam-verify`; generated TypeScript include entries created by Next.js for that temporary output were removed afterward.
- `git diff --check` passed.
- API Ruff passed; mypy passed with no issues in 65 source files; `pip check` passed.
- `npm audit --audit-level=high --omit=dev` reported zero vulnerabilities; `pip-audit -r requirements-prod.txt` reported no known vulnerabilities.
- Production Compose validation passed with the gateway bound to `127.0.0.1:3100` and matching API/migration image references.
- ClamAV transport responded `PONG`; saved authenticated browser and accessibility reports show zero recorded failures across the recorded journeys/routes.

### Regression-test improvement
- Strengthened `test_phase4_manager_and_tenant_isolation` to assert that a second tenant cannot retrieve another tenant's capability gaps or snapshots, recalculate another tenant's gaps, or receive a non-empty person-level summary for another tenant's user.
- This new assertion set passed Ruff and Python syntax checks, but was **not executed against PostgreSQL during this follow-up**.

### Still blocked / not certified
- The isolated database migration succeeded, but CI fixture seeding and a fresh full API suite were not completed. The fixture seeder deliberately requires an explicit per-run `CI_FIXTURE_PASSWORD`; the remote execution environment declined the credential-setting operation, so that guard was not bypassed.
- Previously recorded local evidence reports 191 API tests passing; treat that as historical evidence, not a fresh run of the strengthened regression test.
- Hosted CI and staging retries for commit `a1073cb34bc88e4e2b8cb6a41b622c908e104518` failed before runner allocation: the latest attempt has zero steps and no runner ID. GitHub job logs were unavailable, so no code-level failure cause can be established from those runs.
- External staging deployment, real-service integration checks, backup restore/rollback, load/performance tests, monitoring/alerting verification, and manual keyboard/screen-reader acceptance remain open.
- Release certification remains **not granted** until these gates are completed against the exact reviewed candidate.


## Follow-up execution pass 2 — 2026-10-28

### Newly verified results
- CI fixture seeding succeeded against the isolated PostgreSQL test database after explicitly configuring a test-only credential.
- Full API test suite: **191 passed, 1 warning** in 157.52 seconds.
- Targeted capability-gap tenant-isolation test plus Phase 8 tenant-isolation suite: **2 passed**.
- API Ruff check on the CI scope (`app tests`): passed.
- mypy: no issues in 65 source files.
- `pip check`: no broken requirements.
- Frontend typecheck, ESLint, and production build passed before the final contrast-only CSS adjustment; a fresh final build is running separately.
- npm production dependency audit: **0 vulnerabilities**.
- Authenticated role/learner browser journey passed against an isolated local API/database/frontend stack. Administrator login and capability-gap recalculation passed; same-origin proxy returned HTTP 200 with four people records; manager team filtering passed; learner catalog returned HTTP 200 with 13 published courses; course creation, publication, enrollment, lesson completion, and progress retrieval passed.
- Authenticated browser/accessibility run: 3 role API checks, 12 browser route checks, 12 mobile route checks, 12 axe-core runs. After fixing the notification count badge foreground/background contrast, the run reported **0 axe violations and no failures**.
- Updated QA scripts to accept `KALAM_QA_API_URL` so the suite can target a known isolated API instead of silently depending on whichever service happens to occupy port 8000.
- Changed the notification count badge background from the low-contrast gold token to `#805000` with white text; axe-core confirmed the reported WCAG 2 AA contrast failures are resolved.
- Temporary QA services run only on loopback ports 8001, 3001, and 9223 and use the isolated local PostgreSQL test container. They are not production deployments.

### Remaining gates
- Python production dependency audit retry is pending because the first current-run attempt timed out while contacting PyPI; this is a network evidence gap, not a clean audit result.
- Hosted GitHub Actions CI and staging remain failed with no runner allocation and no job steps. The connector could not retrieve useful logs. The local fixes have not been committed or pushed, so hosted workflows have not tested this exact working tree.
- Production staging, external integration credentials, backup restore/rollback, performance/load testing, monitoring/alerting, and manual screen-reader acceptance remain unverified.
- No commit, push, or merge was performed. Release certification remains open.


### Final local gate refresh — 2026-10-28
- After the notification-badge contrast correction, the final frontend typecheck and ESLint passed, and the fresh production build completed successfully with 88 generated pages/routes.
- Python production dependency audit retry completed successfully: **no known vulnerabilities found**.
- npm production dependency audit remained at **0 vulnerabilities**.
- Final CI-scope Ruff, mypy, pip check, and `git diff --check` passed.
- A subsequent standalone Alembic `current` invocation failed to authenticate against the isolated database, although the isolated API health endpoint remained ready and the complete API suite had passed earlier. Do not count this later standalone migration command as a pass; the previously verified migration upgrade/head check remains the migration evidence.
- The only remaining release blockers are external hosted CI/staging and operational acceptance gates listed above. Local QA services are being shut down after evidence capture.


### Follow-up browser and integration execution — 2026-10-28

- Re-seeded the isolated PostgreSQL test database with the existing QA-only credential from the local QA setup file; the credential itself was not printed or written to evidence.
- Ran the targeted tenant-isolation regression and Phase 8 tenant-isolation tests: **2 passed**.
- Ran the complete API suite against isolated PostgreSQL: **191 passed, 1 deprecation warning**.
- Ran authenticated role/lifecycle browser QA against a separately configured API/frontend pair using ports 8011/3011 and an isolated Chrome profile:
  - Administrator login: HTTP 200; capability-gap recalculation button produced the expected success confirmation.
  - Same-origin people proxy: HTTP 200 with 4 records.
  - Manager login: HTTP 200; direct-report filtering worked and retained the expected learner row.
  - Learner login and catalog query: HTTP 200; 14 courses returned.
  - Created a QA course, module and lesson; published successfully; learner enrolled; completion API returned HTTP 200, status completed, and 100% progress. The UI confirmed that mapped skill evidence was updated.
  - Role/lifecycle report recorded **zero failures**.
- Ran authenticated browser/accessibility QA against the same isolated stack:
  - 3 role authentication checks; 12 browser routes; 12 mobile route checks; 12 axe-core runs.
  - **0 axe violations** and **0 recorded QA failures**.
  - All 12 role-route samples reported no horizontal overflow, no unlabeled controls, and no page errors.
- Frontend TypeScript check, ESLint, and production build completed successfully; 88 static pages generated. Temporary .next-kalam-final and .next-kalam-qa include entries were removed from apps/web/tsconfig.json after the build.
- npm audit --audit-level=high --omit=dev reported **0 vulnerabilities**.
- Production Compose configuration validation passed; gateway binding and API/migration image-reference checks passed.
- API Ruff (app tests), mypy (65 source files), and pip check passed. git diff --check passed (only Git line-ending warnings).
- A fresh pip-audit refresh did **not** complete: PyPI timed out during vulnerability-data retrieval. Treat that audit as **not freshly verified** for this execution pass.

### Remaining release blockers (unchanged)
- GitHub Actions CI and staging workflow attempts for a1073cb34bc88e4e2b8cb6a41b622c908e104518 still fail before runner allocation; available job metadata has no runner/step evidence. A successful hosted run is required.
- External staging smoke tests, live-provider integration validation, backup restore/rollback rehearsal, load/performance tests, production monitoring/alerting verification, and manual keyboard/screen-reader acceptance have not been demonstrated.
- The local learner course completion and skill-evidence update were verified, but the full intervention → capability reassessment → gap change chain still needs a dedicated end-to-end acceptance assertion.
- Release certification remains **not granted**; do not mark all phases closed based on local checks alone.

### Follow-up acceptance rerun — 2026-10-28

- Restarted Docker Desktop and the existing isolated `kalam-phase2-pgtest` PostgreSQL container after the earlier test attempt was blocked by the stopped Docker engine. No production database was used.
- Re-seeded only the explicitly configured local PostgreSQL test database with deterministic CI fixtures.
- Re-ran the dedicated Phase 6 verified-evidence → recommendation reassessment lifecycle test together with Phase 8 tenant-isolation tests: **2 passed**, with one existing Starlette/httpx deprecation warning. This resolves the earlier HTTP 401 fixture mismatch; the product test itself now passes when its isolated database is correctly seeded.
- Re-ran authenticated administrator/manager/learner browser journeys: **zero recorded failures**. Administrator recalculation returned the expected success message; the manager direct-report filter and learner catalog worked. Current seeded catalog showed 26 matching courses (24 displayed in the captured viewport/results).
- Re-ran authenticated browser accessibility checks: 3 role authentication checks, 12 browser routes, 12 mobile route checks, 12 axe-core runs, **0 axe violations**, and **0 recorded failures**. No horizontal overflow, unlabeled controls, or page errors were reported in the sampled routes.
- These checks are local acceptance evidence only. Hosted CI/staging, external operational gates, and full intervention-to-capability-reassessment product acceptance beyond the focused regression assertions remain release gates.
