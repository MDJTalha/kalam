# Corporate LMS — Delivery Roadmap

Version: 0.1

## Phase 0 — Baseline and repository foundation
Outputs:
- Requirements baseline
- Architecture baseline
- Security baseline
- QA strategy
- Traceability matrix
- ADR index
- Git repository
- Monorepo skeleton
- Environment templates
- CI baseline

Exit evidence:
- repository starts
- documentation is internally consistent
- CI runs baseline checks

## Phase 1 — Identity, tenancy and core platform
Build:
- tenant lifecycle
- organization hierarchy
- user management
- authentication
- password reset
- RBAC
- permission checks
- sessions
- audit events
- navigation
- settings
- database migrations

Test:
- authentication
- authorization
- tenant isolation
- negative access tests
- migration safety

## Phase 2 — Course and learner core
Build:
- categories
- courses
- modules
- lessons
- content
- publishing
- enrollment
- learner dashboard
- course player
- progress
- completion
- due dates
- notifications

Test:
- complete learner journey
- progress persistence
- duplicate enrollment protection
- content authorization

## Phase 3 — Assessments and credentials
Build:
- question bank
- assessment builder
- attempts
- scoring
- manual grading
- feedback
- certificates
- QR verification
- expiry
- revocation

Test:
- grading correctness
- attempt rules
- certificate integrity
- verification security

## Phase 4 — Corporate L&D
Build:
- programs
- curricula
- learning paths
- cohorts
- manager dashboards
- instructor workflows
- attendance
- bulk assignment
- calendar
- waitlists

## Phase 5 — Compliance and skills
Build:
- compliance requirements
- assignment rules
- recurrence
- exceptions
- escalation
- audit reports
- skills
- competencies
- role requirements
- learner skill profile
- development plans

## Phase 6 — Reporting, analytics and integrations
Build:
- executive dashboard
- L&D dashboard
- manager dashboard
- compliance dashboard
- reports
- exports
- REST API
- webhooks
- integration adapters
- SSO/OIDC boundary
- LTI/xAPI boundaries

## Phase 7 — Governed AI
Build:
- AI gateway
- content assistance
- summaries
- recommendations
- learner Q&A over authorized content
- skill-gap explanations
- AI evaluation and audit

Rules:
- no permission bypass
- no unsupported authoritative claims
- no hidden consequential employment decisions

## Phase 8 — Commercial readiness
Build:
- production deployment
- monitoring
- backups
- restore verification
- disaster recovery runbook
- security verification
- accessibility verification
- performance testing
- customer documentation
- release procedures
- legal document review

## Change control

New scope must record:
- requirement ID
- business reason
- impacted modules
- security impact
- testing impact
- architecture impact
- release target

## Delivery discipline

A phase advances only on evidence:
code + database + tests + permissions + documentation.
