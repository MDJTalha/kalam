# CorpLMS Phase 0 Re-baseline Audit

Date: 2026-09-25
Repository: C:\Projects\CorpLMS
Purpose: Re-open Phase 0 as the authoritative foundation gate before further phase work.

## Findings

P0-01 Environment matrix drift — CRITICAL
The Phase 0 environment matrix documented PostgreSQL host port 55433 while docker-compose.yml exposes 55434. Root and API environment templates were inconsistent with the canonical local runtime. Corrected.

P0-02 Web origin drift — HIGH
The earlier re-baseline incorrectly treated 3001 as the canonical local web port. Live verification shows the actual Next.js development server and package default are on 3000. Root/API templates and the environment matrix have now been corrected to 3000; CI remains isolated on service-native ports.

P0-03 API template typos — HIGH
The API template contained REDI_URL and SESSION_TTL_SECOND3 instead of REDIS_URL and SESSION_TTL_SECONDS. Corrected.

P0-04 Repository hygiene — HIGH
Git status contains a very large tracked deletion set under .npm-cache-clean plus generated local artifacts/profiles/logs. These can obscure meaningful source changes. Generated paths were added to .gitignore. Existing tracked deletions were NOT automatically restored or discarded.

P0-05 Evidence drift — MEDIUM
Historical Phase 0 evidence records 42 generated routes, while the current application has materially evolved. Historical evidence remains historical; current status must use current verification.

P0-06 Validation scope — MEDIUM
The root npm workspace currently declares apps/web only; the Python API is managed independently under apps/api. This is workable, but there is no single root command validating the complete stack.

P0-07 Database migration drift — CRITICAL, RESOLVED
The live database was previously at branchpoint `f1c2d3e4a5b6` while Alembic reported `j5a6b7c8d9e0` as head. `alembic upgrade head` completed successfully and the live database now reports `j5a6b7c8d9e0 (head)`.

P0-08 API test isolation — HIGH, RESOLVED
The foundation API suite could stall/fail when reusing one session-scoped TestClient across tests. The fixture was changed to function scope. The full API suite now completes with 65/65 passing.

## Acceptance criteria

1. Canonical ports and origins documented.
2. Environment templates aligned.
3. Generated local artifacts excluded from future Git changes.
4. Existing source changes preserved; no destructive reset performed.
5. Architecture/environment documentation reflect actual topology.
6. Foundation validation is repeatable.
7. Final Phase 0 closure requires a fresh current-state evidence run.

## Fresh validation — 2026-09-25

- Docker foundation: PASS — PostgreSQL healthy on host 55434, Valkey on 56379, ClamAV on 55000.
- Alembic: PASS — database is at `j5a6b7c8d9e0 (head)` after successful `upgrade head`.
- API tests: PASS — 65 tests passed in 96.87s across the API test suite.
- API Ruff: PASS — exit 0.
- API mypy: PASS — no issues in 46 source files.
- Web TypeScript: PASS — `tsc --noEmit` exit 0.
- Web ESLint: PASS — exit 0.
- Web production build: PASS — Next.js generated all 48 application routes.
- Runtime API health: PASS — `/api/v1/health` returned `status=ok`; readiness returned `status=ready`.
- Runtime web: PASS — the existing Next.js development server is on port 3000 and `/login` and `/` returned HTTP 200.
- Frontend-to-backend authentication: PASS — web proxy login returned HTTP 200 and a `corp_lms_session` cookie; the proxied `/api/lms/auth/me` returned HTTP 200 for the authenticated learner; `/dashboard` returned HTTP 200 with the authenticated cookie.
- Test isolation repair: PASS — the API `TestClient` fixture was changed from session scope to function scope; the full API suite then completed deterministically at 65/65.

## Current state

PHASE 0 TECHNICAL GATE: PASS.

Repository hygiene remains an explicit change-control item before a formal Git-clean Phase 0 closure: current status contains 1,144 tracked deletions (primarily `.npm-cache-clean`) and 135 untracked paths. These changes were not reset or discarded. The environment baseline was also corrected to the actual Next.js local default port 3000 after live verification.

## 2026-09-28 reconciliation

The 2026-09-25 working-tree counts above are historical and are no longer current. The large tracked deletion set under `.npm-cache-clean` is no longer present in the current status scan. Generated browser profile `.phase8rc-browser/` has also been added to `.gitignore`.

Phase 0 now has a single repeatable local validator: `npm run validate:phase0`. The current-tree run passed required artifact checks, environment contract, Docker dependency readiness, Alembic head, Ruff, mypy, 112 API tests, web TypeScript, ESLint and a 75-route production build.

Current formal local evidence is authoritative in `PHASE_0_EXIT_EVIDENCE.md`. Hosted CI remains external because this checkout has no configured Git remote.
