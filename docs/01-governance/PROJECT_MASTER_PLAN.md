# Kalam — Project Master Plan

Version: 0.2
Status: Baseline for implementation; product naming reconciled 2026-09-28
Date: 2026-09-24
Product: Kalam — Enterprise Workforce Capability Platform
Repository identifier: CorpLMS (retained for technical continuity)
Project Director: Muhammad Talha
Implementation root: C:\Projects\CorpLMS

## 1. Executive mandate

Build Kalam as a serious enterprise workforce capability and learning platform, not a course catalogue or front-end prototype.

The platform must support organizations that need to plan, deliver, administer, measure and govern employee learning, skills, readiness and workforce capability at scale.

The product will be designed as a SaaS-capable, multi-tenant platform with optional single-tenant deployment.

The system must serve:
- Enterprise HR and L&D
- Department and business-unit managers
- Training administrators
- Instructors and facilitators
- Employees/learners
- Compliance and audit teams
- Executives
- External/client learners where enabled

## 2. Source baseline and evidence

This plan consolidates the LMS-specific material recoverable from the project context and stored project files, including the earlier Corporate LMS planning discussion, LMS-oriented product goals, architecture direction, phased-development expectations, and related AIVON/Learnify context.

The file index did not expose the exact titled “Corporate LMS Overview” conversation or a uniquely named white-paper/blueprint artifact as a discrete retrievable file in this session. Therefore this plan deliberately uses a controlled synthesized baseline and identifies verification gates rather than inventing unseen wording.

Retrieved LMS-related context confirms the requirement for production-level architecture, complete backend/database/authentication/permissions, dashboards, deployment, testing and security rather than static UI-only pages.

## 3. Product vision

Create a modern corporate learning operating system that connects:
Learning -> People -> Skills -> Compliance -> Performance evidence -> Analytics -> Decisions.

Core product promise:
- Put every learner, course, program and learning record in one governed system.
- Make mandatory training measurable and audit-ready.
- Make employee development visible to employees, managers and HR.
- Connect learning to skills and organizational capability.
- Provide executive visibility without exposing unnecessary personal data.
- Provide APIs and standards-based integrations instead of proprietary lock-in.

## 4. Product pillars

1. Learning management
2. Content and curriculum management
3. Enrollment and learning delivery
4. Assessments and examinations
5. Certifications and credential verification
6. Compliance and mandatory training
7. Skills and competency management
8. Employee development and learning paths
9. Instructor/facilitator management
10. HR/L&D administration
11. Reporting and analytics
12. Communications and notifications
13. Integrations and interoperability
14. AI-assisted learning operations
15. Governance, security and audit

## 5. Target personas

### Enterprise administrators
Organization-wide configuration, policies, structures, integrations, audit and reporting.

### HR/L&D administrators
Programs, curricula, audiences, enrollments, campaigns, compliance, skills and reports.

### Department managers
Team learning visibility, assignments, approvals, completion, skill development and manager dashboards.

### Instructors
Facilitation, attendance, grading, feedback, content support and learner progress.

### Learners
Discovery, assigned learning, self-enrollment, progress, assessments, certificates, skills and development plans.

### Compliance/audit users
Mandatory training status, evidence, expirations, exceptions, audit trails and exports.

### Executives
High-level workforce learning, capability, risk, completion and trend indicators.

### System/platform operators
Tenant lifecycle, platform operations, security, monitoring and support.

## 6. Functional scope

### A. Identity and organization
- Tenant management
- Organizations
- Business units
- Departments
- Locations
- Teams
- Job roles
- Employee profiles
- Manager relationships
- User lifecycle
- Invitations
- SSO-ready architecture
- MFA-ready architecture
- Session and device management

### B. Authorization
- Role-based access control
- Permission matrix
- Tenant scope
- Organization scope
- Department/team scope
- Course/program scope
- Manager/team scope
- Explicit deny/allow rules
- Server-side policy enforcement
- Audit logging of privileged actions

### C. Course and content management
- Courses
- Modules
- Lessons
- Learning objectives
- Content items
- Documents
- Video
- Audio
- Links
- Embedded resources
- Versioning
- Draft/review/publish lifecycle
- Prerequisites
- Course owners
- Categories/tags
- Content visibility rules

### D. Curriculum/program management
- Learning programs
- Curricula
- Learning paths
- Cohorts
- Batches
- Sessions
- Workshops
- Programs by audience
- Required/elective components
- Sequential learning
- Prerequisite rules
- Equivalencies

### E. Enrollment and delivery
- Self enrollment
- Manager enrollment
- Admin enrollment
- Bulk enrollment
- Rules-based enrollment
- Approval workflows
- Waitlists
- Attendance
- Progress tracking
- Completion rules
- Due dates
- Recurrence
- Calendar
- Reminders
- Overdue handling

### F. Assessments
- Quizzes
- Question banks
- Question types
- Randomization
- Attempts
- Time limits
- Pass thresholds
- Grading
- Manual grading
- Automated grading
- Feedback
- Retakes
- Exam integrity controls
- Assessment analytics

### G. Certificates and credentials
- Certificate templates
- Certificate issuance
- Expiry
- Renewal
- Revocation
- QR verification
- Public verification endpoint
- Verification audit
- Credential metadata
- Downloadable evidence

### H. Compliance learning
- Mandatory training
- Regulatory/organizational requirement catalog
- Assignments
- Due dates
- Recurrence
- Expiry
- Exceptions
- Evidence
- Completion dashboards
- Escalation rules
- Audit reports
- Department/location/job-role applicability

### I. Skills and competencies
- Skill taxonomy
- Competencies
- Proficiency levels
- Skill profiles
- Target skills
- Assessment evidence
- Development gaps
- Learning-to-skill mapping
- Role skill requirements
- Skills reporting

### J. Development
- Individual development plans
- Development goals
- Recommended learning
- Manager feedback
- Development milestones
- Evidence and notes

### K. Instructor/facilitator
- Instructor profiles
- Expertise
- Availability
- Assigned courses
- Sessions
- Attendance
- Grading
- Feedback
- Facilitator analytics

### L. Communication
- Email notifications
- In-app notifications
- Digest notifications
- Assignment notices
- Due reminders
- Completion notices
- Expiry alerts
- Manager escalations
- Template management
- Delivery logging

### M. Search and discovery
- Global search
- Course search
- Filters
- Categories
- Skill search
- Saved views
- Search-ready architecture
- Future semantic search

### N. Analytics
- Executive dashboard
- HR/L&D dashboard
- Manager dashboard
- Learner dashboard
- Compliance dashboard
- Course analytics
- Assessment analytics
- Skill analytics
- Engagement analytics
- Completion trends
- At-risk learners
- Exportable reports

### O. Integrations
- REST API
- Webhooks
- CSV import/export
- HRIS integration boundary
- SSO identity-provider boundary
- Calendar integration boundary
- Email provider boundary
- Standards-based learning integration
- Future LTI 1.3
- xAPI 2.0/LRS-compatible event model
- Optional SCORM/cmi5 adapter strategy

### P. AI capabilities
AI is an assistive layer, not an uncontrolled decision-maker.

Planned AI capabilities:
- Course description drafting
- Learning objective suggestions
- Quiz/question drafting
- Learning recommendations
- Skill-gap explanations
- Content summarization
- Learner Q&A over approved content
- Manager/HR summaries
- Compliance risk explanations
- Search assistance
- Content metadata generation

Every AI capability requires:
- Explicit feature ownership
- Source/context tracking
- Prompt/version tracking
- Model/version tracking
- Output logging where appropriate
- Human review for consequential actions
- Privacy controls
- Tenant isolation
- Disable/override controls

## 7. Non-functional requirements

### Performance
- Fast primary learner experience
- Pagination for large datasets
- Async processing for heavy jobs
- Indexed database queries
- Background jobs for notifications/imports/reports
- Performance budgets defined before release

### Reliability
- Structured error handling
- Idempotent critical operations
- Retry with backoff
- Health checks
- Safe migrations
- Backups
- Restore procedures
- Job visibility

### Security
- Secure authentication
- Strong password hashing
- MFA-ready
- Session controls
- CSRF protection where applicable
- Input validation
- Output encoding
- Rate limiting
- Secrets management
- Audit logging
- Least privilege
- Tenant isolation
- Secure file handling
- Encryption in transit
- Encryption at rest where supported

### Accessibility
Target WCAG 2.2 AA for the learner and administrative web interfaces.

WCAG 2.2 is a W3C Recommendation, and Level AA includes all Level A and AA success criteria. See the external standards record in the architecture/compliance document.

### Observability
- Structured logs
- Metrics
- Traces where practical
- Correlation/request IDs
- Error reporting
- Audit events
- Job status
- Health/readiness endpoints

## 8. Product architecture strategy

Use a modular monolith for the initial production platform.

Do not begin with microservices.

Why:
- Smaller operational footprint
- Easier local development
- Lower infrastructure cost
- Strong transactional consistency
- Easier testing
- Clear module boundaries can later become services if scale requires it

Architecture layers:
1. Web application
2. API/application layer
3. Domain modules
4. Data/repository layer
5. Background jobs/events
6. Integration adapters
7. AI services
8. Observability/security
9. Infrastructure

## 9. Proposed technology baseline

Frontend:
- Next.js
- TypeScript
- Accessible component system
- Responsive/PWA-ready interface
- Server and client rendering used deliberately

Backend:
- Python
- FastAPI
- Pydantic-based validation
- Modular service/domain structure
- OpenAPI-first API contracts

Database:
- PostgreSQL

Caching/job infrastructure:
- Redis-compatible service
- Background worker architecture

File/object storage:
- S3-compatible abstraction

API:
- REST/OpenAPI
- Webhooks
- Versioned external API strategy

Testing:
- Unit tests
- API integration tests
- Database tests
- Browser/E2E tests
- Security tests
- Accessibility checks
- Performance checks

Deployment:
- Local Windows development first
- Docker-compatible production setup
- Reverse proxy
- Managed PostgreSQL option
- Object storage
- CI/CD

## 10. Data architecture principles

Every tenant-owned business entity should carry an unambiguous tenant boundary.

Common fields:
- id
- tenant_id
- created_at
- updated_at
- created_by
- updated_by
- deleted_at where soft delete is justified

Additional principles:
- UUIDs for public identifiers
- Unique constraints defined explicitly
- Foreign keys enforced
- Indexes designed from access patterns
- Audit history separated from mutable business data where needed
- Sensitive fields classified

## 11. High-level domain modules

Identity
Organization
Users
Roles
Permissions
HR/people
Learning catalog
Content
Programs
Cohorts
Enrollments
Learning activity
Assessments
Question banks
Certificates
Compliance
Skills
Competencies
Development plans
Instructors
Attendance
Notifications
Reports
Analytics
Files
Audit
Integrations
Webhooks
AI
System settings

## 12. Delivery phases

### Phase 0 — Requirements and architecture baseline
Deliver:
- Master plan
- Requirements baseline
- Domain model
- Architecture
- Security baseline
- Test strategy
- ADRs
- Initial repo skeleton

Exit gate:
Requirements are traceable to modules and test cases.

### Phase 1 — Foundation
Deliver:
- Repository
- Environment configuration
- Authentication
- User management
- Tenant model
- Organization hierarchy
- RBAC
- Audit framework
- Core UI shell
- Navigation
- Settings baseline
- Database migration framework

Exit gate:
A user can authenticate, receive correct permissions, and access only authorized tenant data.

### Phase 2 — Learning core
Deliver:
- Catalog
- Courses
- Modules/lessons
- Content
- Programs
- Enrollments
- Learner dashboard
- Course player
- Progress
- Completion rules

Exit gate:
End-to-end learning journey works with persistent records.

### Phase 3 — Assessment and certification
Deliver:
- Question banks
- Assessments
- Attempts
- Grading
- Certificates
- QR verification
- Expiry/renewal
- Evidence

Exit gate:
Assess -> pass -> certificate -> verification is fully traceable.

### Phase 4 — Corporate L&D and compliance
Deliver:
- Mandatory learning
- Assignment rules
- Recurrence
- Exceptions
- Compliance dashboards
- Manager/team learning
- Skills
- Competencies
- Development plans

Exit gate:
HR can define requirements and produce audit-ready evidence.

### Phase 5 — Analytics and integrations
Deliver:
- Executive analytics
- L&D analytics
- Manager analytics
- Exports
- API
- Webhooks
- HRIS/SSO integration framework
- Standards adapters

Exit gate:
Data is consistent, permission-aware, exportable and integration-ready.

### Phase 6 — Reporting, analytics and integrations
Deliver:
- Executive and operational analytics
- Reports and exports
- Saved and scheduled reports
- REST/OpenAPI integration boundary
- Webhooks and integration registry
- External-provider adapter boundaries
- Server-side filtering, sorting and pagination for high-volume datasets

Exit gate:
Reporting is tenant-scoped, permission-aware, scalable and auditable; integration contracts are locally evidenced.

### Phase 7 — Governed AI
Deliver:
- Governed AI gateway
- Authorized retrieval and citations
- Content assistance
- Learner/course summaries
- Learning recommendations
- Skill-gap explanations
- Provider/model governance
- Evaluation, human review and audit controls
- Token/cost budgets, telemetry and deterministic fallback

Exit gate:
AI is assistive and traceable, cannot bypass permissions or tenant boundaries, and does not create unsupported authoritative or consequential employment decisions.

### Phase 8 — Production hardening and commercialization
Deliver:
- Production deployment
- Security verification
- Accessibility verification
- Performance testing
- Backup/restore and disaster recovery
- Monitoring and alerting
- Deployment/rollback automation
- Customer documentation
- Legal/privacy/commercial review
- Release checklist and evidence packet

Exit gate:
All applicable target-environment and independent release criteria pass; open Critical/High defects = 0.

## 13. Quality gates

No phase is complete because screens exist.

Every phase must pass:
- Functional tests
- API tests
- Permission tests
- Database integrity tests
- Negative/security tests
- Accessibility review
- Error-state review
- Audit-log review
- Regression tests
- Documentation update

Critical severity defects block promotion.

## 14. Definition of Done

A feature is done only when:
1. Requirement documented.
2. Data model implemented.
3. API implemented.
4. Authorization implemented.
5. UI implemented.
6. Validation implemented.
7. Audit behavior implemented where required.
8. Tests implemented.
9. Error/empty/loading states handled.
10. Documentation updated.
11. No known critical security issue.
12. Regression suite passes.

## 15. Release philosophy

Development releases:
- Internal development
- QA
- UAT
- Pilot
- Production

No “100% complete” claim is permitted without evidence from test results and release gates.

## 16. Project controls

The project will maintain:
- Requirements Traceability Matrix
- Architecture Decision Records
- Change log
- Risk register
- Security register
- Test evidence
- Release checklist
- Defect register
- Environment matrix

## 17. Initial risks

1. Scope expansion before the learning core is stable.
2. Excessive frontend-first development.
3. Weak multi-tenant isolation.
4. Overcomplicated microservice architecture.
5. AI being added before learning data is trustworthy.
6. Missing auditability.
7. Integration assumptions without real credentials.
8. Poor migration discipline.
9. Accessibility treated as cosmetic.
10. Seed/demo data mistaken for production capability.

## 18. Immediate execution sequence

1. Freeze this baseline.
2. Build requirements traceability matrix.
3. Define complete domain model.
4. Create repository skeleton.
5. Create database migration foundation.
6. Build authentication and tenancy.
7. Build RBAC and audit.
8. Build learning catalog and content.
9. Build learner journey.
10. Build assessment/certification.
11. Build compliance/skills.
12. Build reporting/analytics and integrations.
13. Add governed AI with evaluation and audit controls.
14. Execute production-hardening, QA and release certification.

## 19. Source standards considered

- W3C WCAG 2.2
- 1EdTech LTI 1.3 / LTI Advantage
- xAPI / IEEE 9274.1.1-aligned event strategy
- OWASP ASVS
- NIST AI RMF Generative AI Profile

External references are documented separately so version changes can be reviewed without silently changing the product baseline.

## 20. Approval status

This document is the implementation starting point.

It is not permission to skip requirements verification. New requirements must be recorded as controlled changes.

Next artifact:
docs/02-product/REQUIREMENTS_BASELINE.md
