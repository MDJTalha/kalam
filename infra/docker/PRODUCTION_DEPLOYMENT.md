# Corporate LMS — Production Container Deployment

## Required variables

Set these outside source control:
- POSTGRES_PASSWORD
- WEB_ORIGIN
- API_ORIGIN
- NEXT_PUBLIC_API_ORIGIN
- SMTP settings
- future integration secrets

Never commit real credentials.

## Start

docker compose -f infra/docker/docker-compose.app.yml up -d --build

## Migration

docker compose -f infra/docker/docker-compose.app.yml exec api python -m alembic upgrade head

## Seed

Demo seed data is for development/UAT only. Never run the seed command against a customer production database.

## Health

API: GET /api/v1/health
Readiness: GET /api/v1/health/ready
Web: GET /

## Backup

Configure PostgreSQL backups outside the application container lifecycle.

Restore must be tested in a separate environment before recovery is considered verified.

## Reverse proxy

Put the web application behind a TLS-capable reverse proxy or managed ingress. Do not expose the API publicly unless required by the deployment architecture.

## Release rule

A production deployment is incomplete until migrations, health/readiness, smoke tests, backup verification, logging and rollback procedures have all been evidenced.
