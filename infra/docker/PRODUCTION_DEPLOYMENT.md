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
- Optional AI provider settings and secrets. Keep `AI_PROVIDER=disabled` until the
  provider, model and tenant policy have been tested in the Kalam AI workspace.
  Keep `AI_ENABLED=false` until the provider connection test has passed; set it to
  `true` only for an approved tenant activation.
  Use `OPENAI_API_KEY` for OpenAI-compatible providers or `ANTHROPIC_API_KEY` for
  Claude; the API stores only the environment-variable reference.
- The staging workflow maps `STAGING_AI_ENABLED`, `STAGING_AI_PROVIDER`,
  `STAGING_AI_BASE_URL` and `STAGING_AI_MODEL` repository variables, plus
  `STAGING_OPENAI_API_KEY` / `STAGING_ANTHROPIC_API_KEY` environment secrets. If
  `STAGING_AI_ENABLED` is `true`, the matching provider secret is required by the
  workflow; the default remains `false`.
- future integration secrets

Never commit real credentials.

## Start

From the repository root, use the exact release commit and set the required variables in the deployment secret store. Run the Phase 8 preflight before deployment. Then start the production topology:

```powershell
docker compose -f infra/docker/docker-compose.app.yml up -d --build
```

The one-shot `migrate` service applies Alembic migrations before the API starts. Verify that it exited successfully and that the API readiness endpoint passes. The dedicated `worker` image runs `/app/worker/run.py` for reminders, compliance, email, webhooks and scheduled reports; verify its container and controlled job-cycle evidence. Do not run an additional migration through `exec api`; follow the Phase 8 release runbook for health, smoke, and evidence checks.

After the API and web services are healthy, an authorized tenant administrator can
register the provider and model at `/dashboard/ai`, run the provider connection test,
enable the tested provider, enable the approved model, and then enable the tenant
policy. AI activation is fail-closed: without a ready and enabled provider, enabled
model and enabled policy, core LMS workflows remain available and AI requests are
rejected as unavailable.

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
