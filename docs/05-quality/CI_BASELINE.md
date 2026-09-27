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