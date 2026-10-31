# Kalam — Final Certification Execution Evidence
Date: 2026-10-31

## Scope

This record captures evidence executed after the current mainline candidate was re-read. It deliberately separates local verification from exact-candidate production certification.

## Candidate

Current main candidate observed: `2a26dd18ad57c024d99be5216db77eb76781ca8a`.

Hosted PR evidence already recorded for the exact application tree:
- PR #30
- hosted run #470
- run ID `41214013410`
- API, Web and release-config passed, including production-image runtime smoke.

No separate push-triggered run for the merge SHA is exposed by the available GitHub workflow connector.

## Local environment verification

Desktop Commander device MDT was online and local Docker services were healthy:
- PostgreSQL: healthy, host port 55434
- Valkey: running, host port 56379
- ClamAV: healthy, host port 55000

The preflight script was executed. Compose validation passed, but the installed local checkout at `C:\Projects\Kalam` is not the GitHub certification checkout and does not contain `apps/api`; therefore the API portion of the preflight correctly stopped rather than producing false certification evidence.

The local web application responded successfully to `GET /login` with HTTP 200. This is only availability evidence for the installed local checkout, not authenticated browser certification of the exact candidate.

## Backup restore drill

An actual PostgreSQL restore was executed against a disposable database:

1. Created disposable database `kalam_restore_verify_20261031`.
2. Copied the existing recovery-drill dump into the PostgreSQL container.
3. Ran `pg_restore --no-owner --exit-on-error`.
4. Restore completed with exit code 0.
5. Restored database contained 99 public tables.
6. Dump inventory contained 99 TABLE DATA entries.
7. Disposable database was dropped with FORCE after verification.

Backup artifact:
`backups/recovery-drill-20261011-053831/kalam-prod-corplms-20261011-053831.dump`

Observed SHA-256:
`57CF9D3CAEBFF2A1059B47FF2EF12E623C7577E89F5AAB2B3286050938BEB2CB`

Observed size: 1,991,373 bytes.

This closes the question of whether this retained dump can be physically restored into PostgreSQL locally. It does **not** by itself certify current production backup freshness, off-host retention, measured RTO/RPO, or disaster-recovery failover.

## AWS state

A direct `aws sts get-caller-identity` check returned an expired AWS session requiring re-authentication. The active Kubernetes context is `docker-desktop`; available contexts are `docker-desktop` and `rancher-desktop`.

Therefore no AWS production deployment, production TLS, managed secrets, staging smoke, production rollback, or cloud failover is claimed by this evidence record.

## Certification interpretation

PASS evidence added:
- local Docker dependency health
- local login endpoint availability
- actual disposable PostgreSQL restore
- restored schema inventory
- backup hash/size capture

Still NOT CERTIFIED:
- exact-candidate authenticated browser matrix
- exact-candidate full API regression from a clean certification checkout
- live cross-tenant negative matrix
- manual accessibility sign-off
- 10k+ performance certification
- migration rollback drill
- AWS/staging deployment
- production observability/smoke
- executed DR/failover with measured RTO/RPO
- AI provider certification
- independent final approval

No production 9.99/10 claim is made until those gates have exact evidence.
