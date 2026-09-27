# Corporate LMS — ADR Index

Version: 0.1
Status: Phase 0 baseline

| ADR | Decision | Status |
|---|---|---|
| ADR-001 | Next.js + TypeScript web stack | Accepted |
| ADR-002 | FastAPI + Python API stack | Accepted |
| ADR-003 | PostgreSQL + SQLAlchemy + Alembic | Accepted |
| ADR-004 | HTTP-only session authentication with Argon2 | Accepted |
| ADR-005 | Explicit tenant-scoped multi-tenancy | Accepted |
| ADR-006 | Redis-compatible background job boundary | Accepted |
| ADR-007 | Storage abstraction; local dev and S3-compatible production | Accepted |
| ADR-008 | Versioned REST API under `/api/v1` | Accepted |
| ADR-009 | Audit events + webhooks + learning-event boundary | Accepted |
| ADR-010 | Optional governed AI provider abstraction | Accepted |
| ADR-011 | Standards boundary for LTI/xAPI/SCORM/cmi5 | Accepted |
| ADR-012 | OIDC-first SSO with adapter boundary | Accepted |
| ADR-013 | Containerized production topology behind reverse proxy | Accepted |

## Rules
ADRs capture durable architectural choices, alternatives considered and consequences.
Implementation details that do not change a durable decision do not require a new ADR.
A superseding decision references the prior ADR and preserves it as historical record.

## Phase 0 status
All architecture decisions required by the Architecture and Technical Plan have an explicit record.