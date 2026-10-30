# Kalam Remediation Register — 2026-10-29

> **Governance note (2026-10-30):** This file is the detailed technical finding history. The single current delivery-status authority is `KALAM_MASTER_DELIVERY_REGISTER_2026-10-30.md`; update the master register when a finding's disposition changes. Do not treat this historical register as a competing release decision.

## Baseline

- Repository: `MDJTalha/kalam`
- Local path: `C:\Projects\Kalam`
- Branch: `work/kalam-local-changes-2026-10-26`
- Audited working-tree base commit: `a1073cb34bc88e4e2b8cb6a41b622c908e104518`
- Remote `origin/main` was at the same SHA during this check. No commit, push, merge, or deployment was performed.
- The working tree contains substantial pre-existing staged, unstaged, and untracked changes. They have been preserved.

## Finding register

| ID | Severity | Finding / impact | Evidence and disposition | Status |
|---|---|---|---|---|
| CI-ENV-001 | High | CI fixture seeder could receive an empty password because a `GITHUB_ENV` value was re-exported via `${{ env.CI_FIXTURE_PASSWORD }}`. This can cause fixture authentication failures. | Removed the incorrect step-level env mapping. Workflow validator now checks the generated `GITHUB_ENV` handoff and test password reuse. Full isolated API suite passed with a freshly generated random password: 191 passed, 1 warning. Hosted CI has not yet executed the corrected workflow. | Fixed locally; hosted verification open |
| DB-MIG-001 | High | Fresh-install migration correctness must be demonstrated on an empty database. | New database created only inside dedicated loopback test container. `alembic upgrade head` exit 0; current revision `82cb7d9e1f4a`; `alembic check` reported no new upgrade operations. | Verified pass |
| DB-DR-001 | High | Backup restore must be tested, not inferred from backup creation. | Custom-format dump of isolated `kalam_test` restored into a new isolated database. Alembic revision and tenant/user/course counts matched exactly (`82cb7d9e1f4a`, `3,5,383`). Test artifact retained under `.tools/`. This is not a production-data recovery drill. | Local test-data restore verified; production recovery open |
| QA-API-001 | High | API regressions and fixture auth need reliable local verification. | Full suite passed twice in the current run: once in Phase 8 preflight and once with a newly generated random fixture password. Each run: 191 passed, 1 warning. | Verified pass |
| QA-WEB-001 | High | Frontend type safety, lint and production build are release gates. | `npm run typecheck`, `npm run lint`, and production build passed; 88 static pages generated. | Verified pass |
| QA-IMG-001 | High | Current-tree production images must be built and smoke-tested; stale images do not prove current-tree image correctness. | Image runtime smoke passed against locally available image digests created approximately 22 hours earlier. Current-tree production image rebuild was not completed in this pass. | Open |
| CI-HOST-001 | Critical | Hosted Actions execution is unavailable for the candidate. | Recorded CI/staging runs failed with no recorded job steps and logs unavailable. The cause is consistent with a runner/account-level restriction but is not confirmed. No account policy or billing changes were attempted. | Externally blocked / cause unconfirmed |
| DEPLOY-001 | Critical | Staging deployment cannot be configured or verified without real target details and credentials. | GitHub `staging` environment currently exposes no configured secret names and no variable names. Required minimum: `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY`, `STAGING_APP_DIR`, `STAGING_WEB_ORIGIN`. Values must be set securely by an authorized owner; none were requested in chat or fabricated. | Externally blocked |
| QA-A11Y-001 | Medium | Fresh browser and accessibility validation against the exact current working tree is required. | Existing saved accessibility evidence is dated 2026-10-28. A fresh browser/axe run was not completed because the Chrome remote-debugging endpoint was unavailable in the prior attempt. | Open / not freshly verified |
| LINT-OPS-001 | Medium | Operational API scripts have a style backlog outside the enforced `app tests` Ruff gate. | Safe `E401`/`F401` import fixes applied (17 findings). Prior scan showed 85 `E702`, 21 `E701`, 12 `E402`, and 2 `F841` findings. Remaining findings need file-by-file review; no mass rewrite was performed. | Partially remediated; open |
| SEC-SCAN-001 | High | Comprehensive secret scanning and static application security analysis must cover current files and Git history. | Known private-key/AWS/GitHub token marker scan of changed files produced no matches. `gitleaks`, `trufflehog`, `semgrep`, and `bandit` were not installed. Git history was not comprehensively scanned in this pass. | Incomplete / open |
| OPS-PERF-001 | Medium | Performance targets and historical readiness p95 must be re-measured under controlled conditions. | No current controlled p50/p95/p99 or concurrency benchmark was executed in this pass. | Not assessed |
| OPS-MON-001 | High | Production alerts, dashboards, notification delivery and recovery objectives require operational evidence. | Documentation and scripts exist, but alert delivery/acknowledgement/escalation were not exercised in this pass. | Not assessed |
| RELEASE-001 | Critical | Candidate hygiene and release traceability require a reviewed immutable commit and hosted/staging evidence. | Working tree remains substantially modified with staged, unstaged, and untracked files. No commit/push/deploy was made. | Open; release approval withheld |

## Verification commands captured in this pass

- `.\tools\validate-ci-workflow.py` — passed: YAML parse, fixture password handoff, test password reuse, isolated DB guard.
- `.\tools\run-phase8-full-preflight.ps1` — exit 0; API suite 191 passed, web typecheck/lint/build passed.
- Full API suite with newly generated ephemeral fixture password — exit 0; 191 passed, 1 warning.
- `python -m alembic upgrade head` on a new isolated database — exit 0.
- `python -m alembic check` — no new upgrade operations detected.
- `infra/scripts/phase8-image-runtime-smoke.ps1` — exit 0 against pre-existing image digests; not current-tree image certification.
- Backup/restore comparison — source and restored migration revision plus selected row counts matched.
- `ruff check app tests` — passed after safe import-only fixes in operational scripts.
- `git diff --check` and `git diff --cached --check` — exit 0; line-ending conversion warnings remain.

## Release decision

**NOT APPROVED FOR PRODUCTION.** Local API/frontend and isolated database gates are green, but hosted CI, staging configuration/deployment, current-tree image smoke, fresh browser accessibility, comprehensive security analysis, and production operational/recovery acceptance are not complete. Do not mark Phase 8 complete until hosted and staging gates are verified for a reviewed immutable candidate.
| SEC-XML-001 | High | Remote integration XML metadata was parsed with stdlib ElementTree, which is unsafe for untrusted entity declarations. | Replaced with `defusedxml.ElementTree`; direct runtime dependency declared; DTD/entity-expansion regression added. Focused tests passed; full suite 193 passed; production Ruff security rules passed. | Fixed and locally verified |
| SEC-ASSERT-001 | Medium | Runtime `assert` statements guarded API/business invariants and can be removed by optimized Python execution. | Replaced runtime assertions with explicit HTTP 422/404 handling or safe null guards. Regression added for null trial seats; full API suite passed. | Fixed and locally verified |
| SEC-DEP-001 | High | Newly declared XML security and typing dependencies must remain vulnerability-free and compatible. | `pip check` passed; production and full requirements `pip-audit` both reported no known vulnerabilities; mypy passed after adding the type-stub package to development requirements. | Verified pass |
| QA-WEB-002 | High | A preflight production build initially reported a dashboard TSX parse error despite typecheck/lint passing. | Re-ran current-tree isolated production build successfully, then ran stable-tree preflight with `-SkipTests`; Compose, migration, Ruff, mypy, typecheck, lint, and build all passed. Root cause of the initial intermittent parse result was not conclusively established. | Current-tree build verified pass; intermittent failure cause open |
| SEC-WEB-001 | High | Production frontend dependencies must be audited against current lockfile. | `npm audit --audit-level=high --omit=dev` reported 0 vulnerabilities, exit code 0. | Verified pass |

## Follow-up implementation — 2026-10-30

The subsequent role/workspace remediation added two platform operations capabilities to the local working tree:

- `GET /api/v1/support/developer/health` requires `platform.health.read`, verifies the database and Redis, returns only component status (not exception details), and reports `ready` or `degraded`.
- `GET /api/v1/support/developer/audit` requires `platform.audit.read`, is restricted to the persisted Kalam operations tenant, and returns a bounded latest-event list without raw metadata.
- The Platform Operations page now displays these health and audit views.
- Role-governance tests now assert Platform Developer access and SaaS Owner denial for these endpoints.

Fresh verification after these edits:
- API Python compilation for `support.py` and `test_role_governance.py`: PASS.
- Targeted Ruff for those files: PASS.
- Web TypeScript: PASS.
- Full web ESLint: PASS.
- Web production build: PASS; 89 static pages generated.

Not verified in this follow-up:
- Database-backed execution of the new role-governance tests and health/audit routes.
- Platform incident lifecycle. The `platform.incidents.manage` permission still has no dedicated incident data model/API/UI and must not be described as implemented.
- The latest hosted staging run (`40717880856`) has a failed deployment job with no steps; no deployment evidence exists.
- All previously recorded Critical/High external release gates remain open unless separately evidenced.

## Follow-up implementation — platform incident lifecycle (2026-10-30)

Implemented in the local working tree:
- Added `PlatformIncident` persistence model and additive Alembic migration `a1b2c3d4e5f6_platform_incidents.py` (parent `9a7b8c9d0e1f`). The current source migration graph reports one head: `a1b2c3d4e5f6`.
- Added Platform Developer-only incident list, create and update APIs. Supported severity values are SEV1–SEV4; lifecycle states are open, investigating, mitigated and resolved. Resolving records `resolved_at`; reopening clears it.
- Incident owner assignment is validated against an active user in the internal Kalam operations tenant. Incident changes write corresponding internal platform audit events.
- Added incident create/list/status controls to the Platform Operations workspace and expanded role-governance regression assertions for Developer access and SaaS Owner denial.
- Updated the pre-existing Developer Support Session migration to avoid SQLAlchemy inspection calls in offline Alembic mode.

Fresh verification:
- Python compilation for the incident model, support routes, new migration, adjusted support-session migration and role-governance tests: PASS.
- Targeted Ruff for those files: PASS (`All checks passed!`).
- Alembic source graph: one head, `a1b2c3d4e5f6`.
- Web TypeScript: PASS.
- Full web ESLint: PASS.
- Web production build: PASS; all 89 static pages generated.

Important limitations:
- The incident migration has not been applied to any database, and incident API tests have not been executed against a database.
- Offline SQL generation is currently blocked by an existing data migration (`l1m2n3o4p5q6_role_governance.py`) that queries tenant rows during upgrade. This is a live-data migration and must be validated on an isolated PostgreSQL database rather than bypassed or skipped.
- No production database migration, commit, push or deployment was performed.

Additional route-registration verification: importing the FastAPI application and generating OpenAPI succeeded; all three platform incident operations (GET list, POST create, PATCH update) are present in the generated schema. The corresponding route-registry test was added, but the test suite itself has not been executed in this follow-up.


## Follow-up verification — 2026-10-30

### Platform incident workspace hardening

- Replaced incident workspace layout class names that had no matching global CSS selectors with dedicated, explicitly defined responsive styles. The incident table now scrolls horizontally within its own bounded container; form controls have visible keyboard focus treatment; status feedback uses a dedicated accessible status style.
- Increased the random incident-number suffix from 6 to 10 hexadecimal characters to reduce collision probability.
- The incident workspace remains permission-gated by `platform.incidents.manage` and the home Kalam operations context; create/update operations write platform audit events.

### Verified in this follow-up

- Web TypeScript typecheck: PASS (`npm --prefix apps/web run typecheck`).
- Web ESLint: PASS (`npm --prefix apps/web run lint`).
- Web production build: PASS (`npm --prefix apps/web run build`; 89 pages generated; `/dashboard/platform` included).
- Backend targeted Python compile: PASS.
- Backend targeted Ruff: PASS.
- Alembic graph: one head, `a1b2c3d4e5f6`.
- FastAPI application import and generated OpenAPI registration for GET/POST `/api/v1/support/developer/incidents` and PATCH `/api/v1/support/developer/incidents/{incident_id}`: PASS.
- `git diff --check` and `git diff --cached --check`: PASS (Git emitted line-ending normalization warnings only).
- Incident-specific CSS selector presence: PASS.

### Still not certified

- No database migration was applied; the platform incident table is not yet verified against a live migrated database.
- No database-backed role-governance, incident lifecycle, or tenant-isolation test suite was run in this follow-up.
- No real Platform Developer/SaaS Owner operator account login and negative-permission matrix was verified.
- No end-to-end browser workflow, staging deployment, production image/runtime, backup/restore, or release certification was completed here.
- The working tree contains extensive pre-existing staged, unstaged, and untracked work. No changes were committed, pushed, or deployed.

**Disposition:** source-level incident workspace implementation and static/build verification are complete; overall Kalam release readiness remains open pending the evidence gates above.


## Database verification campaign — 2026-10-30

### Isolated PostgreSQL environments

- `kalam-release-test-pg` (`kalam_test`, loopback port 5434) was confirmed as a dedicated test container. It was already at `9a7b8c9d0e1f`; the migration upgrade completed successfully to `b2c3d4e5f6a7`, and `platform_incidents` was present.
- `kalam-role-test-pg` (`kalam_test`, loopback port 5435) was confirmed empty before the clean-schema run. The complete Alembic chain upgraded from base to `b2c3d4e5f6a7` successfully. The resulting public schema contained 102 tables, including `platform_incidents`.
- The `b2c3d4e5f6a7_manager_capability_catalog_read` migration was exercised through a downgrade/upgrade round trip on the isolated test database. A predefined Manager role retained the expected `capabilities.read` grant after re-upgrade.
- The local application database (`corplms-postgres`, database `corplms`) remains at `82cb7d9e1f4a`. It was inspected read-only and was not migrated as part of this verification campaign.

### Database-backed API verification

- Targeted role-governance, incident lifecycle, tenant-isolation, seed-guard and database-engine tests: **10 passed**.
- Manager direct-report authorization suite after fixture correction: **4 passed**.
- Full API suite on the existing isolated release-test database: **222 passed, 0 failed**.
- Full API suite on a clean database after a fresh migration from base: **222 passed, 0 failed**.
- Both full-suite runs emitted one third-party Starlette/httpx deprecation warning; no test failures resulted.

### Clean-database fixture defect found and corrected

- The first full-suite run on a newly migrated database exposed a CI fixture defect: `seed_ci_fixtures.py` created reserved built-in test roles using the ORM default `role_kind='custom'`.
- The first role-governance test consequently treated the Tenant Administrator fixture as a mutable custom role and changed its permissions, causing cascading authorization failures in subsequent tests.
- The fixture now creates and normalizes its reserved CI roles as `predefined` in test/CI environments and continues to replace their permission grants with the authoritative fixture matrix.
- The previously failing role-governance tests passed after reseeding; the subsequent clean-database full suite passed all 222 tests.
- This correction is limited to test fixture roles; it does not grant broader customer permissions or weaken production authorization checks.

### Runtime and web smoke verification

- Built standalone Next.js runtime started successfully on isolated loopback port 3007 and used an isolated API test server on port 8003.
- HTTP 200: `/`, `/login`, `/dashboard/platform`, `/pricing`, `/trust`, `/guided-evaluation`, `/contact-sales`.
- API health endpoint returned HTTP 200; unauthenticated `/api/v1/auth/me` returned HTTP 401 as expected.
- The existing development server on port 3000 did not respond during the initial probe; the built standalone runtime was separately verified on 3007. Authenticated real-browser role journeys and axe scans remain open.

### Current verification disposition

- API test suite: PASS on both populated and clean migrated isolated PostgreSQL databases (222/222).
- Complete migration chain from base: PASS on isolated PostgreSQL.
- Manager capability-catalogue read-only permission migration: PASS via round trip.
- Backend targeted compile/Ruff: PASS; Alembic graph has one head, `b2c3d4e5f6a7`.
- Frontend TypeScript, ESLint and production build: PASS in this campaign's preceding verification step; standalone public/dashboard route smoke: PASS.
- Still open: migrate and verify the local application database after an explicit operator go-ahead; authenticated browser/role journeys and accessibility scans; verify every production integration and secret; staging deployment; production runtime, backup/restore and final release certification.
- No commit, push, or deployment was performed.


## Verification continuation — 2026-10-30

### Verified on isolated PostgreSQL databases

- A clean, empty PostgreSQL database (`kalam-role-test-pg`, database/user `kalam_test`, local port 5435) accepted the complete Alembic migration chain through head `b2c3d4e5f6a7`.
- The clean migration created `platform_incidents`; the database revision and the expected Manager permission grant were checked directly with read-only SQL.
- Deterministic CI fixtures were seeded into the isolated database. The Manager fixture is now explicitly marked `role_kind='predefined'`, matching the production role-governance model. This corrects a fixture fidelity gap: the migration intentionally grants the new catalogue-read permission to predefined/legacy Manager roles, not arbitrary custom roles.
- The entire API suite then passed against that cleanly migrated and seeded database: **222 passed, 0 failed**, in 205.68 seconds. One Starlette/httpx deprecation warning remains.
- A downgrade of the latest migration followed by re-upgrade completed successfully on the isolated database. The database remains at head after the round-trip.
- `alembic heads` reports one head: `b2c3d4e5f6a7`.
- `git diff --check` and `git diff --cached --check` completed without whitespace errors (Git emitted only line-ending conversion warnings).

### Additional changes made during verification

- Added migration `b2c3d4e5f6a7_manager_capability_catalog_read.py`, which grants `capabilities.read` only to predefined/legacy Manager roles and removes that grant on downgrade. Capability catalogue reading remains separate from capability administration and assessment permissions.
- Updated `seed_ci_fixtures.py` so built-in CI role identities are marked predefined. Existing fixture roles are explicitly normalized to that role kind on reseed.
- The permission regression was found in a capability-domain test and is covered by the full clean-database API suite.

### Still not certified

- The existing local application database remains at revision `82cb7d9e1f4a`; no migration was applied to it. The new migrations have only been applied to isolated disposable test databases.
- An authenticated browser/accessibility attempt against the isolated QA runtime returned HTTP 401 for the three demo accounts; therefore no authenticated browser route or axe-core results were produced. Do not treat this as a UI/accessibility pass. The fixture credential/runtime mismatch remains to be diagnosed using a safe, controlled QA login setup.
- The frontend typecheck, lint, and production build are being rerun after the current verification changes; record their final outcome separately when complete.
- Real Platform Developer and SaaS Owner operational accounts have not been provisioned or verified.
- No production image/runtime, staging deployment, backup/restore drill, external release gate, or AWS production deployment is certified by these local test results.
- No commit, push, or deployment was performed.


### Formal Phase 8 preflight — 2026-10-30 (final rerun)

- The first formal preflight exposed 12 test failures because the isolated test database had been mutated by a previous test run and the preflight prepared the SaaS operations tenant without restoring the deterministic demo/tenant-isolation role fixtures. This was fixture-state contamination, not a reason to relax authorization checks.
- Updated `infra/scripts/phase8-preflight.ps1` to run `scripts/seed_ci_fixtures.py` after `scripts/bootstrap_saas_ops.py` and before pytest. The CI seed now resets fixture role grants, role kind, user-role assignments, and demo fixture account state to the declared matrix.
- The corrected formal preflight passed end-to-end:
  - Development Docker Compose configuration: PASS
  - Production Docker Compose configuration: PASS
  - Alembic current-at-all-heads check: PASS (`b2c3d4e5f6a7`)
  - API Ruff (`app`, `tests`): PASS
  - API mypy: PASS (65 source files)
  - SaaS operations fixture bootstrap: PASS (roles ready; no operator account created)
  - Deterministic CI tenant/role fixture seed: PASS
  - Full API suite: **222 passed, 0 failed**, 1 Starlette/httpx deprecation warning
  - Frontend TypeScript typecheck: PASS
  - Frontend ESLint: PASS
  - Isolated Next.js production build: PASS; 89 static pages generated
  - Overall: `Phase 8 preflight passed.`
- Mypy also identified two SQLAlchemy `Result.rowcount` typing errors in tenant suspension paths. The affected reads now use a guarded `getattr(result, "rowcount", 0)` conversion; API mypy subsequently passed.
- Freshly built standalone web runtime returned HTTP 200 for `/`, `/login`, `/pricing`, `/trust`, `/dashboard`, `/dashboard/platform`, and `/dashboard/saas/tenants`; a CSS chunk and a JavaScript chunk both returned HTTP 200 when the standalone server was started from its correct runtime directory with static assets copied into the standalone tree. Isolated API health endpoint returned HTTP 200.
- `git diff --check` and `git diff --cached --check` passed. Git emitted line-ending conversion warnings only.

### Remaining release blockers / boundaries

- The authenticated browser/axe run is still not certified. An earlier attempt against a temporary API QA runtime returned HTTP 401 for the demo logins and produced no authenticated route or accessibility evidence. A later attempt to start a fresh authenticated QA API process was blocked by the execution safety layer; no workaround was used. The role fixtures were subsequently reseeded and their exact grants verified read-only, but that does not substitute for a browser login run.
- The local application database is still at revision `82cb7d9e1f4a`. All new migrations were verified on isolated disposable PostgreSQL databases only; the application database was not upgraded.
- SaaS operations roles exist in the isolated test tenant, but the bootstrap explicitly did not create a Platform Developer or SaaS Owner operator account. No production operator account was provisioned or login-verified.
- Production container image execution, live staging, external CI deployment, backup/restore, disaster-recovery, and AWS production release certification remain outstanding.
- The branch remains `work/kalam-local-changes-2026-10-26`, HEAD `a1073cb`. The working tree contains numerous pre-existing staged, unstaged, and untracked project changes. No commit, push, deployment, or application-database migration was performed.


### Authorization template consistency review — 2026-10-30

- Reviewed the people directory, direct-report endpoint, capability-gap scope, capability-risk scope, team reporting, development-intervention access, global search, tenant role templates, and organization endpoints.
- Confirmed that `/people` and `/people/page` require `users.read`; Managers are limited to `/people/team` and direct-report detail access. Capability-gap and capability-risk read calculations filter non-manager users to self plus active direct reports. Team reports aggregate only direct reports.
- Found a role-template drift: `PREDEFINED_TENANT_ROLES` in `saas_commercial.py` still granted tenant-wide `users.read`, `reports.read`, and capability access to HR Business Partner and Regional Executive, despite the role-boundaries migration explicitly constraining both templates until organization-unit row-level authorization exists.
- Corrected the live tenant-provisioning templates to match the migration's constrained definitions. HR Business Partner now receives only `courses.read`, `learning.access`, and `development.manage`; Regional Executive receives only `tenant.read`, `courses.read`, and `learning.access`.
- Added a regression assertion to `tests/test_role_governance.py` to prevent those unscoped permissions from returning.
- Verification after the change: targeted Ruff PASS; Python compileall PASS; API mypy PASS (65 source files); direct import/runtime assertion of both role templates PASS.
- The focused pytest invocation was blocked by the repository's required `KALAM_TEST_DATABASE_URL` guard because the isolated database URL was not available in this new process. The formal Phase 8 preflight was attempted and safely stopped at that same guard after both Docker Compose validations passed; no fallback database was used. The previously recorded 222-test Phase 8 pass predates this latest role-template change, so a database-backed regression/full-suite rerun is still required.
- No local application database migration, commit, push, or deployment was performed.
