# Corporate LMS — CI Baseline and Evidence

Version: 0.1
Status: Phase 0 baseline

## CI contract
GitHub Actions workflow: `.github/workflows/ci.yml`.

API job: PostgreSQL 18 service -> Python 3.11 -> dependency install -> Alembic migrations -> demo seed -> Ruff -> mypy -> pytest.

Web job: Node 24 -> `npm ci --include=dev` -> TypeScript check -> ESLint -> production build.

## Local CI-equivalent evidence — 2026-09-24
- Alembic migrations: PASS.
- Demo seed: PASS.
- Ruff: PASS.
- mypy: PASS, 38 source files checked.
- pytest: PASS, 15 tests passed.
- `npm ci --include=dev`: PASS, 1,273 packages audited, 0 vulnerabilities reported by npm.
- Web TypeScript check: PASS.
- Web ESLint: PASS.
- Web production build: verified separately when the live server is stopped.

## CI interpretation
The workflow is the reproducible baseline. Local evidence validates command compatibility on the development machine; GitHub-hosted execution remains the authoritative remote CI signal.

Non-blocking note: npm may report pending install-script approval for `unrs-resolver`; this did not fail installation.
## 2026-09-28 verification update
The original 2026-09-24 results are historical. The API workflow now includes a healthy ClamAV service, an explicit PING transport check, and scanner environment settings for the full tests. A local YAML parse and contract check passed, and the two previously blocked scanner-dependent tests passed against a real ClamAV process. Full current-tree tests and static gates are recorded in `docs/06-delivery/PHASE_0_EXIT_EVIDENCE.md`.
No Git remote is configured for the current checkout, so no hosted CI run can be attributed to this candidate. Phase 0 formal CI evidence remains OPEN until a run URL, exact commit and job conclusions are recorded.

The fresh-database check also exposed a missing SaaS operator bootstrap and a stale AI test retrieval mock. The workflow now bootstraps operator roles before tests; the test covers the correct authorized and capability retrieval paths. The five affected tests passed on an isolated database. The final full isolated run had 111 passes and one local host-relay scanner failure. Hosted CI remains required for formal closure.

## Current local CI-equivalent evidence — 2026-09-28

The root command `npm run validate:phase0` is the current local foundation gate. It verifies required Phase 0 artifacts, environment contract, Docker dependency readiness, migration head, API quality gates and web quality/build gates in one repeatable run.

Latest result:
- PostgreSQL/Valkey/ClamAV readiness: PASS.
- Alembic head: `b3c4d5e6f7g8`.
- Ruff: PASS.
- mypy: PASS — 54 source files.
- pytest: **112 passed, 1 dependency deprecation warning**.
- Web TypeScript: PASS.
- Web ESLint: PASS.
- Web production build: PASS — **75 routes**.

Hosted CI remains authoritative when a remote repository exists. This checkout currently has no Git remote, so no hosted workflow result can be attached to the exact candidate.
