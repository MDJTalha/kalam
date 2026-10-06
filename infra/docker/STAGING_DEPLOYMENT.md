# Kalam Staging Deployment

The staging workflow deploys an exact Git commit to a Docker host using the GitHub `staging` environment.

## Required GitHub environment configuration

Create an environment named `staging` and configure:

### Environment secrets

- `STAGING_HOST` — staging server hostname or IP
- `STAGING_USER` — non-root SSH deployment user
- `STAGING_SSH_KEY` — private SSH key for that deployment user
- `STAGING_POSTGRES_PASSWORD` — unique staging PostgreSQL password
- `STAGING_OPENAI_API_KEY` — optional OpenAI credential, required only when
  `STAGING_AI_PROVIDER=openai_compatible` and `STAGING_AI_ENABLED=true`
- `STAGING_ANTHROPIC_API_KEY` — optional Claude credential, required only when
  `STAGING_AI_PROVIDER=anthropic` and `STAGING_AI_ENABLED=true`

### Environment variables

- `STAGING_APP_DIR` — absolute path of the Kalam checkout on the staging host
- `STAGING_WEB_ORIGIN` — public HTTPS origin, for example `https://staging.example.com`
- `STAGING_AI_ENABLED` — optional `true`/`false`, default `false`; keep disabled
  until provider, model and tenant policy approval
- `STAGING_AI_PROVIDER` — optional `disabled`, `openai_compatible` or `anthropic`,
  default `disabled`
- `STAGING_AI_BASE_URL` — optional provider base URL, default `https://api.openai.com`
- `STAGING_AI_MODEL` — optional model/deployment key, required when AI is enabled

Do not put credentials in repository files, workflow YAML, or `.env.example`.

## Staging host prerequisites

The host must have Docker Engine, the Docker Compose plugin, Git, outbound registry/network access, and an SSH account that can run Docker. The checkout must already exist at `STAGING_APP_DIR` and have the repository remote configured.

The deployment creates a mode-0600 `.env.staging` on the host, checks out the exact GitHub Actions commit, runs the production Compose topology, and verifies API readiness plus gateway health.

## Release flow

1. GitHub Actions CI must pass on `main`.
2. Configure the `staging` environment once.
3. Push to `main` or manually dispatch the staging workflow with an exact ref.
4. Confirm migration completion and all containers healthy.
5. If AI is explicitly approved for staging, test the provider, enable it, enable the
   approved model, then enable the tenant policy from `/dashboard/ai`; otherwise keep
   the deployment kill switch closed.
6. Run the hosted QA suite against the staging origin.
7. Only after staging evidence is complete should a production deployment be considered.

## Important

This workflow does not provision cloud infrastructure or create DNS/TLS certificates. Those remain deployment-environment responsibilities. The gateway is intentionally not exposed directly by the application Compose file; public TLS must terminate at a protected reverse proxy or managed ingress.
