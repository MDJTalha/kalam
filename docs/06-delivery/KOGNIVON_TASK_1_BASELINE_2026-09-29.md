# Kognivon Task 1 — Current Baseline and System-State Verification

Date: 2026-09-29  
Status: **LOCAL BASELINE COMPLETE — RELEASE CERTIFICATION OPEN**  
Branch: `release/phase8-rc1-20260927`  
HEAD: `6fea20a92337f18b0b74eedab9493675981da08e`

## Scope

This record establishes the current checkout and local runtime as the source of truth before further product redesign. It covers repository state, project controls, environment contract, services, migrations, API/web verification, route surface and demo authentication. No application-code redesign was performed.

The repository was already substantially modified before this task. The working tree contains 245 modified or untracked entries and has no configured Git remote. Those changes were preserved.

## Current architecture

- Web: Next.js 16.3.6, React 19.2.8, TypeScript.
- API: FastAPI 0.141.1 on Python 3.11, SQLAlchemy/Alembic.
- Data/services: PostgreSQL 18.6, Valkey 8, ClamAV 1.4.3.
- Local development ports: web `3000`, API `8000`, PostgreSQL `55434`, Valkey `56379`, ClamAV `55000`.
- Production-style local gateway: `http://127.0.0.1:3100`.
- Gateway API contract: `/api/lms/*` is rewritten to FastAPI `/api/v1/*`; direct `/api/v1/*` requests at the gateway are handled by Next.js and return its 404 page.
- Current source includes public commercial routes, role-aware dashboard routes, SaaS CRM routes, authentication flows, learning, assessments, certificates, compliance, skills, development, reporting, integrations, support and governed AI surfaces.

## Current-tree verification

The built-in command `npm run validate:phase0` completed successfully with elevated Docker access.

| Area | Result |
|---|---|
| Required Phase 0 artifacts and repository skeleton | PASS |
| 13 ADR records | PASS |
| Canonical environment contract | PASS |
| Compose configuration parsing | PASS |
| PostgreSQL, Valkey and ClamAV readiness | PASS |
| Alembic migration head | `h9i0j1k2l3m4` — PASS |
| Ruff | PASS |
| mypy | PASS — 56 API source files |
| API regression | **121 passed, 1 deprecation warning** |
| Web TypeScript | PASS |
| Web ESLint | PASS |
| Next.js production build | PASS — **82 routes generated** |
| Repository state | WARNING — dirty tree, no Git remote |

The only test warning is the existing Starlette/httpx TestClient deprecation warning. No test failures were reported by the current-tree validator.

## Runtime verification

The active `phase8rc` local stack is healthy: gateway, web, API, PostgreSQL, Valkey, worker and ClamAV are running; the migration container exited successfully. Gateway `/proxy-health`, API liveness and API readiness all returned HTTP 200. API readiness reported both database and Redis ready.

The seeded `demo-corporation` tenant-admin account completed a login → authenticated `/auth/me` → logout smoke flow successfully. The response exposed the expected Tenant Admin role and permissions. The account is demo data only.

## Source/runtime boundary

The active `phase8rc` API, web and worker containers use older image digests than the current working tree. Therefore the running stack is not a certification of the current source.

The current source build contains `/pricing`, `/contact-sales`, `/free-trial` and `/trust`. The older running web image returned 404 for those routes while returning 200 for `/`, `/login` and `/dashboard`. The current source must be built, deployed and smoke-tested as an exact image set before any release or feature-completeness claim.

There are also stopped/created containers from an older `docker` Compose project, including a previously failed migration container. They were not changed during this baseline task and should be handled in a controlled environment-hygiene task.

## Open baseline risks and release gates

1. The checkout is not an immutable candidate: it is dirty and has no remote, so hosted CI evidence cannot be attached to this exact source.
2. The active runtime is an older image set and does not contain all routes present in the current source.
3. Production deployment, TLS, monitoring/alert transport, external SMTP/integration certification, backup/restore and rollback remain open as documented in the Phase 8 evidence.
4. Demo credentials and local HTTP cookie settings are development/runtime concerns that must remain isolated from production; production must use approved secret management, TLS and secure cookies.
5. The non-blocking Starlette/httpx deprecation warning should be resolved in the testing dependency baseline.

## Task disposition

Task 1 is complete for the local engineering baseline. The next task should be the architecture/navigation audit, using this record and the current source tree—not the older running image—as its starting point.
