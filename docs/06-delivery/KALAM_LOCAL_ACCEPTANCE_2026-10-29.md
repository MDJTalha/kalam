# Kalam Local Acceptance Evidence — 2026-10-29

## Scope and safety

Verification was performed against the local working tree at `C:\Projects\Kalam`. Existing staged, unstaged, and untracked work was preserved. API tests used the dedicated local PostgreSQL test container `kalam-release-test-pg` on loopback port `5434`; fixture credentials and database password were not emitted. The developer database on port `55434` was not used for tests.

## Passed checks

| Gate | Result | Evidence |
|---|---|---|
| Focused foundation/auth API tests | PASS | `62 passed, 1 warning in 78.69s` |
| Complete API test suite | PASS | `191 passed, 1 warning in 179.84s` after security dependency upgrades and explicit pytest fixture-loop configuration; `FULL_API_SUITE_EXIT=0` |
| Python bytecode compilation | PASS | `compileall -q app tests scripts`, exit 0 |
| API/test Ruff | PASS | `ruff check app tests`: all checks passed |
| API mypy | PASS | `Success: no issues found in 65 source files` |
| API virtualenv dependencies | PASS | `pip check`: no broken requirements found after security updates |
| Production dependency audit | PASS | `pip-audit -r requirements-prod.txt`: no known vulnerabilities |
| Development dependency audit | PASS | `pip-audit -r requirements.txt`: no known vulnerabilities |
| Installed API environment audit | PASS | `pip-audit --local`: no known vulnerabilities; unused Authlib removed and audit cache dependency upgraded |
| Test tooling security | PASS | pytest upgraded to 9.2.0; pip upgraded to 26.2.2; setuptools to 84.2.1; certifi to 2026.10.23; dnspython to 2.9.0; filelock to 4.2.4 |
| Web TypeScript | PASS | `npm run typecheck`, exit 0 |
| Web ESLint | PASS | `npm run lint`, exit 0 |
| Web production build | PASS | Next.js 16.4.3 production build exit 0; 88 static pages generated |
| Docker Compose development config | PASS | `docker compose -f docker-compose.yml config --quiet` |
| Docker Compose production config | PASS | `docker compose -f infra/docker/docker-compose.app.yml config --quiet` |
| Alembic migration-head check | PASS | `check_migration_head.py`: migration head `82cb7d9e1f4a` (mergepoint), head check passed |
| Full Phase 8 local preflight | PASS | Compose validation, migration check, isolated SaaS ops fixtures, complete API suite (`191 passed`), API Ruff/mypy, web typecheck/lint, and isolated Next.js production build all passed |
| Phase 8 image runtime smoke | PASS | API liveness 200; docs disabled 404; readiness correctly 503 without dependencies; web `/`, `/login`, `/dashboard` returned 200; worker job entry points present in image |
| Current authenticated API role smoke | PASS (2026-10-29) | Fresh local API checks: admin, manager, and learner login each returned 200; route-level permissions matched expected 200/403 outcomes; web `/`, `/login`, `/dashboard` returned HTML 200; evidence saved to `qa/api-role-smoke-20261029.json` |
| Existing browser accessibility evidence | PASS (dated 2026-10-28) | Saved artifact records 12 axe runs, zero violations, and no failures; a fresh browser/axe run was not possible in this pass because the Chrome remote-debugging endpoint was unavailable |
| Git diff whitespace check | PASS | `git diff --check`, exit 0 |

## Warnings and non-gating findings

- API tests emit one Starlette deprecation warning about the current `httpx` integration in `fastapi.testclient`. It did not fail tests. Dependency changes should be made only after confirming compatibility with the locked FastAPI/Starlette stack.
- The first full-preflight attempt exposed a real environment-isolation defect: the placeholder outbound proxy used for production Compose validation leaked into integration tests. `infra/scripts/phase8-preflight.ps1` now restores caller-provided deployment variables before tests. The full preflight was rerun successfully afterward (`191 passed`, web build passed).
- `ruff check scripts` reports 137 findings in existing operational/QA scripts. This is outside the release preflight's enforced `app tests` lint gate and includes formatting/style findings in browser probes and seed utilities. It remains a cleanup backlog; it has not been represented as passing.
- `git diff --check` reported Git LF-to-CRLF conversion warnings on working-tree files, but no whitespace errors.

## Release blockers still open

1. **Hosted staging deployment is not verified.** The latest GitHub Actions staging run (`40717880856`) is failed, and its `deploy` job has no recorded steps. Attempting to retrieve job logs returned 404, so there is no actionable step-level log to diagnose from that run. [Workflow run](https://github.com/MDJTalha/kalam/actions/runs/40717880856).
2. **AWS account-level access restrictions block deployment diagnosis.** Read-only EC2, SSM, and ECS inventory calls in multiple regions returned explicit-deny errors from an AWS Organizations service control policy. The one region where the EC2/SSM/ECS inventory calls succeeded reported zero SSM-managed instances and zero ECS clusters. This tool context cannot override an organization-level SCP. The target region/account and policy need to be confirmed by an authorized AWS organization administrator.
3. **Integrated gateway/deployment smoke remains unrun.** The local Docker image smoke validates the images in isolation; no deployed gateway/API/web/worker/migration stack was running locally for the integrated gateway smoke. Therefore `integrated_deployment_certified` remains `false`.
4. **Release-candidate hygiene is still open.** The working tree contains many pre-existing staged, unstaged, and untracked changes. No reset, clean, commit, push, or deployment was performed. A release candidate must be reviewed and committed deliberately before hosted deployment certification.

## Current disposition

Local API and frontend verification is green. Phase 8 is **not complete for production release** until the hosted deployment access/billing/policy blocker is resolved, a reviewed release candidate is committed, and the integrated deployment smoke plus post-deployment health checks pass.

## Follow-up remediation evidence — 2026-10-29

### CI fixture-password handoff

- Finding `CI-ENV-001` — **High / release-blocking until hosted verification**: the fixture seeding step re-exported a value written to `GITHUB_ENV` using `${{ env.CI_FIXTURE_PASSWORD }}`. The `env` expression is evaluated from workflow/job/step configuration context and is not a reliable way to read a value created dynamically by a prior step through `GITHUB_ENV`. This could pass an empty password to the fixture seeder and cause demo-account authentication failures.
- Corrective change: removed the invalid explicit `CI_FIXTURE_PASSWORD` env mapping from the fixture seeding step. The runner automatically exports `GITHUB_ENV` values to subsequent steps; the test step exports the same inherited value as `KALAM_QA_DEMO_PASSWORD`.
- Regression validation: `.tools/validate-ci-workflow.py` parses the workflow YAML and asserts the generator writes to `GITHUB_ENV`, the seed step does not re-export through `env`, the tests use the inherited generated password, and the test database guard is configured.
- Local end-to-end validation with a newly generated random fixture password: **PASS**, fixture seeder accepted the generated value and the full API suite returned `191 passed, 1 warning in 181.82s`, exit code 0. This verifies the local fixture seed/authentication path; hosted validation remains blocked because recorded GitHub Actions runs have no step records/logs.

### Latest local release gates

- Full Phase 8 preflight rerun: **PASS**, exit code 0.
- Isolated API suite within that preflight: **191 passed, 1 warning**.
- Web TypeScript typecheck: **PASS**.
- Web ESLint: **PASS**.
- Next.js production build: **PASS**, 88 static pages generated.
- Production image runtime smoke on the locally available images: **PASS**, exit code 0. API liveness returned 200; docs endpoint returned 404; readiness without dependencies returned 503; web `/`, `/login`, `/dashboard` returned 200; worker entry points were present. The images were built approximately 22 hours before this check, so this is evidence for those image digests, not proof that they contain the current working tree.
- `git diff --check` and `git diff --cached --check`: both exit 0; Git printed line-ending conversion warnings only.
- The single Starlette deprecation warning remains non-failing. Current manifests pin FastAPI 0.141.1 and httpx 0.28.x; no dependency upgrade was made without compatibility evidence.

### External release blockers (still open)

- The GitHub `staging` environment has no configured secret names and no configured variable names. The workflow requires `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY`, `STAGING_APP_DIR`, and `STAGING_WEB_ORIGIN` at minimum. No values were exposed or fabricated.
- Latest observed CI and staging runs are failed with no recorded job steps; log retrieval is unavailable. This is consistent with a runner/account-level restriction, but its exact cause is **not confirmed** from available evidence.
- No reviewed immutable release candidate has been committed or pushed, and no staging deployment or integrated post-deployment acceptance has been performed.
- Production approval remains withheld pending hosted CI, staging configuration/access, deployment, security, recovery, and operational acceptance evidence.

### Database and operational-script follow-up

- Fresh empty-database migration: **PASS** on a newly created database (`kalam_migration_test_20261029`) inside the dedicated loopback PostgreSQL test container, isolated from the developer database and production. `alembic upgrade head` exited 0; current revision is `82cb7d9e1f4a` and the migration-head check passed.
- ORM/migration drift: **PASS**. `alembic check` reported `No new upgrade operations detected.` against the migrated empty database.
- Operational-script import hygiene: **17 safe Ruff import findings** (`E401`/`F401`) were fixed in API scripts using only those explicitly selected rules. The enforced application/test lint gate was rerun and passed (`All checks passed!`).
- Remaining non-gating lint backlog in `apps/api/scripts`: 85 `E702`, 21 `E701`, 12 `E402`, and 2 `F841` findings were observed before the import fixes. These were not mass-rewritten because semicolon-separated control flow and late imports need file-by-file review; they remain open rather than being falsely reported as resolved.
- Backup/restore drill (isolated test data only): **PASS**. Created a non-empty PostgreSQL custom-format dump from `kalam_test` (`.tools/kalam_restore_verify_20261029.dump`, 1,391,478 bytes), restored it into a new database `kalam_restore_verify_20261029`, and compared the Alembic revision plus tenant/user/course counts. Source and restore matched exactly: revision `82cb7d9e1f4a`, counts `3,5,383`. No production or developer database was used. The disposable restore database and backup artifact are retained for inspection; they were not deleted during this pass.

### Security hardening follow-up — 2026-10-29

- Finding `SEC-XML-001` — **High / input-parsing security**: Ruff's Bandit-compatible scan identified `xml.etree.ElementTree.fromstring` parsing remote integration metadata as untrusted XML. Switched to `defusedxml.ElementTree`, added `defusedxml>=0.7.1,<1` to runtime dependency manifests, and added an XML entity-expansion regression test. The parser now converts both malformed and unsafe XML failures into a controlled `IntegrationCheckError`.
- Finding `SEC-ASSERT-001` — **Medium / correctness under optimized Python**: removed runtime `assert` statements used for API/business validation in subscription seat updates, offer discount calculation, contract updates, and renewal reconciliation. These checks must not disappear under `python -O`. Null trial-seat input now returns a deliberate HTTP 422, and a regression test covers it.
- Added `types-defusedxml>=0.7.0,<1` as a development/mypy dependency because the third-party library has no bundled typing stubs. `mypy app` now passes with `Success: no issues found in 65 source files`; `pip check` reports no broken requirements.
- Focused XML/integration/commercial regression suite: **23 passed, 1 warning**. Full API suite after these changes: **193 passed, 1 warning in 246.11s**, exit code 0.
- Production application Ruff security rules (`ruff check app --select S --ignore S105,S106`) passed after the fixes. A broad scan of tests also reports many expected `assert` uses in pytest and test-only dummy secret labels; those are not runtime production assertions and were not mass-modified.
- Updated production dependency audit after adding `defusedxml`: `pip-audit -r requirements-prod.txt` reported **no known vulnerabilities**.
- Full dependency audit after adding the XML hardening and typing dependencies: **PASS**. `python -m pip_audit -r requirements.txt` reported no known vulnerabilities; production dependency audit also reported no known vulnerabilities.
- Final stable-tree preflight after XML hardening and commercial validation fixes: **PASS** with `-SkipTests`, exit code 0. It revalidated development/production Compose, Alembic head, Ruff, mypy, web typecheck, web lint, and an isolated production build generating 88 static pages. The full API suite was run separately after these changes and passed 193/193.
- A first full preflight attempt encountered a dashboard TSX parse error during its production build. A subsequent isolated current-tree production build passed, and the stable-tree preflight build also passed. The initial failure is recorded as transient/unresolved in cause; no source was overwritten to force the result.
- Frontend production dependency audit after final local build: **PASS**. `npm audit --audit-level=high --omit=dev` reported `found 0 vulnerabilities`, exit code 0.
