# Phase 8 — Operations Checklist

## Daily/continuous
- Public gateway availability, with immediate critical alert on failure.
- API liveness/readiness; two consecutive failures warn, and five minutes of failure is critical. Preserve probe state and verify alert delivery.
- Database and Valkey health.
- Worker failure/retry signals.
- Authentication failure/lockout anomalies.
- Notification/webhook/integration delivery failures.
- AI provider failures/budget exhaustion where enabled.
- Disk/storage capacity and upload scan failures.

## Release-day
- Verified PostgreSQL and upload/object-storage backups, their checksums, and separate restore tests.
- Alembic head matches release.
- CI/preflight green.
- Image digests captured.
- External dependencies certified.
- Browser and focused axe accessibility smoke green; manual review of incomplete axe checks, keyboard interaction, assistive technology and remaining routes still required.
- Security headers/TLS verified.
- Rollback owner available.

## Periodic
- Restore drill.
- Secret/key rotation.
- Webhook encryption-key rotation.
- Dependency vulnerability review.
- Access/RBAC review.
- Audit-log review.
- Capacity/performance review.
- Certificate/domain expiry review.
- Disaster-recovery tabletop exercise.
