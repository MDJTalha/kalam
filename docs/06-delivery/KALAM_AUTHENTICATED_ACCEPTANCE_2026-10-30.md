# Kalam Authenticated Local Acceptance Evidence — 2026-10-30

## Scope and isolation

Authenticated acceptance was executed against a dedicated QA stack, separate from the existing local application services:

- PostgreSQL test container: `kalam-role-test-pg`, loopback port `5435`, database `kalam_test`.
- QA API: `127.0.0.1:8001`, explicitly configured with `WEB_ORIGIN=http://127.0.0.1:3001`.
- QA web: `127.0.0.1:3001`, proxy target `127.0.0.1:8001`.
- Existing application services on ports `3000`, `8000`, and `55434` were not stopped or reconfigured by this QA run.
- No production database, AWS resource, deployment, commit, or push was used.
- QA fixture credentials were read locally and were not written to this report or console output.

## Automated API authorization

| Account | Login | `/api/v1/people` | `/api/v1/development/interventions` | `/api/v1/capability-gaps` |
|---|---:|---:|---:|---:|
| Tenant Admin | 200 | 200 | 200 | 200 |
| Manager | 200 | 403 | 200 | 403 |
| Learner | 200 | 403 | 200 | 403 |

The manager and learner were denied tenant-wide people and capability-gap access. The intervention endpoint returned 200 for all three test identities; this is recorded as observed behavior, not a claim that the returned data was exhaustively proven to be scoped by this particular smoke test. Dedicated manager-scope and tenant-isolation tests remain part of the API suite.

## Authenticated browser workflows

| Workflow | Result | Evidence |
|---|---|---|
| Tenant Admin frontend login | PASS | Real login form reached `/dashboard`; `Executive Overview` rendered |
| Capability-gap recalculation | PASS | Real button action returned `Capability gaps refreshed using the governed Phase 4 calculation.` |
| Same-origin API proxy | PASS | Authenticated people lookup returned HTTP 200, 4 items |
| Manager team workspace | PASS | `/dashboard/team` rendered; 1 direct report shown; client-side search filter executed |
| Learner catalog | PASS | `/dashboard/catalog` rendered; course query returned HTTP 200, 24 items |
| Course authoring and publication | PASS | QA admin created course, module and lesson; publish returned HTTP 200 |
| Learner enrollment | PASS | UI confirmed enrollment; persisted API status `enrolled` |
| Lesson completion | PASS | UI confirmed course completion; persisted API status `completed`, progress `100%`, lesson ID present in completed list |

The end-to-end course lifecycle used a uniquely named temporary QA course in the isolated `kalam_test` database. It did not create records in the normal application database.

Detailed machine-readable evidence: `qa/authenticated-role-interactions-20261030.json`.

## Accessibility and responsive smoke

axe-core `4.13.0` was executed in the authenticated learner browser session on three routes:

| Route | axe passes | Incomplete/manual review | Violations | 390px horizontal overflow |
|---|---:|---:|---:|---|
| `/dashboard` | 36 | 2 | 0 | No |
| `/dashboard/learning-paths` | 36 | 2 | 0 | No |
| `/dashboard/development` | 40 | 3 | 0 | No |

This is a scoped learner-workspace accessibility smoke, not a full accessibility certification. Admin, manager, platform and SaaS workspaces still require axe review. Incomplete axe checks require manual review where applicable.

## QA harness correction

The first isolated browser attempt used the web origin on port `3001` while the QA API retained its default `WEB_ORIGIN` on port `3000`. The API correctly rejected state-changing requests with `Origin not allowed`. The isolated API was restarted with the matching QA-only origin; the subsequent admin, manager, learner and course-lifecycle workflows passed. The initial accessibility run against the unavailable web port was invalid and is not counted as evidence.

## Combined local verification

The same working tree passed `infra/scripts/phase8-preflight.ps1` on 2026-10-30:

- Development and production Compose validation.
- Alembic migration-head check (`b2c3d4e5f6a7`).
- Ruff and mypy (65 source files).
- Isolated SaaS operations and deterministic CI fixtures.
- API suite: `223 passed`, one Starlette/httpx deprecation warning.
- Web TypeScript, ESLint and Next.js production build (89 static pages).

## Remaining acceptance and release gates

1. Authenticated browser/API workflows for Platform Developer, SaaS Owner, Sales Operations, trainer/instructor and additional tenant roles.
2. axe-core and responsive review for admin, manager, platform and SaaS workspaces, including manual review of incomplete checks.
3. Explicit negative tests for every restricted action and cross-tenant object access in authenticated browser/API contexts.
4. Real operator account provisioning and login, only after explicit approval.
5. Current production container image/runtime verification and integrated gateway smoke.
6. Hosted CI and staging deployment evidence, followed by post-deployment health checks.
7. Backup/restore and disaster-recovery acceptance against the intended deployment environment.
8. Reviewed release candidate, immutable commit and deployment approval.

## Disposition

**Local Phase 8 preflight: PASS.**

**Authenticated local acceptance: PARTIAL PASS** for Tenant Admin, Manager and Learner workflows, with successful end-to-end learning enrollment/completion and scoped learner accessibility checks.

**Production release certification: NOT GRANTED.** External deployment, full role matrix, broader accessibility and operational recovery evidence remain outstanding.

No repository changes were committed or pushed during this work.

## Additional focused authorization and SaaS regression run — 2026-10-30

After refreshing the deterministic CI fixtures in the isolated PostgreSQL test database, the focused suites completed successfully:

- `tests/test_role_governance.py`
- `tests/test_saas_commercial.py`
- Result: **10 passed, 0 failed**, one existing Starlette/httpx deprecation warning.

The passing test cases explicitly cover:

- SaaS Owner read-only CRM permission and denial of platform operations.
- Platform Developer platform permissions without commercial CRM permissions.
- Sales Viewer read-only CRM permission and denial of platform operations.
- HR Business Partner and Regional Executive templates do not receive unscoped tenant-wide permissions.
- Commercial plan publishing, isolated CRM sandbox access, finance reconciliation guards, renewal task deduplication, plan/offer/subscription/trial guards and cross-tenant finance relationship filtering.

A first direct invocation of these focused tests, without first running the required deterministic CI fixture seeder, produced one invalid-credentials failure because the demo admin fixture was not seeded with that invocation's temporary password. No product-code failure was established by that run. The fixtures were then seeded explicitly and the complete focused suites passed (10/10).

These are API/test-suite authorization results. They do not substitute for real browser login journeys for Platform Developer, SaaS Owner or Sales Operations. No production operator account has been created.

## Sales Operations authorization regression — 2026-10-30

Added `test_sales_operations_can_manage_crm_without_platform_access` to `apps/api/tests/test_role_governance.py`.

The test verifies that Sales Operations receives exactly `saas.crm.read` and `saas.crm.manage`, can read the SaaS plan workspace and create a QA plan, and is denied platform tenant administration, platform health, audit and incident endpoints.

Validation after refreshing deterministic fixtures in the isolated `kalam_test` PostgreSQL database:

- Ruff: PASS.
- Python syntax compilation: PASS.
- `tests/test_role_governance.py` + `tests/test_saas_commercial.py`: **11 passed, 0 failed**, one existing Starlette/httpx deprecation warning.

The QA plan is created in the isolated test database. The temporary test identity is removed by the test cleanup. No production operator identity or production data was created.

## Updated full Phase 8 preflight — 2026-10-30

After adding the Sales Operations permission-boundary regression, the complete `infra/scripts/phase8-preflight.ps1` was rerun against the isolated `kalam-role-test-pg` database. The updated working tree passed every configured gate:

- Development Compose validation: PASS.
- Production Compose validation: PASS.
- Alembic current at all heads (`b2c3d4e5f6a7`): PASS.
- Ruff: PASS.
- mypy: PASS (65 source files).
- Isolated SaaS operations fixture bootstrap: PASS; no operator account created.
- Deterministic CI fixture seeding: PASS.
- Full API pytest suite: **224 passed, 0 failed**, one existing Starlette/httpx deprecation warning (180.77 seconds).
- Web TypeScript typecheck: PASS.
- Web ESLint: PASS.
- Isolated Next.js production build: PASS; 89 static pages generated.

The script concluded: `Phase 8 preflight passed.` This is a local preflight result only. It does not certify staging, AWS deployment, full platform-role browser acceptance, production database migration, backup/restore or disaster recovery.

## Isolated production-image runtime smoke — 2026-10-30

The repository's `infra/scripts/phase8-image-runtime-smoke.ps1` completed successfully against the existing candidate images. The smoke starts isolated containers with `--network none`, probes production-mode behavior and removes the temporary API/web containers in its `finally` block.

Verified image digests:

- API: `sha256:dae397e361f8d0ffde7b4d877378d3b0813b697e15bc786b181df0601e4435dd`
- Web: `sha256:d56bafe19f35f09fad5f82de1a70c297e72d14571b3a8d04b55231ce8132ee33`
- Worker: `sha256:2f35b75c414efe17a4523905b5b85c1f29b07d55c1723e1732fe4edfed59ccd3`

Results:

- API liveness: HTTP 200.
- API readiness without external dependencies: HTTP 503 (expected fail-closed behavior).
- API documentation endpoint: HTTP 404 (production docs disabled).
- Web routes `/`, `/login`, `/dashboard`: HTTP 200.
- Worker image contains callable `run_once`, `process_notification_webhooks` and `process_scheduled_reports` jobs.
- Script reported `integrated_deployment_certified: false`.

This is isolated image/runtime evidence only. It does not establish that the API, web, worker, PostgreSQL, Redis/Valkey, object storage, email, file scanning, ingress and secrets are correctly integrated in a deployed environment. No candidate container was left running by this smoke.

## Trainer / Instructor acceptance scope clarification - 2026-10-30

A read-only review of the current frontend and API implementation clarified the remaining trainer/instructor acceptance scope:

- `/dashboard/instructor` and `/dashboard/instructors` are compatibility aliases that redirect to `/dashboard/sessions`; they are not independent instructor workspaces.
- `/dashboard/sessions` displays the tenant session calendar and scheduling form only when the authenticated user has `courses.manage`. Other authenticated users see sessions for courses in which they are enrolled.
- API session creation is guarded by `courses.manage` (`apps/api/app/api/routes/sessions.py`). Session attendance and analytics enforce facilitator ownership unless the caller has tenant-wide course-management permission.
- Existing API regression coverage in `apps/api/tests/test_foundation_api.py` includes `test_phase4_facilitator_session_analytics_is_scoped_and_accurate` and `test_live_session_schedule_is_visible_to_enrolled_learners_only`, covering attendance analytics, non-facilitator denial, enrolled-learner visibility and cross-tenant instructor rejection. These tests were included in the previously recorded full API suite result (224 passed).

This review does not establish a real trainer/instructor browser journey. Browser acceptance must still verify a dedicated course-management/facilitator identity can schedule and manage an assigned session, while a learner sees only enrolled-course sessions and cannot create sessions or access facilitator analytics. The current browser process on ports 3000/8000 is the normal local application instance, not a confirmed isolated QA deployment; no browser mutations were run against it.

## Isolated release-database role regression rerun - 2026-10-30

The role-governance suite was rerun against the dedicated `kalam-release-test-pg` database (host loopback port 5434), not the normal application database:

- `apps/api/tests/test_role_governance.py`: **5 passed, 0 failed** in 8.87 seconds.
- Covered SaaS Owner read-only access, Platform Developer platform-only access, Sales Viewer read-only access, Sales Operations CRM write access without platform access, and restricted HR Business Partner / Regional Executive templates.
- Four temporary browser-acceptance role identities were created in this isolated release-test database for setup validation and then removed. The role-governance test run independently creates and cleans its own temporary role identities.
- API readiness on port 8000 returned HTTP 200 with database and Redis ready; the web login route on port 3000 returned HTTP 200. The web proxy defaults to API port 8000, and the API launcher explicitly targets the isolated release-test database.

Qualification: this is a repeatable API role-authorization regression run plus service availability evidence. It is **not** a completed authenticated browser journey for these four roles. The Chrome remote-debugging endpoint had no existing page target at inspection, and the role-specific browser flow remains pending. No role browser acceptance is claimed from this run.

### Accessibility evidence validity review — 2026-10-30

A review of `qa/authenticated-browser-accessibility-20261029-authenticated.json` found that its 12 axe runs (36 recorded rule occurrences: `landmark-one-main`, `meta-viewport`, and `region`) are not valid evidence of the Kalam application UI. The captured DOM examples include Chrome network-error-page selectors such as `#main-message` and `#suggestions-list`, rather than Kalam workspace components. The associated earlier browser target was `http://127.0.0.1:3001/...`, while no service was listening on port 3001. The report therefore cannot be used either to certify application accessibility or to claim 36 application defects.

A live, isolated frontend is now confirmed at `http://127.0.0.1:3000/login` (HTTP 200), with the corresponding isolated API at port 8000 responding HTTP 200 on `/api/v1/health/live` and `/api/v1/health/ready`. A fresh Chrome page was opened on the port-3000 login route. Authenticated axe reruns against this fresh page have not yet been completed; accessibility remains **unverified**, not passed. The root `Viewport` declaration currently specifies device width, initial scale 1, and viewport fit cover; it does not explicitly disable user scaling. The dashboard shell already supplies a `<main id="main-content">` landmark for workspace pages.

No application source was changed during this review. No browser test was run against the stale port-3001 target, and no commit, push, deployment, or application database migration was performed.

### Fresh unauthenticated login accessibility probe — 2026-10-30

A fresh Chrome DevTools Protocol page was used against the live isolated port-3000 frontend (not the stale port-3001 target). The login page returned its real Kalam UI: title `Sign in · Kalam`, one `<main>` landmark, a rendered viewport declaration that preserves zoom (`width=device-width, initial-scale=1, viewport-fit=cover`), and the sign-in form. axe-core 4.13.0 completed 35 checks and reported one moderate `page-has-heading-one` violation at the default headless viewport. The page contains a marketing `<h1>`, but the responsive stylesheet hides `.auth-brand` below 900px; the sign-in card heading is an `<h2>`. This suggests a real responsive heading-structure issue that needs a viewport-specific review. This was an unauthenticated login-page probe only; it does not represent authenticated dashboard or role-based accessibility acceptance.

### Responsive login accessibility rerun - supersedes preliminary finding - 2026-10-30

The preliminary single-viewport `page-has-heading-one` result above was not reproducible against the current live frontend. A fresh Chrome DevTools Protocol run against `http://127.0.0.1:3000/login` evaluated axe-core 4.13.0 at three explicit viewport sizes:

- Mobile: 390 × 844 — 36 checks passed; **0 violations**. The visible page heading is `Welcome back` and one `<main>` landmark is present.
- Tablet: 768 × 1024 — 36 checks passed; **0 violations**. The visible page heading is `Welcome back` and one `<main>` landmark is present.
- Desktop: 1440 × 900 — 36 checks passed; **0 violations**. Both the marketing and sign-in `<h1>` elements are visible and one `<main>` landmark is present.

Machine-readable evidence: `qa/public-login-accessibility-responsive-20261030.json`. The earlier preliminary result is retained for audit history but is superseded by this repeatable responsive run. This evidence covers only the unauthenticated login page and the axe rules configured in the probe; it is not a full accessibility conformance audit and does not certify authenticated application routes.

### Login heading remediation and responsive accessibility retest — 2026-10-30

Remediation: changed the always-visible login-card heading from `<h2 id="login-title">` to `<h1 id="login-title">` and updated its scoped CSS selector from `.auth-card-heading h2` to `.auth-card-heading h1`. This ensures a primary heading remains visible when the desktop marketing panel is hidden at responsive widths. The existing staged login component content was preserved; only the heading element was changed in the component.

Fresh Chrome/axe-core 4.13.0 verification against the running isolated frontend (`http://127.0.0.1:3000/login`):

- Mobile 375×812: **36 checks passed, 0 violations**; one visible H1; document width 375px equals viewport width (no horizontal overflow).
- Tablet 768×1024: **36 checks passed, 0 violations**; one visible H1; document width 768px equals viewport width (no horizontal overflow).
- Desktop 1365×900: **36 checks passed, 0 violations**; both the marketing H1 and sign-in H1 are visible; document width 1365px equals viewport width.
- The viewport declaration continues to permit user zoom.

Evidence: `qa/public-login-accessibility-20261030.json`.

Frontend verification after the source change: `npm --prefix apps/web run typecheck` passed; `npm --prefix apps/web run lint` passed; `npm --prefix apps/web run build` passed, compiling successfully and generating all 89 static pages. This is a public login-page accessibility result only. It does not certify authenticated dashboard routes, role-based workflows, or whole-application WCAG conformance.

### Authenticated browser QA safety gate — 2026-10-30

The existing `qa/run_authenticated_role_interactions.py` was inspected before reuse. It is not a read-only accessibility runner: it clears browser cookies, logs in as multiple seeded users, triggers capability-gap recalculation, and creates/publishes a uniquely named course plus module and lesson, then enrolls a learner and completes the lesson. Its output path is also hard-coded to the older `authenticated-role-interactions-20261028.json`. It was therefore not rerun as-is against the current browser session because it would create persistent QA data and overwrite older evidence. Existing historical role-interaction output points at frontend port 3001 and is not accepted as fresh current-browser evidence. A separate read-only authenticated route/axe runner with explicit fixture cleanup is still required.

### Authenticated browser rerun qualification - 2026-10-30

A fresh attempt was made to rerun the existing administrator/manager/learner browser acceptance workflow against the currently active port-3000 frontend and port-8000 API. The frontend rendered correctly, but the deterministic fixture logins returned HTTP 401 for `admin@demo.corp`, `manager@demo.corp` and `learner@demo.corp`; the administrator form also reported an unrecognized organization. Consequently the dependent manager, learner, proxy and course-lifecycle actions did not execute. This run is **blocked by a browser-test fixture/environment mismatch**, not evidence of a product authorization regression. API liveness and readiness remained HTTP 200. The failure output is preserved in `qa/authenticated-role-interactions-20261030-rerun.json`.

The active API's database/fixture provenance must be reconciled with the browser runner before another authenticated run. Do not treat the old port-3001 browser evidence as current port-3000 acceptance. No credentials were printed, no new QA course was created in this failed attempt, and no production database or deployment was touched.

### Browser fixture environment provenance correction - 2026-10-30

A follow-up inspection identified that the temporary browser environment bootstrap is stale and must not be used as evidence of a working isolated fixture. `C:\Temp\kalam_browser_env.py` still targets PostgreSQL host port `15434` with the historical `lms` role, while no listener exists on `15434`. The persisted `C:\Temp\kalam-browser-env-state.txt` is dated 2026-10-28 and is therefore stale state, not proof that the current browser API process is connected to its named database. Current dedicated PostgreSQL containers expose ports `5434` (`kalam-release-test-pg`) and `5435` (`kalam-role-test-pg`); both report configured database/user `kalam_test`. The current port-8000 API is a separate pre-existing process. Accordingly, the 2026-10-30 role-login rerun is **inconclusive for product authentication** because it did not establish and verify a fresh isolated API/database pair before exercising the browser. The earlier 401 results remain preserved as raw diagnostic output but must not be interpreted as an application defect or acceptance result.

Required correction before rerun: provision a fresh isolated browser database using the currently active dedicated test PostgreSQL instance and its authorized credentials; start a new API on an unused port; verify the spawned API process identity and database readiness (not merely an HTTP 200 from an already-running service); start a separate frontend instance with `API_ORIGIN` explicitly targeting that API; then run a read-only administrator/manager/learner route and interaction check. Do not reuse the stale temporary state file, do not target the existing developer API/database, and do not run the legacy course-creation/recalculation workflow as a read-only test.

### Earlier successful authenticated workflow evidence - qualification - 2026-10-30

An earlier same-day artifact, `qa/authenticated-role-interactions-20261030.json` (created 2026-10-30 13:45), was re-examined. It records a successful administrator UI login on frontend port `3001`; administrator capability-gap recalculation returned the expected success message; the same-origin API proxy returned HTTP 200 with four people; manager login returned HTTP 200 and the team route/filter rendered; learner login and catalog query returned HTTP 200 with 24 items; and the dedicated course lifecycle completed with persisted `completed` status and 100% progress. The artifact records an empty failures array.

This is valid historical evidence that the complete role workflow succeeded on the port-3001 instance at that time. It is **not** current port-3000 acceptance evidence, and it does not prove that the currently running API/frontend pair is wired to the same database or fixture set. It also includes a course-creation workflow and must not be described as read-only. Preserve this successful artifact alongside the later inconclusive port-3000 rerun; neither result should be discarded or conflated with the other.

### Static quality gate rerun - 2026-10-30

Fresh local checks after the login-heading remediation and delivery-report updates:

- API Ruff: passed.
- API mypy: passed; 65 source files, no issues.
- Web TypeScript typecheck: passed.
- Web ESLint: passed.
- `git diff --check`: passed (Git emitted only LF-to-CRLF working-copy notices).

The previously recorded frontend production build also passed and generated 89 static pages. These checks do not replace the isolated full API test suite, authenticated port-3000 acceptance, release certification, or deployment evidence.

### Kalam SaaS owner administrator provisioning - 2026-10-30

The persistent account `owner@kalam.global` already existed and was active in the same local development database used by the API settings: PostgreSQL `127.0.0.1:55434`, database `corplms`, operations tenant `kalam`. The account was already assigned the existing `SaaS Administrator` role (`role_kind=platform`); no new role or additional privilege grants were created. Its password was rotated using the application's Argon2id `hash_password` implementation, failed-login counters/lockout state were reset, and any active prior sessions were revoked.

The provisioning script explicitly refused any database target other than the verified local development database and required `APP_ENV=development` plus `SAAS_OPS_TENANT_SLUG=kalam`. A newly started API on port `8003`, loaded from the same `apps/api/.env`, successfully authenticated the account and returned HTTP 200 from `/api/v1/auth/me`. The authenticated response confirmed exactly these permissions: `saas.crm.manage`, `saas.crm.read`, `tenant.manage`, and `tenant.read`. It did not return any `platform.*` permissions. This account is therefore the requested SaaS Administrator, not the separate Platform Developer identity.

A separate frontend instance is running on port `3002` with `API_ORIGIN=http://127.0.0.1:8003` and isolated Next build output `.next-owner-qa`. Its login page returned HTTP 200 and its same-origin organization discovery proxy recognized `kalam`. The actual browser form submission for this account has not yet been independently verified; do not describe the UI login as passed. The existing port-3000/port-8000 pair is separate and is not the verified credential-validation pair.

The password was delivered to the user in the conversation. No plaintext password or password hash was added to repository files. The requested downloadable credential PDF remains pending; do not commit credentials to source control.


### Fresh isolated owner-QA pre-authentication checks - 2026-10-30

A fresh read-only check was completed against the isolated local pair: frontend `http://127.0.0.1:3002` and API `http://127.0.0.1:8003`.

- API root, `/api/v1/health`, `/api/v1/health/live`, and `/api/v1/health/ready` returned HTTP 200. Readiness explicitly reported database and Redis as ready.
- Frontend `/login` returned HTTP 200.
- The same-origin tenant discovery endpoint for `kalam` returned HTTP 200 and recognized the organization as **Kalam**, with password sign-in available.
- A real Chrome browser session rendered the login page at 390px, 768px, and 1440px without horizontal overflow. All three required login fields had associated labels; the page exposed two H1 elements (brand statement and form heading).
- An unauthenticated request to `/dashboard` was redirected to `/login`, confirming the observed client-side route guard.
- No application data was created or modified.

Evidence is saved in `qa/kalam-owner-browser-preauth-20261030.json`. This is **pre-authentication evidence only**. It does not certify the Super Admin browser-form login, authenticated dashboard, role-specific actions, axe-core results, complete Phase 8 acceptance, or production readiness. Those gates remain open.


### Targeted Phase 8 and authorization regression tests - 2026-10-30

The dedicated `kalam-role-test-pg` PostgreSQL container (host port 5435, database `kalam_test`) was confirmed ready and isolated from the local development database. Its Alembic revision was advanced from mergepoint `82cb7d9e1f4a` to current repository head `b2c3d4e5f6a7` on that test database only. Deterministic demo fixtures were then seeded into that isolated test database using an ephemeral test-only password.

Results:

- Tenant isolation, role governance, production database fail-closed, database engine, and seed/support guard tests: **19 passed**.
- Phase 8 compliance operations and manager-scope tests: **6 passed**.
- Combined: **25 passed, 0 failed, 0 errors**.
- One non-blocking Starlette deprecation warning recommends `httpx2` for TestClient integration.

Coverage included cross-tenant course isolation, SaaS Owner/Sales Viewer/Platform Developer/Sales Operations permission separation, direct-report manager scope, learner denial of team routes, compliance recurrence and evidence verification, idempotent escalation, exception expiry, production PostgreSQL fail-closed settings, and support/seed safety guards.

Detailed machine-readable evidence: `qa/phase8-targeted-tests-20261030.json`.

These are **targeted regression results**, not a full API-suite pass or release certification. The isolated test database was the only database migrated or seeded by this test run.


### Full API integration test suite - 2026-10-30

The complete API test suite was run after migrating the isolated role-test PostgreSQL database to the current Alembic head and seeding deterministic CI fixtures into that database.

Command: `python -m pytest tests -q`

Result: **224 passed, 0 failed, 0 errors** in approximately 186 seconds. One non-blocking Starlette deprecation warning recommends using `httpx2` with Starlette TestClient.

The test database was `kalam_test` on the dedicated `kalam-role-test-pg` container at host port 5435. The local development database at port 55434 and production services were not used. The test-only fixture password was generated ephemerally and not written to repository files or printed.

Machine-readable result: `qa/api-full-suite-20261030.json`.

This closes the **local API test-suite gate** for the current working tree. It does not close authenticated browser acceptance, web production build/release gates, independent security review, release-candidate commit/review, or external deployment verification.


### Static quality and production build gates - 2026-10-30

Fresh checks on the current working tree:

- API Ruff: passed (`All checks passed!`).
- API mypy: passed (65 source files, no issues).
- Web TypeScript typecheck: passed.
- Web ESLint: passed.
- Isolated Next.js production build: passed; all 89 static pages generated.
- `git diff --check`: passed. Git emitted only LF-to-CRLF working-copy notices.

The production build used a separate `.next-phase8-final` output directory to avoid colliding with the running owner-QA frontend. Next.js temporarily added that directory's dev-types path to `apps/web/tsconfig.json`; that newly generated path was removed afterward, preserving the pre-existing working-tree configuration. No application source files were intentionally changed by this build verification.

These results close the local static/build gates for this check. They do not close browser-authenticated acceptance or release/deployment gates.


### Phase 8 preflight script - 2026-10-30

Executed `infra/scripts/phase8-preflight.ps1 -SkipTests -SkipBuild` with `KALAM_TEST_DATABASE_URL` explicitly pointed to the dedicated loopback PostgreSQL test database on port 5435.

- Development Docker Compose validation: PASS.
- Production Docker Compose validation: PASS.
- Alembic migration head check: PASS at `b2c3d4e5f6a7`.
- API Ruff: PASS.
- API mypy: PASS (65 source files).
- Web TypeScript: PASS.
- Web ESLint: PASS.
- Script result: `Phase 8 preflight passed.`

Tests and production build were skipped in this invocation because their full independent runs are recorded above. The preflight did not require a clean working tree and did not perform deployment.


### Current-tree API/web/worker image runtime smoke - 2026-10-30

Fresh local QA images were built from the current Kalam working tree (branch `work/kalam-local-changes-2026-10-26`, base commit `a1073cb`; working tree remains dirty):

| Image | Local tag | Image digest |
|---|---|---|
| API | `kalam-api:qa-20261030` | `sha256:779df2d0056854245ea331d0928d4fddaff5b111a7c933c4e7d5f0319ae7381b` |
| Web | `kalam-web:qa-20261030` | `sha256:cd16bffd1ea532ed2715a890ba9dc94edaf16e62159f77f2c1e70751a2aa7f01` |
| Worker | `kalam-worker:qa-20261030` | `sha256:156b4fd11a3152f9568134012b96694b6e99dcd749e1dac7bead4d0c6ad10436` |

The first web prebuilt-runner smoke exposed a packaging issue specific to the alternate QA output directory: Docker's ignore rules excluded the standalone `node_modules` tree. Added narrow `.dockerignore` exceptions for `.next-phase8-final/standalone` and `.next-phase8-final/static`, rebuilt the web image, verified `require.resolve('next')` inside the image, and reran the smoke successfully.

Runtime smoke result:

- API liveness: HTTP 200.
- API readiness without external dependencies: HTTP 503 as expected.
- API docs: HTTP 404 (disabled).
- Web routes `/`, `/login`, `/dashboard`: HTTP 200.
- Worker required job entry points: present.
- Smoke containers used `--network none` and a 256 MB memory limit.
- Script output explicitly records `integrated_deployment_certified: false`.

Production dependency checks:

- `npm audit --omit=dev`: 0 vulnerabilities.
- `pip-audit -r requirements-prod.txt`: no known vulnerabilities found; pip-audit logged cache deserialization warnings but exited successfully.

Machine-readable evidence: `qa/phase8-image-runtime-20261030.json`.

These images are local QA artifacts from a dirty working tree. They are not a release candidate, have not been pushed to a registry, and have not been deployed.


### Production-mode web security headers - 2026-10-30

A fresh local production-mode web image container was queried directly (network isolated, 256 MB limit). All seven assertions passed:

- Strict-Transport-Security present.
- Production Content-Security-Policy omits `unsafe-eval`.
- `X-Frame-Options: DENY`.
- `X-Content-Type-Options: nosniff`.
- `Referrer-Policy: strict-origin-when-cross-origin`.
- `Cross-Origin-Opener-Policy: same-origin`.
- `Cross-Origin-Resource-Policy: same-origin`.

This validates the headers emitted by the local production-mode web image. It does not verify public ingress TLS, HSTS behavior at the actual domain, proxy overrides, or a deployed target.


### Container runtime identity inspection - 2026-10-30

The freshly built local QA images declare non-root runtime users:

- API: `app` (working directory `/app`).
- Web: `nextjs` (working directory `/app/apps/web`).
- Worker: `app` (working directory `/app/worker`).

The API smoke container also ran with a read-only root filesystem and a bounded temporary filesystem, as configured by the runtime smoke script. All temporary QA smoke containers were removed after checks; no smoke containers remain running.


### Final web accessibility remediation and production image verification - 2026-10-30

The homepage accessibility review found a public mobile navigation toggle whose `aria-controls` referenced a panel rendered only while open. Removed that dangling reference; the toggle retains its accessible name and `aria-expanded` state. The homepage capability illustration wrapper was also changed from a generic `div` to a labelled `section`.

After those changes:

- Web TypeScript typecheck: passed.
- Web ESLint: passed.
- Next.js production build: passed; 89 routes generated.
- Final web image rebuilt: `sha256:c7ce4b37d19f24bdc7ec9d5af994cf2e45f03f2d4725a7856d75c38ee28f1f63`.
- API/web/worker runtime smoke rerun: passed; web routes `/`, `/login`, `/dashboard` returned HTTP 200; API liveness 200; docs 404; worker job entry points packaged.
- Production web security-header assertions: all seven passed.
- axe-core WCAG 2.0 A/AA, 2.1 A/AA and 2.2 AA scan on final production image:
  - `/login`: 25 passed checks, zero violations, zero incomplete checks.
  - `/`: 28 passed checks, zero confirmed violations; axe marked one ARIA-value check and 43 contrast nodes as incomplete/manual review, not as confirmed failures. These require manual follow-up before claiming full WCAG conformance.

The final machine-readable image and accessibility evidence is in `qa/phase8-image-runtime-20261030.json`.

This remains local verification only. The working tree is dirty; no release commit, registry push, hosted deployment, or production certification was performed.


### Fresh Manager and Learner frontend sign-in acceptance — 2026-10-30

A fresh browser acceptance run used the isolated Kalam Phase 8 QA stack (web `http://127.0.0.1:3014`, API `http://127.0.0.1:8005`, PostgreSQL container `kalam-phase8-rc-pg` on host port 5436, database `kalam_test`). The deterministic CI fixtures were refreshed against this QA database only. A one-run random fixture password was generated in process memory and was not persisted or printed.

Both Manager and Learner submitted the actual Kalam frontend sign-in form in Chrome using their organization ID and role-specific email. Both reached the authenticated dashboard and received the expected HTTP-only `corp_lms_session` cookie.

| Acceptance check | Manager | Learner |
|---|---|---|
| Frontend sign-in form | PASS | PASS |
| Authenticated dashboard | PASS | PASS |
| Role-specific workspace | Team (`/dashboard/team`) | Learning catalog (`/dashboard/catalog`) |
| Restricted tenant-wide people endpoint | HTTP 403 | HTTP 403 |
| Browser harness | PASS | PASS |

Manager team workspace rendered its one direct report and manager-scoped learning/compliance/development information. Learner workspace rendered the learning catalog. The negative people API checks returned HTTP 403 for both identities. Machine-readable evidence: `qa/authenticated-browser-role-login-workspace-20261030.json`.

The separate final-image lifecycle run recorded learner self-enrollment and lesson completion through the UI, with persisted enrollment status `completed` and progress `100%`; that run used an API-authenticated browser session rather than the frontend sign-in form. A subsequent attempt to repeat that lifecycle using the newly seeded fixture could authenticate and open the catalog, but its test query did not locate the expected seeded course. It is recorded as a harness/query limitation, not a product pass. Therefore the combined evidence establishes real Manager/Learner frontend authentication and role workspaces, plus prior learner lifecycle persistence evidence; a single uninterrupted learner frontend-login-to-completion journey remains a narrow follow-up check.

This closes the Manager/Learner frontend sign-in and role-workspace acceptance checks for the isolated local QA stack. It does not certify hosted staging, public TLS, production infrastructure or disaster recovery.
