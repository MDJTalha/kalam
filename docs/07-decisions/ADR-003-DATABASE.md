# ADR-003 — Database and Migration Strategy

Status: Accepted
Date: 2026-09-24

## Decision
Use PostgreSQL as the system of record, SQLAlchemy as the ORM/data-mapping layer and Alembic for schema migrations.

## Why
- Strong relational integrity for tenant, learning and compliance data.
- Native UUID/JSONB support.
- Explicit foreign keys and unique constraints.
- Repeatable migration history.

## Consequences
Schema changes are migration-controlled. Direct production schema edits are prohibited except documented emergency procedures. Backups and restore testing become Phase 8 release evidence.