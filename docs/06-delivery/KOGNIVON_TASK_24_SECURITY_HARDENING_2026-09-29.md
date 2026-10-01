# Kognivon Task 24 — Security Hardening

Date: 2026-09-29  
Status: Complete for the current application/configuration pass.

## Audit scope

Reviewed tenant authorization and session boundaries, CORS and trusted hosts, origin checks for state-changing requests, upload limits, webhook secret handling, integration credential references, security headers, and production configuration defaults.

## Change made

Added a production startup validator to `app/core/config.py`. When `APP_ENV` is production, the API now refuses to start unless:

- `COOKIE_SECURE=true`;
- `API_DOCS_ENABLED=false`;
- `DEV_EMAIL_SINK=false`; and
- `INTEGRATION_ALLOW_PRIVATE_URLS=false`.

This converts deployment misconfiguration into a visible startup failure instead of silently weakening cookie, documentation, email, or SSRF defenses.

## Existing controls verified

- CORS is restricted to the configured web origin and credentials are explicit.
- Trusted hosts are configured independently.
- State-changing requests reject unexpected `Origin` values.
- Uploads are streamed with a configured size limit and path traversal protection.
- Webhook secrets are encrypted at rest and returned only at creation/rotation.
- Sessions store token hashes rather than raw session tokens.
- Security response headers are applied at both web and API layers.

## Verification

- Python compilation passed for `apps/api/app`.
- Authentication lifecycle and OIDC tests: 4 passed.
- `pnpm --filter web typecheck` passed in the preceding Task 23 verification.
- `git diff --check` passed in the preceding verification.

## Follow-up

Production deployment should still run dependency scanning, external perimeter testing, secret rotation rehearsal, rate-limit validation, and a formal upload malware-scan test against the deployed infrastructure.
