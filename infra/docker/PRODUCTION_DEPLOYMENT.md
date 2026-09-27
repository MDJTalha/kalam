# Corporate LMS — Production Container Deployment

## Required variables

Set these outside source control:
- POSTGRES_PASSWORD
- WEB_ORIGIN
- API_ORIGIN
- NEXT_PUBLIC_API_ORIGIN
- ALLOWED_HOSTS must include both the public hostname and the internal Compose
  API hostname (for example, `lms.example.com,api`).
- SMTP settings
- future integration secrets

Never commit real credentials.

## Start

From the repository root, use the exact release commit and set the required variables in the deployment secret store. Run the Phase 8 preflight before deployment. Then start the production topology:

```powershell
docker compose -f infra/docker/docker-compose.app.yml up -d --build
```

The one-shot `migrate` service applies Alembic migrations before the API starts. Verify that it exited successfully and that the API readiness endpoint passes. The dedicated `worker` image runs `/app/worker/run.py` for reminders, compliance, email, webhooks and scheduled reports; verify its container and controlled job-cycle evidence. Do not run an additional migration through `exec api`; follow the Phase 8 release runbook for health, smoke, and evidence checks.

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

The Compose gateway publishes plain HTTP on `127.0.0.1:3100` by default (`WEB_BIND_ADDRESS` and `WEB_PORT`). Terminate public TLS at a reverse proxy or managed ingress on the same host and forward to this loopback address. Configure the public hostname, certificate, HTTPS redirect and HSTS at that TLS ingress; verify them from outside the host. If the TLS ingress is on a different host, bind the gateway to an explicitly protected interface with `WEB_BIND_ADDRESS` and restrict access to the ingress through a firewall. Never expose the plain HTTP gateway directly to public clients. Do not expose the API publicly unless the deployment architecture requires it.

## Release rule

A production deployment is incomplete until migrations, health/readiness, smoke tests, backup verification, logging and rollback procedures have all been evidenced.
