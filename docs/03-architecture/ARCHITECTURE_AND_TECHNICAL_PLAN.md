# Corporate LMS — Architecture and Technical Plan

Version: 0.1

## 1. Architecture decision

Initial architecture: modular monolith with explicit domain modules.

The system must be organized so modules have:
- clear ownership
- explicit service interfaces
- bounded data access
- testable business rules
- documented dependencies

A future extraction into services must be possible without designing day-one infrastructure around microservices.

## 2. Proposed repository structure

corp-lms/
  apps/
    web/
    api/
    worker/
  packages/
    ui/
    config/
    schemas/
    api-client/
  database/
    migrations/
    seeds/
    fixtures/
  infra/
    docker/
    reverse-proxy/
    scripts/
    monitoring/
  tests/
    unit/
    integration/
    e2e/
    security/
    accessibility/
    performance/
  docs/
    01-governance/
    02-product/
    03-architecture/
    04-security-compliance/
    05-quality/
    06-delivery/
    07-decisions/

## 3. Web application

Recommended:
- Next.js
- TypeScript
- Strongly typed API client
- Accessible component primitives
- Form validation
- Route-level authorization handling
- Server-side data access only through controlled API/service boundaries

Primary areas:
- /auth
- /learner
- /manager
- /instructor
- /admin
- /compliance
- /reports
- /settings

## 4. API application

Recommended:
- FastAPI
- Pydantic
- SQLAlchemy or equivalent typed ORM/data layer
- Alembic migration framework
- Structured exception handling
- OpenAPI
## 12. Authorization

Authorization checks belong in the backend.

Policy examples:
- learner can see own records
- manager can see authorized direct/indirect team scope
- instructor can manage assigned course/session scope
- L&D admin can manage tenant learning configuration
- auditor is read-only
- platform admin has cross-tenant capability only through explicit privileged workflows

## 13. Audit

Audit event fields:
- id
- tenant_id
- actor_id
- action
- entity_type
- entity_id
- timestamp
- request_id
- before/after summary where appropriate
- IP/device context where lawful and useful

Avoid storing unnecessary sensitive payloads in audit logs.

## 14. Observability

Minimum:
- structured application logs
- request ID
- user/tenant context where safe
- error classification
- metrics
- health endpoint
- readiness endpoint
- worker/job metrics
- database migration visibility

Production extension:
- OpenTelemetry-ready traces
- centralized logging
- alerting
- error tracking

## 15. Caching

Cache only data where stale values are acceptable.

Never rely on cache as the source of truth for:
- completion
- grades
- certification
- compliance evidence
- authorization

Invalidate or version caches deliberately.

## 16. File architecture

Store file metadata in PostgreSQL and file bytes in object storage.

Content lifecycle:
upload
-> validate
-> scan
-> store
-> metadata
-> access policy
-> download/stream
-> retention/deletion

Private files must not be public by URL accident.

## 17. Security baseline

Use OWASP ASVS as a verification-oriented security baseline.

Security controls include:
- secure headers
- input validation
- output encoding
- injection resistance
- authentication controls
- authorization controls
- secrets handling
- dependency scanning
- upload validation
- rate limiting
- audit
- secure error messages
- backup/recovery

## 18. Accessibility baseline

Target WCAG 2.2 AA.

Accessibility is tested in:
- authentication
- learner dashboard
- course player
- assessments
- tables
- modals
- forms
- admin workflows

Keyboard navigation and visible focus are release criteria.

## 19. Performance architecture

Initial targets will be evidence-driven, but the design assumes:
- server-side pagination
- bounded queries
- indexed filters
- async heavy jobs
- lazy loading of large content
- CDN/object storage for static assets in production
- query monitoring

No artificial “sub-second everywhere” promise will be made before measuring realistic workloads.

## 20. AI architecture

AI gateway:
Application
 -> AI policy/permission
 -> retrieval/context boundary
 -> model provider
 -> safety/output validation
 -> response
 -> logging/evaluation

The gateway must know:
- tenant
- user
- feature
- allowed sources
- model
- prompt version
- policy
- output status

For retrieval:
- tenant-scoped knowledge
- document permissions
- citations/source references
- chunk versioning
- deletion propagation

## 21. Configuration and secrets

Never commit:
- API keys
- production passwords
- private certificates
- OAuth secrets
- database passwords

Use .env.example for names only.

Production secrets must be injected through deployment secret management.

## 22. Environment strategy

Development
QA
UAT
Production

Each environment has separate:
- database
- secrets
- storage
- integration credentials
- notification targets

Demo data must never be mistaken for production customer data.

## 23. Backup and recovery

Define:
- database backup schedule
- object storage backup/versioning where applicable
- restore procedure
- restore verification
- retention
- recovery time objective
- recovery point objective

A backup that has never been restored is not release evidence.

## 24. Deployment strategy

Production-compatible:
- web container
- API container
- worker container
- PostgreSQL
- Redis-compatible service
- object storage
- reverse proxy
- monitoring

Local development may run selected dependencies natively to reduce hardware overhead.

## 25. ADRs required

Create Architecture Decision Records for:
- frontend stack
- backend stack
- database/ORM
- authentication model
- multi-tenancy
- background jobs
- object storage
- API versioning
- event model
- AI provider abstraction
- content standards
- SSO strategy
- deployment topology

## 26. Architecture exit criteria

Architecture is accepted when:
- module boundaries are documented
- data ownership is documented
- tenant isolation is demonstrated
- auth/authz flows are documented
- critical sequence diagrams exist
- migration strategy exists
- test strategy exists
- deployment topology exists
- security assumptions are explicit
