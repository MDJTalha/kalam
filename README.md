# Kalam

Enterprise Workforce Capability Platform. The repository keeps the historical `CorpLMS` technical identifier for continuity.

## Project root
C:\Projects\Kalam

## Baseline status
Local acceptance evidence was refreshed on 2026-10-28: 191 API tests passed; frontend typecheck, lint, production build, authenticated browser lifecycle, accessibility smoke, dependency audit, and local Docker image runtime smoke passed. See `docs/06-delivery/KALAM_LOCAL_ACCEPTANCE_2026-10-28.md` for the evidence and remaining release gates. Hosted CI and staging/production acceptance remain open because the exact candidate has not been committed/pushed or deployed.

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
