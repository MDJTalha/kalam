# Phase 2 — Course and Learner Core Progress Evidence

Date: 2026-09-25
Implementation root: C:\\Projects\\CorpLMS

## Current Phase 2 status

**IN PROGRESS**

Phase 2 has advanced through course governance, enrollment, learner journey, file-security and outbound notification hardening. It is not being marked closed until production SMTP delivery is configured and externally verified.

## Latest validation increment — 2026-09-25

### Outbound notification webhooks

Implemented:

- Added webhook delivery service using HTTP POST with bounded timeout and redirects disabled.
- Added HMAC-SHA256 request signing.
- Added event, event ID, tenant and timestamp headers.
- Added persistent webhook delivery state.
- Added unique webhook/notification delivery identity to prevent duplicate successful delivery.
- Added delivery attempt tracking.
- Added exponential retry scheduling with a 60-minute maximum delay.
- Added terminal failed state after eight unsuccessful attempts.
- Added persisted last-error information for operational diagnosis.
- Integrated notification webhook processing into the one-shot and continuous worker flows.
- Existing tenant-scoped webhook endpoint management remains permission protected.

Security note — hardened 2026-09-25:
- New webhook secrets are generated once, encrypted at rest with Fernet authenticated encryption, and never persisted as plaintext or as an HMAC key hash.
- Each encrypted secret records the active encryption key ID; the encryption key ring is injected through `WEBHOOK_ENCRYPTION_KEYS` and `WEBHOOK_ACTIVE_KEY_ID` rather than stored in the database.
- Webhook HMAC-SHA256 signatures are generated from the recovered original secret in process memory, so recipients can verify the signature with the secret issued at creation/rotation.
- Added `/rotate-secret` endpoint; the secret is returned once and is never readable from the API afterward.
- Added `scripts/rotate_webhook_encryption.py` so application encryption keys can be rotated by supplying the old and new keys during re-encryption.
- Migration `b7d4e8f1a2c3_add_encrypted_webhook_secrets.py` disables legacy endpoints that only have the unrecoverable SHA-256 secret hash; those endpoints must be rotated before activation.

### Database

- Added migration f1c2d3e4a5b6_add_webhook_delivery_state.py; that prior migration was applied in the earlier Phase 2 increment.
- Added migration b7d4e8f1a2c3_add_encrypted_webhook_secrets.py; upgrade completed successfully against the isolated project PostgreSQL instance on 2026-09-25.
- Added webhook_deliveries with unique (webhook_id, notification_id) protection.
- Added status, attempts, next-attempt, delivered-at and last-error state.

### Automated validation

- Webhook/security focused unit suite: **5 passed**.
- Targeted Ruff validation for the changed webhook/email/worker files: **PASS**.
- Python syntax compilation for all changed webhook/email/worker/migration utility files: **PASS**.
- SMTP verification utility executes and currently reports `SMTP_NOT_CONFIGURED` because no real provider settings are present in the connected development environment.
- Database-backed Phase 2 migration validation: **PASS**; Alembic head is `b7d4e8f1a2c3`.
- Phase 2 focused regression set: **13 passed, 29 deselected, 1 deprecation warning**.
- Full API regression on the migrated database: **42 passed, 0 environment-dependent failures**; ClamAV is now available through the local Docker service and the complete API regression is green. The local Windows environment uses host port 55000 because the original 53310 host port is reserved by Windows.
- Worker one-shot execution: **PASS**; 100 development-sink emails processed and `notification_webhooks_delivered` reported 0 because there is no active eligible webhook subscription.
- Frontend typecheck: **PASS**; production build: **PASS** with 44 routes; ESLint: **PASS with 2 warnings and 0 errors** for two unused local `load` functions.

### Remaining Phase 2 exit gates

- Production SMTP provider configuration and real external delivery verification. Current verification utility result: `SMTP_NOT_CONFIGURED`.
- Final backend regression closure requires the ClamAV service to be available so the full API suite can complete without the two environment-dependent scanner failures.
- Final Phase 2 evidence reconciliation and formal exit audit after the above gates are green.

The webhook outbound channel is now implemented with encrypted secret storage, recoverable signing, rotation, persistence, retry and failure-state handling. Phase 2 remains **IN PROGRESS**; no production credentials are invented or stored by the development workflow.

## Historical evidence

The earlier Phase 2 implementation included:

- Tenant-scoped course categories.
- Course ownership and active-user validation.
- Visibility controls.
- Tag normalization.
- Prerequisite enforcement.
- Bulk enrollment and due dates.
- Reminder generation and deduplication.
- Course Studio assignment controls.
- Approval, audience and capacity/waitlist governance.
- Content version history and restore.
- Learner journey completion evidence.
- ClamAV-backed upload scanning.
- Notification email delivery state with retry-safe worker processing.

Frontend evidence remains:

- TypeScript: PASS.
- ESLint: PASS.
- Next.js production build: PASS.
- 44 routes generated.

Release status remains **IN PROGRESS** until the final SMTP production-delivery evidence gate is completed.

## 2026-09-25 � SMTP Transport Hardening Follow-up

Implemented and validated:
- Added explicit implicit-TLS SMTP support through SMTP_SSL for providers that require SMTPS.
- Added configurable SMTP connection timeout through SMTP_TIMEOUT_SECONDS.
- SMTP verification now rejects the invalid combination of SMTP_SSL=true and SMTP_STARTTLS=true before attempting delivery.
- Existing SMTP failures remain retryable at the worker boundary.

Latest validation:
- Full API regression: **49 passed, 1 warning**.
- SMTP delivery regression: **PASS**.
- Ruff: **PASS**.
- Python syntax compilation: **PASS**.
- Frontend TypeScript: **PASS**.
- Frontend ESLint: **PASS**.
- Production build: **PASS**, **45 routes**.
- Current SMTP verification: **SMTP_NOT_CONFIGURED** because no real provider credentials are configured in the connected development environment.

Updated Phase 2 exit position:
- ClamAV-backed scanning is validated and available in the local environment.
- In-app, email worker delivery and outbound webhooks are implemented with persistence/retry/security controls.
- The remaining external evidence gate is real SMTP provider connection/authentication and delivery to a real mailbox.
- After that external test, perform the final Phase 2 evidence reconciliation and formal exit audit.

## Final Local Exit-Gate Reconciliation — 2026-09-25

Phase 2 local engineering work is now reconciled.

Validated in the latest controlled run:
- Phase 2 combined regression: **60 passed, 1 warning, 0 failures**.
- The warning is the known Starlette/httpx TestClient deprecation warning.
- ClamAV-backed scanning is available and validated.
- Webhook delivery/security behavior is covered by the focused regression suites.
- SMTP transport hardening is implemented and its local regression passes.
- Worker notification processing remains operational.
- Frontend TypeScript, ESLint and production-build evidence remain passing from the latest Phase 2 increment.

Final local position:
- Course/learner core: PASS.
- Database/migration work: PASS.
- Security controls: PASS.
- Notification/email implementation: PASS locally.
- Webhook delivery/security: PASS locally.
- External SMTP delivery: **OPEN — deployment/provider prerequisite**.
- Formal Phase 2 production closure: intentionally not claimed until a real SMTP provider and real mailbox delivery are verified.

Exit evidence: `docs/06-delivery/PHASE_2_EXIT_EVIDENCE.md`.
