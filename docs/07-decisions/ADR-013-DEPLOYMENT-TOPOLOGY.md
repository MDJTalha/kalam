# ADR-013 — Production Deployment Topology

Status: Accepted
Date: 2026-09-24

## Decision
Target a containerized production topology: web, API and worker containers behind a reverse proxy, with PostgreSQL, Redis-compatible infrastructure and private object storage.

## Why
This matches the modular monolith strategy and supports repeatable deployment without forcing microservices.

## Consequences
Configuration and secrets are injected per environment. Health/readiness checks and migrations are deployment gates. Backups, restore, monitoring, rollback and disaster recovery remain Phase 8 evidence.