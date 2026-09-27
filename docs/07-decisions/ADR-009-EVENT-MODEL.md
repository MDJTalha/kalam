# ADR-009 — Audit and Event Model

Status: Accepted
Date: 2026-09-24

## Decision
Use durable audit logs for privileged business actions, signed webhooks for external delivery, and a learning-event boundary for xAPI-compatible statements.

## Why
These have different responsibilities: audit is governance evidence, webhooks are delivery integration, and learning events are interoperable activity data.

## Consequences
Event producers must be tenant-aware. Audit data avoids unnecessary sensitive payloads. Webhooks require signing, retry/replay controls and observability. Learning statements do not replace transactional business records.