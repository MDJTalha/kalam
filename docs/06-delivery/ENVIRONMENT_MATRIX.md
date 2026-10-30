# Kalam — Environment Matrix

Version: 0.4
Status: Local API/web checks refreshed — 2026-10-30; hosted QA/UAT/production remain unverified.

| Environment | Web | API | Database | Redis/Jobs | Storage | Secrets |
|---|---|---|---|---|---|---|
| Development | Next.js local Windows | FastAPI/Uvicorn | PostgreSQL Docker | Valkey local | Local filesystem | .env files, never committed |
| QA (local smoke only) | Temporary browser instance on port 3002 | Temporary API on port 8003 | Browser smoke used configured local app DB; API regression suite used separate kalam_test DB on port 5435 | No persistent QA worker/cache environment certified | No isolated QA object store certified | Local test-only values; no production secrets |
| UAT | Production-like containers | Production-like API | Separate DB | Separate worker/cache | Isolated object store | Secret manager |
| Production | Container behind reverse proxy | Container | Managed/HA PostgreSQL option | Redis/Valkey service | S3-compatible object storage | Secret manager |

## Canonical local development endpoints

- Web: http://127.0.0.1:3000
- API: http://127.0.0.1:8000
- PostgreSQL host port: 55434 -> container 5432
- Valkey host port: 56379 -> container 6379
- ClamAV host port: 55000 -> container 3310

The temporary port-3002/8003 browser pair is a local pre-authentication test harness, not a separately provisioned QA data plane. Its browser checks were read-only. The full API pytest suite and targeted database regressions used the dedicated PostgreSQL test database on port 5435. Do not describe either local harness as hosted QA or UAT.

## Environment rules

- Database, secrets, storage and integration credentials are isolated per environment.
- Production secrets never belong in repository files.
- Demo seed data is development/QA evidence only.
- External integration credentials are never reused across environments.
- Web/API origins and allowed hosts are explicit configuration.
- Local runtime configuration must match docker-compose.yml.
- CI uses service-native ports and must not depend on local Windows host mappings.

## Phase 0 finding

The previous matrix documented PostgreSQL host port 55433 while docker-compose.yml exposes 55434. The baseline is now corrected to 55434.
