# ADR-006 — Background Jobs

Status: Accepted
Date: 2026-09-24

## Decision
Keep asynchronous jobs behind a worker boundary using a Redis-compatible queue/cache service; do not split into microservices in Phase 0.

## Why
Notifications, imports, reports and future schedulers can be retried without coupling long-running work to web requests.

## Consequences
Critical jobs require idempotency, observable status and retry/backoff. Redis is not the source of truth for grades, completion, certification, compliance or authorization.