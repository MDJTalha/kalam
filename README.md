# Kalam

Enterprise Workforce Capability Platform. The repository keeps the historical `CorpLMS` technical identifier for continuity.

## Project root
C:\Projects\CorpLMS

## Baseline status
Phase 0 current-tree local foundation gate passed on 2026-09-28. Hosted CI evidence requires a configured Git remote.

## Primary objective
Build a production-grade, multi-tenant enterprise workforce capability platform covering learning administration, learners, instructors, HR/L&D workflows, content, assessments, certifications, skills, compliance, readiness, analytics, integrations, commercial SaaS operations and governed AI capabilities.

## Working principles
- No static/demo-only implementation.
- Backend, database, authorization, auditability and testing are first-class.
- Tenant isolation is mandatory.
- Every business action must have server-side authorization.
- Demo seed data must be clearly identified.
- External integrations must be explicitly configured and verifiable.
- AI outputs must be traceable, governed and optional.
- Security, accessibility, observability and recovery are release requirements.

See docs/ for the governing project plan and architecture.

## Foundation validation

Run the complete repeatable Phase 0 local gate from the repository root:

`npm run validate:phase0`

The command validates required baseline artifacts, environment consistency, Docker dependency readiness, migration head, API Ruff/mypy/pytest, web TypeScript/ESLint/build and reports repository/remote state.
