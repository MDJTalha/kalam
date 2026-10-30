# Kalam Complete System Audit — Refreshed Evidence Register

**Audit date:** 11 October 2026 (Asia/Karachi)
**Repository:** `C:\Projects\CorpLMS`
**Branch / HEAD:** `main` / `fc872e50b2007cc0f365d7acba0d18dfd928ac7a`
**Audit status:** **NOT RELEASE READY — exact-source acceptance and several P0/P1 gates remain open**
**Audit mode:** Read-only source/runtime inspection and safe static / focused tests. No product source, database records, migrations, containers, named volumes, passwords, or production settings were intentionally changed during this audit. This audit report is an additional artifact.

---

## 1. Executive disposition

Kalam has substantial product implementation and a healthy local production-style runtime. The current source also passes useful code-quality checks. However, neither a green gateway smoke nor a successful build/static check proves that the current repository is what the runtime is serving.

The most important findings are a **candidate/runtime mismatch** and multiple current-source security/data-workflow defects:

- The source working tree is dated by changes through 11 October and contains an additional tenant-scoped knowledge-base feature and migration.
- The running API and web images were created on 4 October. The running API image lacks fields now present in the source configuration.
- The running database is at Alembic revision `r7s8t9u0v1w2`; the current source's Alembic head is `k1b2c3d4e5f6`.
- New knowledge-base API routes return HTTP 404 through the currently running gateway, although the source route contract tests pass.
- Production configuration in the current source now requires S3 storage, while the running API is configured for local storage and the running image does not contain the S3 configuration fields.
- **The active database is missing `public.webhook_deliveries`**, but the worker still queries and writes to it. The current Alembic path creates and later drops this table without recreating it in a subsequent upgrade migration.
- Source review also identifies critical outbound-integration risks: webhook SSRF, tenant-controlled AI provider references capable of resolving process-wide secret names, and OIDC metadata endpoints used without the same outbound destination validation.

**Therefore, the running service is usable for a limited local smoke, but it does not certify the current working tree. The webhook table defect is directly confirmed in the active database. Do not declare the whole system, frontend, or current candidate green from these runtime checks.**

### Audit decision

| Area | Current audit disposition |
|---|---|
| Current-tree web typecheck and lint | **PASS** |
| Current-tree API Ruff and mypy | **PASS** |
| Focused database-free API tests | **PASS — 14 tests** |
| Running gateway / public-route smoke | **PASS — running images only** |
| Running API readiness | **PASS — three consecutive probes** |
| Current source deployed to runtime | **FAIL / confirmed mismatch** |
| Current source migration applied to active DB | **FAIL / confirmed migration drift** |
| Knowledge-base UI/API end-to-end | **FAIL against running runtime — endpoints return 404** |
| Current-source full API suite | **NOT RUN — isolation / volume safety must be resolved first** |
| Current-source production build / browser journeys | **NOT RUN — host has under 1 GB free RAM and runtime build is old** |
| Production storage target / recovery | **NOT VERIFIED; running API uses local storage** |
| Complete tenant/role browser/security acceptance | **OPEN** |
| Production/commercial acceptance | **OPEN — no release approval** |

---

## 2. Environment and source identity

### 2.1 Repository state

- Branch: `main`
- HEAD: `fc872e50b2007cc0f365d7acba0d18dfd928ac7a` (commit date 10 October 2026)
- Remote configured: `origin` → `https://github.com/MDJTalha/kalam.git`
- The worktree contains approximately **52 changed/untracked status entries** across API, frontend, tests, migrations, Docker/Nginx, documentation and QA artifacts.
- The source inventory contains **92** frontend `page.tsx` files, **82** frontend component files, **68** Alembic migration files and **37** Python API test modules. These are inventory counts, not coverage or readiness percentages.

**Control:** do not reset, clean, discard, rebase or overwrite any current worktree changes as part of closure. Before promoting a release, review all changed and untracked files, then create an immutable candidate whose revision and image digests are recorded.

### 2.2 Resource constraint

At audit time, Windows reported around **0.87 GB free RAM out of 7.71 GB**. To avoid destabilizing the environment, this audit did not run a full Next.js production build, a large full API suite, or broad parallel analyzers. These checks must be performed after the test runner and resource envelope are made reliable.

### 2.3 Runtime stack inventory

The Docker engine is responsive. The main `kalam-prod` stack's gateway, web, API, PostgreSQL, Valkey and ClamAV services reported healthy; the worker was running without a configured Docker health status. The API readiness endpoint returned `database=ready` and `redis=ready` on three consecutive probes.

Other stacks remain present:

- The duplicate `docker` stack has an unhealthy API and unhealthy ClamAV; its worker and gateway are exited.
- The separate `kalam-tunnel` stack has healthy web/API/PostgreSQL/Valkey services while its gateway and worker remain in `Created` state.
- `phase8rc` and `phase8rc2` include old `Created` and `Exited` containers.
- The stopped `docker-postgres-1` and `corplms-postgres` containers reference the same canonical PostgreSQL volume currently mounted by `kalam-prod-postgres-1`. The tunnel database uses a **different** volume.

No stale container or volume was removed. Do not restart old database containers or remove any volume without proving ownership, data equivalence and a verified backup.

---

## 3. Evidence captured during this audit

### 3.1 Current-source checks

| Check | Result | Notes |
|---|---|---|
| `npm run typecheck:web` | **PASS, exit 0** | Current worktree |
| `npm run lint:web` | **PASS, exit 0** | Current worktree |
| `git diff --check` | **PASS, exit 0** | Only Windows line-ending normalization warnings |
| API Ruff: `.venv\Scripts\python.exe -m ruff check app tests` | **PASS** | Current worktree |
| API focused tests | **14 passed in 10.61 s** | Route registry, storage config and mocked S3 tests only; no database integration |
| API mypy | **PASS** | 65 application source files |
| Root Docker Compose syntax | **PASS** | Does not build or start services |
| Production Compose syntax | **PASS** | Representative validation environment only; does not prove a configured S3 service exists |
| Source Alembic head | **`k1b2c3d4e5f6`** | Includes current knowledge-base migration |

### 3.2 Running-runtime checks

The gateway at `http://127.0.0.1:3100` returned HTTP 200 for `/`, `/pricing`, `/contact-sales`, `/guided-evaluation`, `/login`, `/integrations`, `/trust`, `/implementation`, both API liveness paths (`/api/v1/health/live` and `/api/lms/health/live`), and API readiness. The gateway smoke also passed its expected security-header checks, verified a ready database/Redis response, found migration container exit code 0 and found the production worker running.

Tenant discovery for `kalam` succeeded and reported a recognized tenant with password sign-in available and no SSO providers. `/api/v1/auth/me` returned HTTP 401 without a cookie, which is expected for an anonymous request; it does **not** prove successful authentication.

The gateway smoke used these running image digests:
- API: `sha256:818056c7d47269f944934815035d590b80ddd49fc368ec9815f7926ad79576b6`
- Web: `sha256:43522a7c4d4a6c68283c03c3da8e811c2266ae9f02e3626e3eca7eaa4efc5f18`
- Worker: `sha256:f41e12a69ebf8bfc5e20447dbc38e1a8af7fea83e4ebdba365953954e38f3002`

The API and web images were created on 4 October; they are not an exact build of the 11 October source.

---

## 4. Release-blocking findings

### AUD-001 — Current repository source and live images are not the same candidate

**Severity:** P0 — release blocker
**Status:** Confirmed

**Evidence**
- Current worktree has extensive source changes through 11 October.
- Live API and web images were created on 4 October.
- The live API configuration lacks the current source's `s3_bucket` field.
- Current-tree routes/features are not all present in the deployed API.

**Impact**

Tests against the current source and smoke checks against the old runtime can disagree. A green result from one cannot stand in for the other. Deploying only some current components risks API/schema/frontend contract mismatches.

**Required closure**
1. Review current tracked and untracked source changes without deleting any.
2. Produce an immutable release candidate from the reviewed source.
3. Build API, web and worker from that exact candidate.
4. Record source revision, build time, image digests and migration head.
5. Prove the deployed API/web/worker digests match that candidate before running final smoke and browser tests.

**Acceptance:** all release test evidence names the exact source revision and matching runtime image digests.

### AUD-002 — Active database migration revision is behind the current source

**Severity:** P0 — release blocker
**Status:** Confirmed

**Evidence**
- Active `kalam-prod` database reports `r7s8t9u0v1w2`.
- Current source's head is `k1b2c3d4e5f6`.
- The new current-source migration adds `knowledge_articles` and depends on `r7s8t9u0v1w2`.

**Impact**

The current ORM/API expects a schema change the active database has not received. Even if routes are built into a new image, the database-backed feature cannot be accepted until its migration is applied through a controlled release.

**Required closure**
1. Establish which database volume is authoritative and capture a verified backup before migration.
2. Test upgrade and downgrade behavior on a disposable database copied/seeded from an appropriate baseline.
3. Validate schema, foreign keys, indexes and migration version.
4. Schedule the approved migration against the authoritative database only after the candidate has passed isolated tests.
5. Run post-migration integrity checks and document evidence.

**Safety rule:** do not run `alembic upgrade head` on the live DB as an audit experiment.

### AUD-003 — Current knowledge-base frontend has no matching route in the live API

**Severity:** P1 — functional release blocker
**Status:** Confirmed against the current running runtime

**Evidence**
- Current source adds tenant-scoped knowledge article list, detail, create and update endpoints.
- The route-registry tests cover the expected paths and pass in the current source.
- Live calls through the current gateway returned HTTP 404 for `/api/v1/support/knowledge`, `/api/lms/support/knowledge` and `/api/v1/support/admin/knowledge`.

**Impact**

The current Help & Support source calls an API surface that does not exist in the deployed older image. The feature will fail in the current runtime.

**Required closure**
- Build and deploy API and frontend from the same candidate.
- Apply the knowledge-base migration safely.
- Run the database-backed `test_knowledge_base.py` against an isolated migrated DB first.
- Verify published-only learner visibility, tenant isolation, admin draft visibility, create/edit/publish/archive/restore and refresh persistence in a browser.

**Acceptance:** all article actions pass through the exact candidate, and a second tenant cannot read or modify the article.

### AUD-004 — New production storage guard and CI image-smoke script conflict

**Severity:** P1 — CI/release pipeline blocker
**Status:** Strong static finding; exact candidate runtime not built in this audit

**Evidence**
- Current source validator rejects `APP_ENV=production` unless `STORAGE_BACKEND=s3`, and requires `S3_BUCKET` when S3 is selected.
- `infra/scripts/phase8-image-runtime-smoke.ps1` launches API and worker with `APP_ENV=production` but does not pass `STORAGE_BACKEND` or `S3_BUCKET`.

**Impact**

When CI builds an image from the current source and executes this script, the smoke containers are expected to fail during configuration/startup because storage defaults to local and production mode rejects it. The historical image could pass because it used an older settings validator.

**Required closure**
- Make the smoke use an explicit safe test configuration consistent with production safety validation (for example, an isolated placeholder S3 bucket value for a network-isolated smoke that never performs an upload).
- Ensure API, worker and migrate runtime envs satisfy the same production validation contract.
- Add a static/CI guard that fails when required production settings are omitted.
- Run the full image-runtime smoke on the exact candidate.

**Acceptance:** candidate CI completes image-runtime smoke successfully without disabling production safeguards.

### AUD-005 — Preflight may contend with the live PostgreSQL data volume; full tests are not safely isolated

**Severity:** P0/P1 — audit/test safety blocker
**Status:** Confirmed configuration risk

**Evidence**
- Root `docker-compose.yml` gives its PostgreSQL service the canonical data volume.
- That canonical volume is mounted by `kalam-prod-postgres-1`; stopped `docker-postgres-1` and `corplms-postgres` also reference it.
- `infra/scripts/phase0-validate.ps1` runs `docker compose up -d postgres valkey clamav`, and then runs migration checks and a full API pytest suite.
- The preflight does not explicitly create/select a unique disposable PostgreSQL database for the full suite. API configuration defaults from `apps/api/.env`, which currently targets host port 55434; that port was not listening during this audit.

**Impact**

Running the preflight unchanged may try to start another PostgreSQL process over the canonical data directory or run state-changing tests against the wrong database. Either can cause failure, resource contention or unintended data mutation.

**Required closure**
1. Change automated test setup so it never starts PostgreSQL against a volume mounted by the live production-like container.
2. Create/use a dedicated isolated test service and unique disposable DB, with explicit `DATABASE_URL`.
3. Add an environment guard that refuses full test execution when the DB target is live/unspecified.
4. Separate read-only preflight from dependency startup and state-changing tests.
5. Ensure teardown only drops the uniquely named test DB/container created by that run.

**Acceptance:** verify test target identity before any database-backed test; no test uses the canonical live volume; isolation is demonstrated in CI.

**Until fixed, do not run `npm run validate:phase0` or the full DB-backed API suite on this workstation.**

### AUD-006 — Duplicate/stale Compose stacks create operational ambiguity

**Severity:** P1 — reliability / operations
**Status:** Confirmed

**Evidence**
- The `kalam-prod` stack is the working local gateway path.
- The duplicate `docker` project has an unhealthy API and unhealthy ClamAV; its worker/gateway have exited.
- The separate `kalam-tunnel` stack has a separate PostgreSQL volume, healthy API/web/database/Valkey, but gateway and worker are only `Created`.
- Old `phase8rc` and `phase8rc2` containers remain.
- Some stopped PostgreSQL containers share the canonical live data volume.

**Impact**

Default scripts can target the wrong stack. Duplicate services consume resources, health states conflict, and the existence of a second PostgreSQL volume makes data authority and backup/migration ownership ambiguous.

**Required closure**
- Publish a single environment matrix identifying each Compose project, intended use, API/web endpoints, DB volume and whether it is active.
- Change smoke scripts away from stale defaults (currently defaulting to `docker-api-1`, `docker-worker-1`, `docker-migrate-1`) or require explicit project/container arguments.
- Reconcile all stacks and volumes from read-only inspection first.
- Only after backups and volume ownership are documented, authorize separately reviewed cleanup of known-unused runtime objects.

**Safety:** no container or volume was removed during this audit. Do not delete containers or volumes merely because they are old or stopped.

---

## 5. Frontend and API interaction findings

### AUD-007 — Public mega-menu open/close semantics are likely wrong for keyboard and pointer use

**Severity:** P1 — accessibility / conversion usability
**Status:** Static source finding; requires browser confirmation

**Evidence**
- In `apps/web/src/components/public-header.tsx`, `onMouseEnter` and `onFocus` set the active menu.
- The trigger's click handler toggles the same menu off when it is already active.
- The Escape handler sets the menu closed and then calls focus on the trigger; that focus event can immediately set the same menu active again through the parent `onFocus`.

**Impact**

The state transitions conflict: a menu may close on a click intended to activate it, and Escape may fail to leave it closed. Static TypeScript and ESLint checks cannot prove the interaction is accessible.

**Required closure**
- Define one consistent disclosure state machine for pointer, click, keyboard and touch.
- Escape must close the menu and return focus without reopening it.
- Enter/Space must behave predictably and menu links must remain reachable.
- Add Playwright or equivalent tests for pointer open/close, focus, Enter/Space, Tab traversal, Escape, focus return and mobile touch.
- Verify that the control does not cover adjacent navigation or become unreachable at narrow widths.

### AUD-008 — Login is only partially verified

**Severity:** P1 — identity release blocker
**Status:** Open

**Evidence**
- Tenant discovery for `kalam` succeeds through the running gateway.
- Anonymous `/auth/me` correctly returns 401.
- Successful developer login, cookie receipt/persistence, authenticated `/auth/me`, role landing and logout have not been proven against the exact current candidate.
- Host Next.js port 3000 did not respond in a prior probe; the production-style gateway on 3100 responds.

**Required closure**
- Build/deploy current candidate and test actual login through the browser.
- Verify Set-Cookie attributes, session validity after refresh, protected route behavior, logout invalidation and password reset.
- Verify a Platform Developer can reach all authorized platform screens; verify tenant users cannot reach the internal CRM.
- Test inactive accounts, unknown tenant, invalid credentials, lockout/rate limits and network/5xx responses.
- Do not treat tenant discovery or the generic login page HTTP 200 as sign-in success.

### AUD-009 — Current frontend lacks a maintained automated browser E2E gate

**Severity:** P1 — release verification gap
**Status:** Confirmed from current project configuration

**Evidence**
- The web package scripts include development, build, start, lint and typecheck only.
- CI runs API tests plus web dependency audit/typecheck/lint/build; it does not run a maintained current-source browser E2E workflow.
- Historical QA scripts and screenshots exist, but they do not prove all paths in the current worktree.

**Required closure**
- Add a maintained browser E2E runner, preferably Playwright or an equivalent selected by the project.
- Run public conversion, login/session, learner, manager, L&D admin, instructor, compliance admin and executive workflows.
- Record console errors, failed requests, accessible-name checks and screenshots on failure.
- Run tenant/role negative paths and persistence-after-refresh tests.
- Make the core browser suite a CI release gate.

### AUD-010 — Integration registry overstates readiness and exposes partial providers as connected

**Severity:** P1 — product correctness / integration acceptance
**Status:** Confirmed source-level behavior; real provider conformance remains open

**Evidence**
- The Integrations dashboard displays an `Event layer` metric as literal **“Ready”** rather than deriving it from actual webhook health or delivery state.
- `IntegrationUpsert` accepts `status="connected"` and persists that value without requiring a successful connection test. The current UI status selector offers only “configured” or “disabled”, but the API contract still permits a direct caller to set “connected” without evidence.
- The connection checker for HRIS and Calendar falls through to a generic configured health-URL HTTP check. That does not prove data synchronization or calendar integration.
- The email integration checker validates the host/settings supplied in the tenant Integration record, but `app/services/email.py` sends actual transactional email from global `settings.smtp_*`; the tenant integration record is not used by the email sender. The UI can therefore give the impression that saving/testing tenant SMTP settings controls the actual delivery path when it does not.
- The UI explicitly describes SAML interactive sign-in as unavailable until signed assertion handling is implemented.
- The AI provider connection-test handler returns HTTP 501 for provider types outside its implemented Ollama, OpenAI-compatible and Anthropic branches.
- The xAPI checker validates `/about`; SCORM/cmi5 check a manifest/structure document; LTI uses OIDC discovery. These checks alone do not prove full course-runtime tracking, complete LTI launch/Deep Linking or overall provider conformance.

**Impact**

The registry may show “connected” or “Ready” without the corresponding production operation being configured or proven. Operators could assume that real email, HRIS sync, calendar sync or a standards-based course launch is working based only on a lightweight handshake.

**Required closure**
- Replace static readiness labels with measured operational state or neutral “not verified” messaging.
- Only let the server transition a provider to “connected” after a successful supported test; remove `connected` and `error` from user-controlled status upsert, or enforce the state transition server-side.
- Distinguish configured, handshake-passed, synchronization/launch-tested and production-certified states.
- Wire tenant-configured email to the actual mail delivery path, or make the UI explicitly global-operations-only and remove misleading tenant-specific SMTP expectations.
- Hide, disable or clearly label incomplete providers and functions; provide a supported-capability matrix.
- Certify required providers with real endpoints/credentials and success/failure-path tests before describing them as supported.

---

## 6. Database, storage, security and data integrity

### AUD-011 — Production storage target is not proven in the active runtime

**Severity:** P0 — production readiness blocker
**Status:** Confirmed mismatch

**Evidence**
- The live API image reports `storage_backend=local`.
- Its settings module predates the current S3 settings fields.
- Current source's accepted production target is private S3-compatible storage.
- Current S3 tests use a fake client, not a real provider.
- No real provider-backed upload/download/delete, API malware-scan-to-object-store, tenant isolation or off-host recovery proof is available in this audit.

**Required closure**
- Configure a private S3-compatible provider in the intended deployment.
- Verify bucket privacy, encryption, versioning/lifecycle, identity/credential handling and backup policy.
- Test file upload through the API including size/MIME validation and ClamAV scan before object finalization.
- Test authorized download, unauthorized cross-tenant access, deletion, failed multipart/transfer cleanup and missing-object recovery.
- Verify file metadata integrity and restore of data + objects together.

### AUD-012 — Database tenant isolation is enforced at application layer; database-level defense in depth is not established

**Severity:** P1 — security review requirement
**Status:** Source audit finding, not proof of an exploitable leak

**Evidence**
- Tenant filters and permission dependencies exist in reviewed API routes.
- The source audit did not find PostgreSQL row-level security policies in Alembic source.
- Current requirements demand server-side tenant and role boundaries for every protected endpoint/query.

**Required closure**
- Perform a focused tenant-scope review for all resource/detail/list/search/export/file endpoints.
- Add negative cross-tenant IDOR/BOLA tests for each major entity and bulk/export operation.
- Evaluate database RLS as an additional defense-in-depth control; document an approved decision if not implemented.
- Verify manager, instructor, learner, report viewer, auditor and Platform Developer scopes.
- Do not promote until independent security review and current-source negative authorization tests pass.

### AUD-013 — Migration/integrity/restore evidence is incomplete

**Severity:** P0 — production readiness blocker
**Status:** Open

Required closure:
- Verify current DB Alembic revision and source revision from an explicitly chosen authoritative DB.
- Validate migration upgrade from the last approved release, migration idempotency expectations and safe rollback/forward-fix strategy.
- Check schema constraints, foreign keys, uniqueness/idempotency and data equivalence among any approved migration copies.
- Verify off-host scheduled backups for PostgreSQL **and uploaded/object-storage content**.
- Run a separate restore test, integrity checks and record measured RPO/RTO.
- Preserve evidence and identify the owner/target DB for each operation.

### AUD-014 — Full current-source API regression and database integration coverage are outstanding

**Severity:** P1 — test gate
**Status:** Open

**Evidence**
- Current static checks pass and the focused database-free group has 14 passes.
- The knowledge-base tests, sessions database-backed regression, finance integration tests and full API suite have not been run on the exact current source against an isolated database.
- A prior report of 174 passing API tests predates latest changes and cannot be counted as current-candidate evidence.

**Required closure**
- Isolate PostgreSQL/Valkey/ClamAV for tests; use a disposable, uniquely named database.
- Apply current migrations to that test DB, seed clearly marked fixtures and verify cleanup targets.
- Run full API tests with results broken down by module and test.
- Fix failures, retain regression tests and rerun affected plus full suites.
- Avoid local test runners that inherit a production-like `.env` database URL without an explicit guard.

---

## 7. Product scope and workflow audit

### AUD-015 — Requirements traceability is not yet granular enough to certify 100%

**Severity:** P1 — acceptance governance
**Status:** Confirmed documentation gap

The requirements baseline lists **72 must-have** and **14 secondary** checklist items. The current traceability matrix has 63 high-level requirement rows; these are not one-to-one evidence records for all 86 checklist items.

**Required closure**
- Create a complete crosswalk for all 86 in-scope checklist items.
- For each item, record implementation route/service/model, authorization policy, positive and negative tests, persisted-result expectation, UI loading/empty/error behavior, owner-facing acceptance criterion and release evidence.
- Explicitly mark each capability as implemented + tested, partial, deployment-dependent, intentionally deferred or not implemented.
- Do not infer completion from component count, route count or historical phase label.

### AUD-016 — Secondary capabilities need an explicit implemented/partial/deferred decision

**Severity:** P2 unless an item is approved as a must-have
**Status:** Search suggests gaps; not all absence claims are fully confirmed

Items requiring a complete UI/API/model/test search and product decision:
- notification template management;
- general people/learner CSV import (current audit identified email-only invitation CSV and exports, but not a general employee import);
- external learner lifecycle;
- dedicated workshop/calendar workflows beyond generic live sessions;
- complete SSO/standards adapters where those are in approved scope;
- payment collection/automated subscription billing versus the current internal ledger/CRM workflow.

**Required closure**
For every item above, document the evidence and scope decision. A capability must not be advertised as complete just because its name appears in a provider selector or its schema/model exists.

### AUD-017 — Public website and conversion flows need current-build end-to-end proof

**Severity:** P1 — commercial conversion gate
**Status:** Partially verified

The gateway serves key public routes with HTTP 200, but this is route availability, not form success.

Required closure:
- Test contact-sales, guided evaluation, pricing-driven CTAs and lead-to-CRM readback against an isolated environment.
- Verify mandatory work email, organization size/country ordering, phone country-code behavior, validation, consent and attribution.
- Test duplicates, timeout, rate limit, server error and retry.
- Confirm only approved CRM-driven pricing is shown and the prohibited visible incentive section remains absent.
- Check customer-facing claims and brand assets on the exact candidate.
- Verify privacy/terms/cookie notice publication and approval before public global lead collection.

### AUD-018 — Current browser-wide accessibility certification is open

**Severity:** P1 — release gate
**Status:** Open

Historical public and selected dashboard route audits are useful but do not certify the current whole application.

Required closure:
- Current-candidate browser checks at 320/360/390/768/1024/1440 px and 200% zoom.
- Full route-level axe/automated checks plus keyboard interaction, focus management, Escape behavior, screen-reader spot checks, forced-colors and reduced motion.
- Manual review of any automated tool's incomplete rules.
- Test data-dense tables, dialogs, menus, charts, errors, and role-restricted states.
- Record findings, fixes, rerun result and reviewer.

### AUD-019 — Full performance and resilience tests are not present for the current candidate

**Severity:** P1/P2
**Status:** Open

Required closure:
- Define performance SLOs for frontend interaction, API p95 and error rate using a named topology and representative datasets.
- Test concurrent login, course browsing/completion, assessments, bulk assignment/import, report generation, scheduled jobs and file operations.
- Investigate slow `/auth/me` reports using repeatable measurement and query/pool evidence.
- Verify timeout/retry behavior without duplicate business actions.
- Observe worker retry/backlog, mail/webhook failure, object-storage outage and database disconnect recovery.
- Establish monitoring and alert-delivery proof; health endpoints alone do not satisfy operations readiness.

### AUD-020 — Legal/privacy and production operations approval remain open

**Severity:** P0 for commercial production release
**Status:** Open in existing release acceptance register

Required closure:
- Approved privacy notice, terms, cookie/session notice, data-processing terms, retention/deletion/export procedure, subprocessor inventory, AI disclosure and customer-facing commercial claims.
- External TLS/ingress/host/origin checks and monitoring/alert acknowledgement.
- Verified off-host backups, database + object restore, rollback/disaster-recovery rehearsal.
- Independent security review, dependency/secret scan and hosted CI result.
- Customer documentation and UAT sign-off.
- Release decision with named engineering, security, operations, accessibility, product and legal owners.

---

## 8. API/domain and worker review disposition

Source review shows broad implementations for identity/tenancy, learning delivery, assessment/certification, compliance/skills, reporting, integrations, governed AI, support and SaaS CRM. This is evidence of substantial code, not end-to-end acceptance.

The following must be re-verified through current-source tests:
- state transitions and idempotency for enrollment/completion, assessment attempts, credential issuance/revocation, compliance recurrence/escalations and evidence-driven capability recalculation;
- correct tenant + role + manager/instructor scope for lists, details, update, search, reports, exports, file routes and AI retrieval;
- audit records for privileged changes, support actions, AI policy/provider changes, results overrides and commercial transitions;
- notification and worker retries, scheduled reports, webhook signing/replay and failed-delivery behavior;
- route registry/API schema uniqueness and frontend contract compatibility;
- model/migration consistency, database constraints and query performance.

The API source has one explicit HTTP 501 for an unsupported AI provider type. This is an acceptable fail-closed response only if the UI labels/hides unsupported provider types and the product's approved support matrix says those types are unavailable.

A code-level issue to review: finance overview/paged invoice reads include invoice reconciliation logic that can update invoice statuses and commit inside a GET request. Confirm this side effect is intentional and safe under concurrent requests; if retained, test reconciliation consistency and consider moving state-changing reconciliation to an explicit command/worker rather than a read path.

---

### AUD-021 — Tenant-configured webhook delivery lacks outbound URL/SSRF protections

**Severity:** P0/P1 — security release blocker
**Status:** Confirmed source-level risk; no exploit request was made

**Evidence**
- `WebhookCreate.url` is typed as `AnyHttpUrl`, allowing both HTTP and HTTPS.
- `create_webhook` persists the tenant-supplied URL without validating scheme policy, DNS resolution or private/reserved addresses.
- The worker reads active tenant `WebhookEndpoint.url` values and passes them directly to `deliver_webhook`.
- `app/services/webhook_delivery.py` posts to the supplied URL using `httpx.AsyncClient` but does not call the integration URL guard or independently block private/loopback/link-local/reserved destinations.
- The global production guard `INTEGRATION_ALLOW_PRIVATE_URLS=false` applies to `integration_adapters._url_allowed`; it does not protect the separate webhook-delivery service.
- The integration URL guard resolves a hostname before the HTTP client makes its own connection. Without binding the outbound connection to the validated address, DNS rebinding/time-of-check-to-time-of-use remains a possible bypass.
- OIDC discovery validates the discovery URL, but the callback later fetches the metadata-provided `token_endpoint` and `jwks_uri` directly without applying the same URL/egress policy to those server-side requests.
- AI provider configuration accepts arbitrary HTTPS endpoint URLs outside development; the ordinary URL syntax validator does not apply a destination allow-list or private-network policy.

**Impact**

A tenant administrator able to create a webhook may cause a production worker to send outbound HTTP requests into private services reachable from the application network. Plain HTTP endpoints can also receive notification payloads, tenant IDs, user IDs and related fields without transport encryption. This is a potential SSRF and data-exposure path; the audit did not attempt exploitation.

**Required closure**
- Enforce HTTPS for production webhook URLs and reject loopback, private, link-local, reserved, multicast and cloud-metadata destinations for both IPv4 and IPv6.
- Validate URLs at webhook creation/update **and immediately before delivery**.
- Mitigate DNS rebinding by resolving and validating the exact connection destination or by routing outbound webhooks through a controlled egress proxy/firewall that enforces destination policy. A preflight DNS check alone is insufficient.
- Keep redirects disabled (already set in the delivery client), and ensure redirect responses cannot cause a second outbound request.
- Restrict supported destination ports, apply connection/response timeouts and size limits, and ensure failures do not leak response bodies or internal network details to tenants.
- Add isolated unit/integration tests for localhost/private IPv4, IPv6 loopback/link-local, metadata IPs, domains resolving to private IPs, DNS rebinding, HTTP rejection in production, public HTTPS success and retry behavior.
- Run an independent SSRF/egress-security review before production release.

**Acceptance:** every outbound webhook is HTTPS in production and can connect only to approved public destinations under a policy enforced at connection time; negative SSRF tests pass.

---

### AUD-022 — Tenant-controlled AI provider secret references can expose process-level secrets

**Severity:** P0 — critical security release blocker
**Status:** Confirmed from current source; no outbound credential request was attempted

**Evidence**
- `apps/api/app/services/ai_governance.py` validates `secret_ref` only as an environment-variable-style identifier. It does not restrict the value to an approved secret set or a tenant-scoped secret store.
- `apps/api/app/api/routes/ai.py::_provider_secret` resolves a supplied reference directly with `os.getenv(secret_ref)` / `os.environ[secret_ref]`.
- A principal with `ai.manage` can configure a provider endpoint URL and a `secret_ref`; provider connection tests send the resolved secret as an `Authorization: Bearer` header for OpenAI-compatible providers or an `x-api-key` header for Anthropic providers.
- This permission path is reachable in repository test/demo setups: `apps/api/tests/test_ai_security.py` explicitly asserts that the `admin@demo.corp` tenant-admin profile has `ai.manage`, and `seed_legacy_demo.py` / `seed_ci_fixtures.py` assign it to the demo Tenant Administrator. The normal predefined-role template in `saas_commercial.py` is narrower, so the deployed role assignment must still be audited; this does not eliminate risk in the seeded demo/test roles.
- Production validation requires HTTPS for AI endpoints, but HTTPS alone does not ensure the remote endpoint is trusted. The current validator does not bind a reference to a tenant/provider credential or reject sensitive process variables such as database connection settings.

**Impact**

If an untrusted tenant administrator or compromised account can manage AI providers, they may be able to name a known environment-variable identifier and point a provider test at an endpoint they control. The server can then transmit the corresponding process-level value in an outbound authentication header. Depending on the referenced variable, this could expose database credentials, mail credentials, internal provider keys or other shared secrets across tenant boundaries. The code path permits this; this audit did not attempt to extract or transmit any real secret.

**Required closure**
- Stop resolving arbitrary tenant-supplied strings directly against the full process environment.
- Replace raw environment-name references with narrowly scoped logical secret identifiers backed by a secrets manager or an allow-listed resolver bound to tenant + provider ID.
- Explicitly prevent references to database URLs/passwords, encryption keys, session/signing secrets, webhook secrets, SMTP credentials and secrets belonging to other providers/tenants.
- Restrict provider test and inference egress to approved provider destinations; apply destination validation at connection time and guard against DNS rebinding.
- Avoid returning secret material in responses, logs, exception text or diagnostic fields.
- Add regression tests with harmless canary environment variables: arbitrary/sensitive names must be rejected, no unapproved value may leave the process, and a permitted test secret is sent only to its approved endpoint.
- Add an independent security test covering `ai.manage` authorization, provider configuration, connection testing and tenant isolation.

**Acceptance:** a tenant-scoped AI administrator cannot cause the server to disclose any process-wide or other-tenant secret. Only a secret explicitly provisioned for that tenant/provider and approved destination can be used.

---

### AUD-023 — Email notification worker can starve eligible messages behind preference-suppressed records

**Severity:** P1 — workflow reliability
**Status:** Confirmed from current source

**Evidence**
- `process_notification_emails` selects the oldest 100 active-user notifications where `email_sent_at IS NULL`, ordered by creation time.
- When email is disabled globally for the user or for the notification category, the worker executes `continue` without recording that the item was intentionally suppressed.
- Those records remain eligible for the same query on subsequent runs until their 24-hour query window expires.
- The query also filters out notifications older than 24 hours. If the worker is down long enough, an unsent eligible message can age out of the query permanently instead of being retried after recovery.

**Impact**

If older unsent records are preference-suppressed, they can repeatedly occupy the 100-row batch, delaying eligible messages and causing email notifications to miss their intended window. The current design also cannot distinguish “not yet attempted”, “temporarily failed”, “permanently failed” and “suppressed by preference”.

**Required closure**
- Model delivery state separately from user preference and delivery attempts (e.g. pending, sent, suppressed, retrying, failed).
- Mark suppressed messages explicitly and exclude them from future delivery batches without falsely marking them as delivered.
- Use bounded, ordered queue claiming and safe concurrency/lease semantics so multiple workers cannot send the same message unintentionally.
- Add tests where the first 100 records are suppressed, followed by eligible records, and prove the eligible records are delivered on the next batch.
- Add tests for transient SMTP failure, repeated retries, security-notification policy and permanent failure handling.

**Acceptance:** opted-out notifications do not block eligible messages; every notification has a traceable delivery/suppression outcome.

### AUD-024 — Webhook delivery batching can repeatedly select already-delivered records; concurrent workers can hit unique conflicts

**Severity:** P1/P2 — background-job reliability and scale
**Status:** Confirmed source-level queue design risk

**Evidence**
- `process_notification_webhooks` selects notification/endpoint pairs from the last 24 hours and applies `LIMIT 100` before consulting delivery state. It has no deterministic `ORDER BY` and does not restrict the initial query to due, undelivered delivery records.
- Notifications older than 24 hours are excluded before their delivery state is checked; an outage lasting beyond that window can make not-yet-delivered webhooks ineligible for retry after recovery.
- Already-delivered deliveries remain in the source query and are skipped only inside the loop. Depending on query plan/order, the same rows can occupy a batch repeatedly, starving newer due deliveries.
- The database has a unique constraint on `(webhook_id, notification_id)`, but concurrent workers can both perform the “no delivery exists” read before either insert. A unique-constraint error on the later `flush` is not handled locally and can abort a worker run.

**Required closure**
- Query due delivery records directly, order deterministically by `next_attempt_at` and creation time, and exclude delivered/failed-final records in SQL.
- Claim work transactionally using `FOR UPDATE SKIP LOCKED` or an equivalent lease/claim model.
- Use a race-safe insert/upsert for new delivery rows and handle duplicate claims without aborting the worker batch.
- Keep retry backoff and attempt caps, but make backlog depth, oldest event age, success/failure rates and last error observable.
- Add tests proving a backlog above 100 drains, due retries are processed when expected, and two worker instances do not crash or send concurrent duplicate events.

**Acceptance:** a backlog drains fairly under repeated runs, retries obey their schedule, and concurrent workers claim deliveries safely.

### AUD-025 — Password-reset request commits its token before synchronous email delivery, without a reliable retry path

**Severity:** P1 — account recovery and information-disclosure risk
**Status:** Confirmed source-level behavior; SMTP-failure runtime not induced

**Evidence**
- `_request_password_reset` invalidates older tokens, creates and commits a new token hash, and only then calls `send_email` synchronously.
- `send_email` raises `RuntimeError` when SMTP is unavailable or delivery fails; the reset route does not catch it or place the message on a durable retry queue.
- The endpoint returns `accepted` for a nonexistent/inactive account, while a real eligible account can get a server error if email delivery is unavailable. A valid reset token may already have been committed even though no email was delivered.

**Impact**

Recovery can fail precisely when email is temporarily unavailable, with no safe resend state, and response differences can help distinguish real accounts under misconfiguration/failure conditions.

**Required closure**
- Write reset requests to a durable outbox/job table in the same transaction as token creation.
- Return a consistent public response regardless of whether the account exists and whether delivery currently succeeds.
- Have the worker deliver the message with bounded retries, idempotency, expiry awareness and a safe operational failure status.
- Add rate limiting for reset requests, monitoring of delivery failures and tests for SMTP outage, retry, expired token and non-existent accounts.
- Keep reset tokens single-use, hashed at rest and invalidating other active sessions after a successful password reset.

**Acceptance:** reset request response does not reveal account existence; transient SMTP failure does not silently strand a committed token without a delivery/retry record.

### AUD-026 — OIDC callback accepts an omitted `email_verified` claim

**Severity:** P1 — identity assurance
**Status:** Confirmed source-level condition

**Evidence**
- The OIDC callback rejects an email only when `claims.get("email_verified") is False`.
- If `email_verified` is missing or has an unexpected value, this condition does not reject the identity, despite the error message stating that SSO requires a verified email address.
- The ID-token registry shown in source validates issuer, audience, expiry and nonce, but it does not explicitly require `sub` in the shown registry.

**Required closure**
- Require `email_verified is True` when email is the account-matching identifier, or implement an explicitly approved alternative provisioning policy.
- Require and validate the OIDC subject claim, and document whether identity links are bound to (issuer, sub) rather than mutable email alone.
- Add tests for missing, false and true `email_verified`, absent `sub`, issuer/audience/nonce mismatches, expired tokens and unprovisioned tenant users.

**Acceptance:** only an appropriately validated, tenant-provisioned identity can obtain a session; missing assurance claims are not silently treated as verified.

### AUD-027 — Authentication and password-reset endpoints lack an evident gateway IP/request-rate limit

**Severity:** P1/P2 — security hardening
**Status:** Confirmed in the inspected application/gateway source; external edge protection not verified

**Evidence**
- API login increments `failed_login_count` and temporarily locks individual accounts after repeated failures.
- The inspected Nginx configuration has no `limit_req` or `limit_conn` rules for authentication/password-reset routes.
- The password-reset route does not call the Redis-based limiter used by public marketing inquiry intake.

**Impact**

Per-account lockout does not alone limit credential-stuffing attempts distributed across many accounts, and password-reset endpoints remain exposed to repeated requests when reachable without a verified upstream rate-control layer.

**Required closure**
- Add appropriately scoped per-IP/per-route controls at the gateway or a trusted edge, plus account/email-key controls and progressive delays where needed.
- Ensure rate limits work behind trusted proxies without trusting arbitrary client-supplied forwarding headers.
- Return consistent authentication/recovery messages and monitor rate-limit outcomes.
- Test legitimate shared-NAT users, burst attacks, distributed attempts, lockout recovery and password-reset retry semantics.

**Acceptance:** defined, tested rate limits exist at a trusted layer and cannot be bypassed by untrusted forwarding headers; legitimate users receive safe, actionable feedback.

---

### AUD-028 — Current migration lineage deletes the webhook delivery table required by the active worker

**Severity:** P0 — confirmed database-schema/runtime defect
**Status:** Confirmed in migration source and active database

**Evidence**
- Migration `f1c2d3e4a5b6_add_webhook_delivery_state.py` creates `webhook_deliveries` with status, attempts, next-attempt, delivered-at, last-error and uniqueness fields.
- Later upgrade migration `8f8f960bb643_phase5_development_feedback_milestones.py` explicitly drops the `webhook_deliveries` index and then calls `op.drop_table('webhook_deliveries')`. No subsequent current-lineage upgrade migration recreates this table.
- Current worker code in `apps/worker/run.py::process_notification_webhooks` issues raw SQL `SELECT`, `INSERT` and `UPDATE` statements against `webhook_deliveries`.
- A read-only query against the active `corplms` database returned `MISSING` for `public.webhook_deliveries`, while `alembic_version` returned `r7s8t9u0v1w2`.

**Impact**

When a tenant has an active webhook and a qualifying notification, worker delivery-state handling will fail because the table does not exist. The gateway and general database readiness can still report healthy: neither check exercises this workflow. Delivery retries/idempotency are unavailable and the worker may log a job exception at runtime.

**Required closure**
1. Add a **new forward migration** that restores the table with the exact columns, constraints, indexes and foreign keys required by current worker code. Do not rely only on editing historical migrations: existing deployments that already recorded those revisions will not rerun them.
2. Test upgrade from the active source revision to current head on a disposable PostgreSQL database. Assert the table exists and its schema matches the worker contract.
3. Add migration regression checks that compare required runtime tables to the Alembic upgrade path, including detection of a later migration dropping a table still used by application code.
4. Add worker integration tests for first delivery, repeated delivery, retry, final failure and concurrent claims using the restored schema.
5. Deploy the API and worker from the same reviewed candidate only after backup and migration approval.

**Acceptance:** a disposable database upgraded from the prior approved revision contains `webhook_deliveries`; current-worker delivery tests pass; the production-like database is changed only by an approved migration after backup.

---

### AUD-029 — Legacy demo seeder can provision a broad-privilege administrator with a known default password and print it

**Severity:** P1 — environment/data safety and credential hygiene
**Status:** Confirmed source-level risk; script was not executed

**Evidence**
- Current untracked file `apps/api/scripts/seed_legacy_demo.py` sets `DEMO_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "DemoOnly!1234")`; it falls back to a known password if no environment variable is supplied.
- The script gives the `Tenant Administrator` role every permission in its `PERMISSIONS` list, including `ai.manage`, and creates demo tenant/users through the configured `SessionLocal` database.
- It has no evident hard stop on `APP_ENV=production`, no required explicit demo-seed switch, and no check that its resolved database is a test/demo target.
- It prints the demo password to stdout at completion.
- The separately hardened `scripts/seed.py` does not automatically protect this additional seed entrypoint.

**Impact**

If someone accidentally runs this script with a production database configuration, it can create/augment demo users and high-privilege roles using a known credential and expose that credential to terminal/process logs. This audit does **not** establish that the script has been run against production.

**Required closure**
- Make this script fail closed in `APP_ENV=production` and production-like environments.
- Require an explicit command-line opt-in such as `--allow-demo-seed` for non-production use and validate the target database against an explicitly configured, isolated demo/test target.
- Do not default to a known password; require a one-time secret through a secure environment/secret manager, and never print it.
- Keep CI fixtures separate from general demo seeding and enforce distinct credentials/roles for CI, demo and production.
- Replace the “all permissions for Tenant Administrator” seed behavior with the approved least-privilege role matrix; use a separate explicit platform-only role for internal developer capabilities.
- Add tests proving that production mode, missing explicit opt-in and unintended database target are rejected before any session write occurs.

**Acceptance:** the seeder cannot mutate a production database by accident, emits no credential material, and uses only reviewed least-privilege demo roles.

---

## 9. Correct execution order

1. **Preserve and classify the worktree.** Create a reviewed source snapshot/candidate; do not discard pre-existing changes.
2. **Fix test isolation before running full tests.** Ensure no test process can use or start PostgreSQL on the canonical live volume.
3. **Fix the CI image runtime smoke settings.** Re-run CI on exact source.
4. **Create a candidate image set** (API/web/worker) and record digests.
5. **Use an isolated DB to apply current migrations and run full current-source API tests.** Include knowledge-base and sessions tests.
6. **Run current-source web typecheck/lint/build**, followed by route and browser E2E tests using the candidate. Do not count an old running image as candidate evidence.
7. **Close authentication, role and tenant workflows.** Successful sign-in, authenticated `/auth/me`, logout and six baseline user journeys are mandatory.
8. **Validate storage and integration scope.** Use actual private S3-compatible storage and real configured provider endpoints for any feature included in the release.
9. **Complete accessibility, performance, security and UX review.**
10. **Complete operational/legal gates** and make a signed release decision only with recorded evidence.

---

## 10. Definition of done for the refreshed audit

Kalam is not 100% complete until:
- exact source-to-build-to-deployment provenance is demonstrated;
- current migration head matches the approved candidate and data-integrity/backup gates pass;
- all 72 must-have items and all secondary items included in the approved release have explicit dispositions and traceable passing evidence;
- full API tests run against a disposable isolated DB and pass;
- frontend static/build/browser gates pass on the same candidate;
- public conversion forms and core role-based journeys pass end to end;
- tenant, role, file and AI authorization tests pass;
- production storage, integrations and operational recovery are verified for the release scope;
- there are no unresolved Critical/High release-blocking defects;
- accessibility/security/performance/UAT/legal/operations gates are reviewed and signed;
- any accepted partial capability is clearly documented and not misrepresented as complete.

**Final audit disposition: NOT RELEASE READY.** Static quality checks and local runtime readiness are positive. The source/runtime mismatch, migration drift, missing runtime knowledge-base routes, CI/storage guard mismatch and unsafe test-isolation path must be addressed before full regression or production acceptance. All other open items remain open until their specific evidence is captured.
