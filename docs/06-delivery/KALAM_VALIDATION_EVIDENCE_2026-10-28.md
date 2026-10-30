# Kalam Local Validation Evidence — 2026-10-28

**Repository:** `MDJTalha/kalam`
**Local path:** `C:\Projects\Kalam`
**Branch:** `work/kalam-local-changes-2026-10-26`
**Disposition:** Local foundation validation PASS. Phase 8 production/commercial release remains OPEN.

## Current-tree automated validation

- Full Phase 0 validator with `-RunDatabaseTests`: **PASS**.
- Isolated PostgreSQL test database: migration-head check passed; the disposable database was dropped after test completion.
- API regression suite: **191 passed, 1 non-blocking Starlette/httpx deprecation warning** (171.66 seconds).
- Ruff: **PASS**.
- mypy: **PASS**, 65 API source files.
- Python dependency consistency (`pip check`): **PASS**.
- Production dependency vulnerability audit (`pip-audit -r requirements-prod.txt`): **PASS**, no known vulnerabilities found.
- Web TypeScript: **PASS**.
- Web ESLint: **PASS**.
- Next.js production build: **PASS**, 88/88 static pages generated and application routes enumerated.
- Compose configuration: **PASS**.
- Repository whitespace check: passed before final report creation; rerun after any subsequent edits.

The test database was isolated in the existing `corplms-postgres-test` container on host port 15432 and named `corplms_test_kalam_20261028`. It was separate from the PostgreSQL listener on port 5432 and was removed after the passing run. No production database was used.

## Engineering fixes made during validation

1. Updated 35 hard-coded demo-password references across 16 API test modules to read `CI_FIXTURE_PASSWORD`. This aligns the tests with the CI workflow's generated, test-only fixture credential and avoids coupling test assertions to a fixed password.
2. Updated `infra/scripts/phase0-validate.ps1` to pass `KALAM_TEST_DATABASE_URL` to pytest when database tests are enabled, restore both database environment variables after the run, and require an explicit fixture password for database-connected testing.
3. Isolated the Phase 0 Next.js production build under `.next-phase8-final` to avoid colliding with a running development server. The previous default-output attempt failed with a Windows `EBUSY` lock; the isolated build completed successfully.
4. Removed the generated `.next-phase8-final/dev/types` include that Next.js auto-added to `apps/web/tsconfig.json` after the build, preserving the existing intended configuration.

## Browser and accessibility evidence

The current local QA records dated 2026-10-28 report:
- Authenticated browser/accessibility sweep: 24 browser observations, 12 accessibility scans, zero reported axe violations in the scanned route/role combinations, and an empty failures list.
- Candidate public/learner accessibility smoke: four routes, zero reported axe violations, and an empty failures list.
- Role interactions: admin login and capability-gap recalculation; manager team filtering; learner catalog access; course creation, lesson authoring, publishing, enrolment, and completion; the report records no failures.

These are local automated checks, not independent WCAG certification or proof against a deployed release candidate. The recorded incomplete axe rules still require manual review.

## Release status and remaining external gates

Phase 8 remains **OPEN**. Local validation does not establish:
- a successful hosted CI run for the exact final candidate;
- a reviewed, immutable commit/tag and deployed API/web/worker image digests;
- target-environment migration, worker-cycle and authenticated gateway smoke;
- public TLS/certificate, ingress/host/origin controls and alert delivery;
- off-host database and file/object-storage backups with target restore verification and measured RPO/RTO;
- real SMTP, webhook, enabled AI-provider and HRIS/OIDC integration handshakes;
- production-like performance/load results, manual keyboard/assistive-technology review, customer UAT and legal approval.

The local branch still contains staged, unstaged and untracked work. No commit, push, merge or production deployment was performed as part of this validation. Existing local changes were preserved.
