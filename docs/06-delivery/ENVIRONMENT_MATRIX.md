# Corporate LMS — Environment Matrix

Version: 0.2
Status: Phase 0 technical gate passed — 2026-09-25

| Environment | Web | API | Database | Redis/Jobs | Storage | Secrets |
|---|---|---|---|---|---|---|
| Development | Next.js local Windows | FastAPI/Uvicorn | PostgreSQL Docker | Valkey local | Local filesystem | .env files, never committed |
| QA | Planned isolated web/API | Planned isolated API | Separate DB | Separate worker/cache | Isolated object store | CI/secret store |
| UAT | Production-like containers | Production-like API | Separate DB | Separate worker/cache | Isolated object store | Secret manager |
| Production | Container behind reverse proxy | Container | Managed/HA PostgreSQL option | Redis/Valkey service | S3-compatible object storage | Secret manager |

## Canonical local development endpoints

- Web: http://127.0.0.1:3000
- API: http://127.0.0.1:8000
- PostgreSQL host port: 55434 -> container 5432
- Valkey host port: 56379 -> container 6379
- ClamAV host port: 55000 -> container 3310

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
