# Kalam Local Build, Recovery and Migration Evidence — 2026-10-31

## Scope and candidate

- Repository: `MDJTalha/kalam`
- Candidate source commit tested locally: `a6399efe06284f8fd3e40e6227c02047ea24924a`
- Branch: `work/final-production-readiness-2026-10-31`
- Workstation checkout was reset to and verified at the exact candidate SHA before the final image build.
- This record distinguishes fresh-database migration validation from upgrade validation of retained recovery archives.

## Exact-candidate production image build

The exact candidate's production images were built locally using:

```powershell
docker compose -f infra/docker/docker-compose.app.yml build api web worker
```

Observed results:

- API image build completed.
- Worker image build completed.
- Web production build completed, including TypeScript, lint and optimized Next.js build.
- Next.js generated 89 routes.
- ESLint reported two non-blocking unused-variable warnings in `apps/web/src/app/dashboard/people/admin/page.tsx` (`RolePage`, `UnitPage`); no lint errors.
- Exact-candidate image manifest digests:
  - API: `sha256:3fe9e137c0f0f27cce22e8660b35827b1421b1a227719663d552e84366bc7349`
  - Web: `sha256:8800752deb696bff328839376eceea9b01bea41f341fd7df0e7f2a16111692b7`
  - Worker: `sha256:1eea9da9590d351385c232758359b312002ab4709197acfb17da1cdb58f62245`
- Isolated local Compose configuration validation passed.

The subsequent attempt to start the complete isolated API/worker/web/gateway stack did not yield a final health result. The remote workstation became unresponsive while Compose was pulling `nginx:1.29-alpine`. Therefore no API, web, gateway or browser runtime PASS is claimed from that startup attempt.

## Fresh-database migration

A new isolated PostgreSQL database was created and migrated using the exact-candidate API image and Alembic.

- Result: PASS
- Final Alembic revision: `s1t2u3v4w5x6`
- Synthetic seed completed:
  - 3 tenants
  - 10,006 users
  - enterprise reference dataset plus demo and tenant-isolation fixtures

This validates the fresh-database forward-migration path. It does not validate upgrade from the retained September backup snapshots.

## Retained backup restore tests

Both custom-format PostgreSQL 18.6 archives were restored successfully into separate disposable PostgreSQL 18.6 containers. The restore containers and volumes were removed after validation.

| Archive | Created (UTC) | Size | SHA-256 | Restored public tables | Tenant rows |
|---|---|---:|---|---:|---:|
| `host-before-phase8-restore.dump` | 2026-09-29 18:17:25 | 639,769 bytes | `2682B9A423EED760DC9375E8127F402DF775F03449EFA85889AB5B5B29318FE8` | 77 | 4 |
| `phase8rc-db-restore.dump` | 2026-09-29 18:16:25 | 234,783 bytes | `FD38B85A463D0BEFCE2E635CE895191E7AC0B3277D3E06BE85F2EC654AD0004E` | 73 | 2 |

Both restored snapshots reported Alembic revision `b3c4d5e6f7g8`.

### Restored-snapshot forward migration failure

A forward migration was attempted against the restored `host-before-phase8-restore.dump` snapshot using the exact-candidate API image.

The attempt failed because the schema already contained `users.preferences` while Alembic still reported `b3c4d5e6f7g8`. The candidate migration `d5e6f7g8h9i0_user_preferences.py` attempted to add the existing column and PostgreSQL returned `DuplicateColumnError`.

The existing column was inspected and found to be:

- PostgreSQL type: `jsonb`
- Nullable: `NO`
- Default: `'{}'::jsonb`
- Rows with NULL preferences: `0`

A local experimental idempotency guard was briefly tested and then reverted because the next migration failed on another pre-existing object: `support_cases` already existed when migration `e6f7g8h9i0j1_support_cases.py` attempted to create it. No migration was stamped, no database history was manually advanced, and no speculative migration changes were retained.

This is evidence of schema/Alembic-history drift in the retained snapshot. It is not safe to repair by blindly stamping revisions. The snapshot requires a full schema-to-migration reconciliation before it can be used as a forward-migration certification fixture.

## Accessibility evidence review

Existing axe reports are historical and are not fresh scans of the exact candidate:

- `phase8-axe-authenticated-20261004.json`: 12 checks, zero recorded violations, 30 incomplete/manual-review items.
- `phase8-axe-routes-01-20261004.json`: 20 checks, zero recorded violations, 50 incomplete/manual-review items.
- `phase8-axe-routes-02-20261004.json`: 20 checks and 7 recorded violation rules, including:
  - critical `aria-required-children` on `.integration-provider-list`;
  - serious `color-contrast` findings on the integrations page;
  - serious `scrollable-region-focusable` findings on mobile instructor tables.
- `phase8-axe-integration-fixes-20261004.json` still recorded 8 color-contrast nodes across desktop/mobile.
- `phase11-axe-current-20261001.json` recorded 18 violation rules across 12 checks.

No fresh axe scan was completed against the exact candidate during this execution. Manual WCAG 2.2 AA review remains outstanding.

## Performance evidence review

The retained `phase8rc-performance-current.json` is historical, not an exact-candidate run. It records:

| Endpoint | Requests / concurrency | p95 | Gate |
|---|---:|---:|---|
| `/api/lms/health` | 100 / 10 | 447.94 ms | 750 ms limit — within limit |
| `/api/lms/health/ready` | 30 / 5 | 2,295.04 ms | 1,000 ms limit — exceeded |
| `/api/lms/auth/me` | 100 / 10 | 419.99 ms | 1,500 ms limit — within limit |

The historical readiness check failed its latency threshold. No fresh exact-candidate load run was completed in this execution.

## Certification consequences

- C0 Candidate integrity: CERTIFIED for the tested source SHA.
- C1 Hosted CI: CERTIFIED from successful exact-candidate hosted run #502.
- C7 API/data integrity: CERTIFIED from the successful exact-candidate hosted API job.
- C11 Backup/restore: PARTIAL — both archives restore, but freshness and restore-to-current-schema recovery are not proven.
- C12 Migration safety: FAILED for the tested restored-snapshot forward-upgrade path; fresh-database migration passed.
- C17 AI governance: CERTIFIED only for fail-closed disabled-by-default posture.
- Browser E2E, live authorization/tenant-isolation browser evidence, fresh accessibility, fresh performance, observability failure/alert/recovery, AWS/staging, independent review and production smoke/rollback remain NOT CERTIFIED.

No production deployment, merge, production rollback, or DR/failover PASS is asserted by this evidence record.
