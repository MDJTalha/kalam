# Kalam Readiness — Phase 1 Product Capability Audit

Date: 2026-10-11
Status: **IN PROGRESS — NOT ENDORSED COMPLETE**
Scope: Product capabilities in `docs/02-product/REQUIREMENTS_BASELINE.md` and `docs/02-product/REQUIREMENTS_TRACEABILITY_MATRIX.md`.

## Scope decision

The user approved using the repository's current requirements baseline as the audit scope in conversation on 2026-10-11. Sections 2 (Must-have release capabilities) and 3 (Secondary capabilities) form the feature inventory; the acceptance, data, permission, UI, API, file, notification, reporting, integration and AI controls in Sections 5–15 also apply where relevant. Section 4 (Future/controlled capabilities) is not included in the 100% launch denominator unless an item is also required by an in-scope release capability. This scope decision is not commercial customer acceptance or legal approval.

## Completion criteria

Phase 1 can be endorsed complete only when all of the following are evidenced against the current source/candidate:

1. Every in-scope requirement has a concrete implementation reference, owner-facing acceptance criterion, and passing automated or documented manual test; no unknown, placeholder, or unsupported behavior is silently counted as complete.
2. The baseline's learner, manager, L&D admin, compliance admin, instructor, and executive journeys pass through the actual frontend, API, and isolated database with representative roles and tenant boundaries.
3. Required feature behavior, permission checks, failure states, persisted results, and duplicate/idempotency expectations pass the corresponding regression tests.
4. Any live integration is either tested with real credentials/requests or explicitly identified as deployment-dependent and excluded from the approved release scope.
5. The exact current source is the source tested. A smoke against an older running image is not candidate evidence.

## Evidence observed so far

- The traceability matrix contains **63 requirement rows**; the API test tree contains **38 Python test modules**. These counts establish inventory only, not coverage or pass status.
- The approved in-scope baseline enumerates **72 must-have checklist items** and **14 secondary checklist items**. The 63 matrix IDs are higher-level traceability records, not a one-to-one evidence record for all 86 checklist items; a granular crosswalk is needed to endorse complete coverage.
- Source-level spot-checks confirm programs/cohorts/learning paths and session scheduling/attendance have models and API routes. SaaS client accounts/tenant provisioning and CSV exports also exist.
- Preliminary gaps needing full confirmation: notification APIs cover feed/preferences/read-state but no user-managed notification-template CRUD was found; bulk onboarding supports email-only CSV invitations and exports exist, but a general learner/people data import workflow was not found; no explicit external-learner lifecycle was found. Calendar/workshop coverage appears partial through generic live sessions rather than a dedicated workshop/calendar workspace. These are not yet closed findings: a complete source/UI/test search and disposition per item is still required.
- A tenant-scoped knowledge-base capability has been implemented in the current working tree: migration/model, published-only learner reads, tenant-admin create/edit/publish/archive/restore controls, audit events, and Help Center search/read UI. PATCH now allows clearing a summary and rejects `tags: null` with HTTP 422; the integration test covers these cases plus archive visibility and tenant denial. A migration-unavailable state no longer blocks support-case history. Verified: focused OpenAPI route registry tests **6 passed**, focused Ruff checks passed, Alembic graph has one head, offline migration SQL generation succeeds, frontend typecheck and targeted ESLint pass. The PostgreSQL-backed knowledge-base test has not run, so the feature is not endorsed end-to-end.
- Live-session access now includes sessions for a learner's own active/completed course enrollments as well as sessions they instruct; the query remains tenant-scoped. Session creation now rejects naive/reversed timestamps and cross-tenant or inactive instructor IDs. A database-backed regression test covers learner visibility and isolation; database-free Pydantic schedule-validation checks run in the focused route registry suite.
- An earlier isolated full API run recorded **174 passed** in the Step 1 readiness report. It predates the latest configuration fixes and is not a fresh full-suite result for the current tree.
- Current focused route/storage regression after the recent settings fixes: **12 passed**; Ruff passed for the changed settings and test files.
- A fresh read-only security smoke against the running Docker stack passed **18/18 checks**: gateway home/security headers, anonymous API denial, foreign-origin/CORS rejection, trusted CORS, request ID and direct API untrusted-Host rejection. This validates the running image only; it does not certify the current uncommitted source, public TLS/ingress, or tenant journeys.
- The running API image previously reported `storage_backend=local`; current production Compose defaults to S3, but no provider-backed upload/download, tenant-isolation, or off-host recovery test is evidenced. Storage and recovery are not endorsed.
- Successful developer-account sign-in, authenticated `/auth/me`, role-specific platform-owner screens, and the six baseline user journeys have not been verified in this audit.
- Docker is currently responsive and core containers in both `kalam-prod` and the separate `kalam-tunnel` project report healthy. The tunnel database uses a separate volume but is not published on the host port expected by `infra/scripts/phase8-local-regression.py`, so that runner cannot be used unchanged. Free host memory was about **0.86 GB** during this continuation. No database-backed test was run in this continuation.
- Current-tree checks in this continuation: API Ruff passed; route-registry tests **6 passed** (including session-time validation); Alembic has one head and offline migration SQL generation succeeds; frontend typecheck and targeted ESLint pass. The full API suite, knowledge-base/session integration tests, production frontend build and six-role browser journeys remain unverified against this exact working tree.

## Phase decision

**Phase 1 remains open.** The baseline and traceability artifacts are useful, but end-to-end verification against the exact current source has not been completed. No percentage or 100% endorsement is assigned from file counts, historical test results, or the local smoke alone.

## Next actions

1. Establish a stable, isolated PostgreSQL/Redis/ClamAV test target without using the live Kalam database.
2. Run the full current-source API suite and capture per-requirement evidence; resolve failures before closing affected requirements.
3. Execute the six role-based user journeys in a browser against the same current-source candidate, including tenant-boundary negative checks.
4. Reconcile any capability with missing evidence, disabled status, or external-provider dependency against the approved baseline and record a disposition.
5. Re-score the phase from passed in-scope criteria; only then consider endorsement.

## Follow-up — QA/QC audit, 2026-10-11

- Fresh frontend TypeScript and ESLint passed for the current worktree; the last focused login/navigation changes are included.
- Database-independent API route-registry, storage configuration/S3 adapter, and AI provider-adapter regressions: **21 passed**. Ruff passed on changed API and test files.
- Alembic reports one head (`k1b2c3d4e5f6`); offline SQL generation from `r7s8t9u0v1w2` succeeded. No migration was applied and no database-backed suite ran in this follow-up.
- Read-only `kalam-prod` gateway probes for `/`, both health-live aliases, and `/api/v1/health/ready` returned **200**; `kalam-prod` and `kalam-tunnel` core containers reported healthy. This does not identify those images as the current uncommitted candidate. Two containers in the separate `docker` project remain unhealthy.
- Production Compose configuration validation and `nginx -t` against the running gateway both passed; these are configuration/runtime checks, not a candidate image build.
- Current-source production build and browser journeys remain unverified (no browser session; host free memory fell below 0.5 GB). The full API suite, S3-backed file workflow, role/tenant journeys, and overall release acceptance remain open.
- The separate frontend release-checklist denominator is 16 checks; **3/16 (19%)** have fresh evidence for this checkout. This is verification coverage only, not a feature completion percentage or Phase 1 endorsement.

Phase 1 remains **IN PROGRESS — NOT ENDORSED COMPLETE**.
