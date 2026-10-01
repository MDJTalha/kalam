# Kognivon Task 19 — Notifications and Workflow Actions

Date: 2026-09-29
Status: Complete

## Audit scope

- In-app notification creation, classification, action links, unread/read state, and tenant/user visibility.
- User notification preferences and mandatory security notifications.
- Dedupe behavior across learning reminders, compliance automation, support workflows, and credentials.
- Background email delivery and retry behavior.
- Worker orchestration for reminders, compliance, email, webhooks, reports, and CRM renewals.

## Changes made

- Corrected notification deduplication from globally unique `dedupe_key` to a tenant-scoped unique constraint. Identical workflow keys can now exist independently in separate tenants.
- Added migration `j6k7l8m9n0_scope_notification_dedupe.py` and upgraded the local database.
- Updated the worker email processor to honor `email_enabled` and category preferences while always allowing security notifications.
- Added a worker regression test covering suppressed learning mail, enabled learning mail, and mandatory security mail.

## Existing workflow coverage confirmed

- Learning enrollment, due reminders, completion, compliance reminders/escalations, assessment credentials, support replies/status changes, notification read state, webhooks, and CRM renewal tasks have active event paths.
- Dedupe keys are used for recurring reminders and workflow-generated notifications.
- Worker failures leave email delivery state unset so eligible messages can retry.

## Verification

- `alembic upgrade head` — passed.
- `alembic check` — passed with no new upgrade operations.
- Worker tests — 2 passed.
- Due-date reminder idempotency/tenant-scope regression — passed.
- Python compilation — passed.
