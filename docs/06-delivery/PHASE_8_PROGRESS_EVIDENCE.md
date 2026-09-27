# Corporate LMS — Phase 8 Commercial / Release Readiness Progress

Date: 2026-09-26
Project: C:\Projects\CorpLMS
Status: IN PROGRESS

## Phase 8 objectives
Phase 8 closes the gap between local engineering completion and production/commercial release readiness. The gate covers deployment topology, ingress security, observability, backup/recovery, CI/CD, accessibility/browser certification, external dependency certification, runbooks, rollback and release evidence.

## Achievements verified in this cycle
- Production readiness audit completed against the current implementation-status, deployment, CI/CD and infrastructure assets.
- API readiness now checks both PostgreSQL and Redis/Valkey; liveness is exposed separately.
- Foundation regression after readiness hardening: 51 passed, 1 known non-failing warning.
- Production Compose topology hardened so Next.js remains internal and Nginx gateway is the published ingress service.
- Production Compose validation: PASS.
- Nginx configuration syntax validation: PASS.
- Gateway policy adds baseline security headers and /proxy-health.
- Repeatable PostgreSQL backup and isolated restore-verification scripts added.
- Real canonical database backup: PASS.
- Real isolated restore verification with alembic_version validation: PASS.
- API mypy defect in manager/team plan aggregation fixed.
- API mypy: PASS, 51 source files.
- Phase 8 release-preflight script added.
- Monitoring, reverse-proxy and infrastructure-script placeholder documentation replaced with operational guidance.

## External prerequisites carried into Phase 8
- Real SMTP provider authentication and external mailbox delivery.
- Real third-party integration handshakes where customer/provider credentials are required.
- Real external webhook receiver evidence.
- Real production AI provider credentials/billing/SLA evidence where enabled.
- Production TLS/certificate/managed-ingress evidence.
- Production monitoring/alert transport evidence.
- Production deployment/rollback evidence in the target environment.

## Remaining release gates
- Certify the newly built API/web image pair as an integrated deployment in a production-like target, including migrations, gateway, authenticated journeys, upload scanning and rollback.
- Verify both PostgreSQL and uploaded-file restores from off-host backups in the target environment.
- Validate public TLS, monitoring/alert delivery, SMTP and enabled external integrations with real target credentials.
- Repeat performance, accessibility and browser checks against the release candidate in that environment; retain the results and release approver.

## 2026-09-26 — Local release-gate continuation
- Preflight: development and production Compose config PASS; Alembic current `q2r3s4t5u6v7` (head); Ruff PASS; mypy PASS across 51 API source files after repairing certificate-template history typing.
- Full API regression: **103 passed, 1 dependency deprecation warning**. Web TypeScript and ESLint: PASS.
- Isolated Next.js production build: PASS, **49/49 routes**, using `NEXT_DIST_DIR=.next-phase8-build` to avoid the live development server output directory. Next.js auto-added this temporary directory to `tsconfig.json`; the two auto-added include entries were removed afterward.
- Browser certification script now exits nonzero on failed route checks and waits up to eight seconds for a route to leave its loading state. The first run reported 52/78 failures (51 premature loading samples, one mobile Administration overflow). A targeted CSS fix constrained compact role rows. Final authenticated desktop/mobile sweep: **78 checks, 0 failures**. Raw run: `qa/phase8-browser-cert-rerun.log`.
- Local performance smoke: first run failed the readiness p95 gate at **2289.76 ms** against 1000 ms during other activity, with zero HTTP failures. An idle rerun passed all three profiles: health p95 **189.19 ms**, readiness p95 **834.02 ms**, authenticated `/auth/me` p95 **1191.4 ms**. This is local development evidence, not production capacity or SLA certification; repeat in a production-like environment.
- Production deployment guide now matches the one-shot migration service in the Compose topology and release runbook.

Current decision: local code, browser, and isolated build checks PASS. Production deployment, TLS, monitoring alerts, external provider checks, restore/rollback in the target environment, and independent security/accessibility certification remain OPEN. No production release claim is made.

### Production image build continuation
- Initial `docker compose -f infra/docker/docker-compose.app.yml build api web` failed in the web builder because `next/font/google` could not fetch Geist from Google (`ENETUNREACH`) inside Docker. Raw evidence: `qa/phase8-image-build.log`.
- Bundled the same Latin Geist and Geist Mono variable WOFF2 assets already emitted by the successful local Next.js build under `apps/web/src/app/fonts/`, and changed the root layout to `next/font/local`. The production build no longer needs a Google Fonts request. Non-Latin type coverage remains a separate localization gate.
- Rerun: **API and web production images both built successfully**, including web typecheck, lint, and 49-route production build. Raw evidence: `qa/phase8-image-build-rerun.log`. Targeted Administration browser check after the font change: **2/2 desktop/mobile passed**.
- Image build does not prove the target environment starts, migrates, serves TLS, restores data, or rolls back; these remain release gates.

### Preflight and generated-output hygiene
- Preflight now uses `alembic current --check-heads`, so migration drift fails the gate instead of merely printing the current revision. The revised check passed at `q2r3s4t5u6v7`.
- The isolated Next.js build output was initially picked up by ESLint during a later rerun, producing generated-code errors. `apps/web/eslint.config.mjs` now ignores `.next-*/**`; a fresh `npm run lint:web` passed with the generated build directory still present. These errors were from generated output, not application source.

## 2026-09-26 — Recovery and running-stack verification continuation
- Existing production-style Compose stack on `127.0.0.1:3100` was inspected read-only. Gateway health and homepage returned HTTP 200; API readiness reported database and Redis ready; migration container had exit code 0; baseline security headers were present. Evidence: `qa/phase8-gateway-smoke-20260926.json`.
- **Important image boundary:** running API/web image IDs differ from the newly built release-candidate images. The running stack is therefore evidence for the older deployment only. `phase8-gateway-smoke.ps1` now accepts expected image IDs and correctly refuses a stale image; the new images have not been deployed or smoke-certified.
- An isolated second Compose stack was not started because the host had approximately 646 MB free physical memory at inspection, while the current stack includes PostgreSQL, Valkey, ClamAV, API, worker, web and gateway. This avoids disrupting the live development services.
- Fresh canonical development backup: `backups/corplms-20260926-195713.dump` created successfully. Revised restore verification created a uniquely named database, matched Alembic revision `q2r3s4t5u6v7` and row counts for `tenants`, `users`, and `courses`, then removed its database. The leftover verification-database count was zero.
- Safety check: attempting to use the existing `postgres` database as the restore target was rejected before any drop/create operation, and `pg_isready` remained healthy.
- This recovery drill used the local development database and is not a target-environment recovery or rollback certificate. A production backup must also cover uploaded files/object storage and be restored under an approved data-recovery procedure.

## 2026-09-26 — Uploaded-file recovery continuation
- Added `infra/scripts/backup-uploads.ps1` for read-only Docker-volume archiving with a SHA-256, size and file-count manifest, plus `verify-uploads-backup.ps1` for safe-path validation, checksum verification and isolated extraction.
- Isolated fixture-volume drill: created a 21-byte course file, archived it, and verified **1 extracted file** with SHA-256 `e7d09a7635a12ebddb16d9967c98f3b281b4c6d142f0808105c99ea625b8f1d0`; the fixture volume was removed after the test. The fixture archive and manifest remain in `backups/uploads/phase8-fixture/` as evidence.
- The currently mounted stack volume `docker_corplms_uploads` was archived read-only and verified, with **0 files** (1,536-byte tar). This confirms the procedure runs against that volume but does not prove recovery of real customer uploads. Its evidence is in `backups/uploads/local-stack/`.
- Release/operations/rollback runbooks now require upload or object-storage backups and separate restore verification alongside PostgreSQL. These local archives must be copied to storage outside the host's failure domain before they count as production recovery protection.
- Negative check: a copied manifest with a deliberately wrong SHA-256 was rejected (`Archive SHA-256 mismatch`); the temporary tampered manifest was removed.

## 2026-09-26 — Isolated release-image runtime checks
- Built candidate image IDs: API `sha256:ce983374c8fe1ef0665abef6fe7f91dd1839af4fbdcbff7854b3e6e0762ef49e`; web `sha256:2b3862e9a342f14aac4ad0f05aebabbbf47ef149b5ed70357f19d36fdef569b4`.
- Launched the candidate web temporarily at `127.0.0.1:3101` on the existing Compose network. `/`, `/login` and `/dashboard` each returned 200; login markup included a title and Next static asset references.
- Launched the candidate API with a read-only filesystem, no network and synthetic database/Redis addresses. Production settings disabled API docs. `/api/v1/health/live` returned 200, `/docs` returned 404 and dependency readiness returned the expected 503. This checks startup and readiness failure behavior, not dependency connectivity.
- Evidence: `qa/phase8-candidate-image-isolated-20260926.json`. Temporary containers were removed after the checks. The older gateway stack was not changed.
- Integrated candidate deployment, migrations, authenticated smoke, real restore/rollback and production services remain open. Host free memory was approximately 683 MB before these checks, so another complete stack was not started.

## 2026-09-26 — Monitoring probe continuation
- Added `infra/scripts/phase8-monitor-probe.ps1` to inspect gateway health/homepage and internal API readiness, retaining consecutive failure counts and first-failure time across scheduled runs.
- Healthy local stack: `healthy`, exit 0. Controlled missing-container checks: first API failure `observing`/exit 0; second `warning`/exit 1; simulated elapsed six minutes `critical`/exit 2. Unreachable gateway immediately `critical`/exit 2; restored endpoints reset both counters and returned `healthy`/exit 0.
- Raw validation: `qa/phase8-monitor-probe-validation.json`. `infra/monitoring/README.md` explains once-per-minute scheduling and exit-code routing. No external alert transport, on-call delivery, worker/queue monitoring or target-environment uptime evidence exists yet; those remain release gates.

## 2026-09-27 (PKT) — Release CI runtime-image gate
- Added `infra/scripts/phase8-image-runtime-smoke.ps1` and wired it after the API/web image build in `.github/workflows/ci.yml`. It starts isolated disposable candidate containers, polls API liveness, checks API docs disabled and expected disconnected readiness, then probes web `/`, `/login` and `/dashboard`. Cleanup runs even if a probe fails.
- Local execution on the built images passed in approximately 17 seconds. Evidence: `qa/phase8-image-runtime-smoke-20260926.json`; API `sha256:ce983374c8fe1ef0665abef6fe7f91dd1839af4fbdcbff7854b3e6e0762ef49e`, web `sha256:2b3862e9a342f14aac4ad0f05aebabbbf47ef149b5ed70357f19d36fdef569b4`. No candidate containers remained afterward.
- CI YAML parsed and `git diff --check` passed locally. Hosted CI has not yet been observed; integrated candidate deployment, real readiness, external alert transport and target restore/rollback remain open.

## 2026-09-27 — Safe preflight and current-tree regression
- `infra/scripts/phase8-preflight.ps1` now saves/restores temporary Compose/build environment values and caller location even on failure; the API-directory push is also guarded by `finally`. Its web build uses `.next-phase8-preflight`, with generated type paths declared in `apps/web/tsconfig.json` to avoid Next rewriting that file during the build.
- A preflight rerun initially caught two mypy type errors in concurrently evolving compliance assignment routes. Both calls now check the loaded course before passing it to `ensure_compliance_enrollment`; mypy passed all 51 source files and Ruff passed. These guards do not alter published-course validation.
- Rerun with `-SkipTests -SkipBuild`: development/production Compose, Alembic head `q2r3s4t5u6v7`, Ruff, mypy, web typecheck and ESLint **PASS**. Verified all seven touched environment values and the working directory were restored. Log: `qa/phase8-preflight-safe-rerun.log`.
- Separate isolated web build **PASS**, 49/49 routes; the live frontend continued to return HTTP 200. Log: `qa/phase8-isolated-preflight-build.log`.
- Current API regression **103 passed, 1 dependency deprecation warning**; log: `qa/phase8-api-regression-20260927.log`. This is local evidence for the current tree; integrated release-image deployment and external environment gates remain open.

## 2026-09-27 — Focused authenticated accessibility scan
- Added `apps/api/scripts/phase8_axe_audit.py` to scan authenticated routes with local axe-core in a disposable Chrome DevTools tab. It waits for the expected URL and rendered page heading, runs desktop/mobile viewports, records violation selectors and closes its tab. The demo login is local seed data only.
- Initial scan across six key routes at two widths found shared serious contrast failures and two mobile keyboard-scroll region failures. Corrected supporting-text contrast in the workspace, removed the native grey button background from sidebar sign-out, and made the dashboard activity and compliance coverage scrollers focusable with visible focus outlines.
- Final combined evidence: `qa/phase8-axe-focused-20260927.json`, **12 checks, 0 axe violations** across dashboard, compliance, compliance administration, catalog, people and settings at 1440px and 390px. Catalog and the other five pages were rerun separately with an explicit rendered-heading wait; raw components are `qa/phase8-axe-catalog-20260927.json` and `qa/phase8-axe-other-pages-20260927.json`.
- Web TypeScript and targeted ESLint passed. The compliance CSV download retains native navigation with a documented rule exception. Axe recorded 18 incomplete/manual-review rule instances across these checks. This is focused local automation, not full WCAG certification or a production accessibility assessment.
- Final service check caught a stray literal `\\n` after the dashboard component, which caused the development Next.js server to return HTTP 500. Removed it and reran web TypeScript successfully. The development homepage and login, API readiness, and production-style gateway health each returned HTTP 200. The current whole-tree `git diff --check` reports trailing blank lines in three separately edited web files; the dashboard page was corrected, and those other edits need owner review before a final repository-wide gate.

### Additional accessibility coverage and semantic review
- Extended the audit to seven more canonical routes: analytics, reports, assessments, credentials, team, L&D Operations and Skills. `/dashboard/manager` redirects to `/dashboard/team` and is therefore excluded as a distinct screen. At desktop/mobile widths, the **14 additional route checks have zero reported axe violations** after correcting contrast in breadcrumbs, metric headings and metric chips. The initial extended scan with six serious contrast findings is retained at `qa/phase8-axe-extended-core-20260927.json`; clean reruns are `qa/phase8-axe-extended-core-rerun-20260927.json`, `qa/phase8-axe-extended-workflows-20260927.json` and `qa/phase8-axe-semantic-rerun-20260927.json` (the initial assessments scan had zero violations).
- The audit now retains each incomplete rule's ID and affected selectors for manual follow-up and exits nonzero for **any** reported violation. Manual-review output revealed unsupported labels on unsemanticked divs; the breadcrumb is now a labelled `nav`, and credential summary a labelled `section`. Their final scan reports no `aria-prohibited-attr` incomplete results. Remaining incomplete results include contrast cases that require visual assessment. Across the original six and seven added routes, the local automated coverage is **26 route/viewport checks**, with zero reported violations in the latest applicable result for each route; this does not certify the remaining routes, keyboard journeys or assistive technology behavior.
- Python audit syntax, web TypeScript, targeted ESLint, and scoped `git diff --check` passed. Final checks: development login, API readiness and local gateway health each returned HTTP 200. Production accessibility certification and target-environment release gates remain open.

## 2026-09-27 — Gateway exposure default and release hygiene
- The production Compose gateway previously published HTTP on all host interfaces by default. It now binds `127.0.0.1:3100`; `WEB_BIND_ADDRESS` and `WEB_PORT` allow explicit protected-ingress topology overrides. The deployment guide and platform environment example state the TLS ingress and firewall requirements.
- `docker compose config --format json` passed with the default loopback binding and with an explicit test-interface override (`192.0.2.10:3200`). These checks validate configuration only; the Docker engine was unavailable, so this candidate was not deployed or certified over public TLS.
- Removed trailing blank lines in the web layout and assessments page. Scoped `git diff --check` passed; web TypeScript passed. A concurrent full web ESLint run exited with Windows code `3221226505` after roughly two minutes without source diagnostics; lint is not claimed as passed in this cycle. Re-run under a stable resource profile before release.
- Production release remains open pending integrated candidate deployment, externally verified TLS and alert delivery, real provider handshakes, accessibility/manual review and target restore/rollback evidence.
- Targeted ESLint for `apps/web/src/app/layout.tsx` and `apps/web/src/app/dashboard/assessments/page.tsx` passed. The whole-web ESLint gate remains open after its process-level failure.
- The release-config CI job now asserts the gateway's default published host/IP and port after Compose expansion. CI YAML parsed locally and the scoped diff check passed; hosted CI execution has not been observed.

## 2026-09-27 — Live gateway rebind after Docker recovery
- Docker Engine `29.5.3` became available. The existing production-style stack was healthy but its gateway still bound `0.0.0.0:3100` from an earlier configuration. Recreated only `docker-gateway-1` with an explicit `WEB_PORT=3100` and `WEB_BIND_ADDRESS=127.0.0.1` for that command. Its actual Docker port binding is now `127.0.0.1:3100->8080`.
- Gateway smoke passed with HTTP 200 for health/homepage, expected security headers, ready API/PostgreSQL/Valkey and migration exit 0. Evidence: `qa/phase8-gateway-local-bind-20260927.json` includes the binding and the exact running image IDs.
- The running API (`sha256:8a09494c...`) and web (`sha256:c98f71f...`) remain older than built candidate images (`sha256:ce9833...`, `sha256:2b3862...`). This is a hardening/smoke result for the existing deployment; candidate integrated deployment is still OPEN. The local `.env.phase8.local` specifies `WEB_PORT=3200`, so future recreations must reconcile the intended port explicitly before deployment.
- Host free memory was about 600 MB with two ClamAV containers consuming about 1.77 GiB combined. A parallel integrated stack was not started on this machine. Production-like candidate certification still requires an adequately resourced isolated target, current images, migration, authenticated journeys, scanning, backup/restore and rollback evidence.
