# Corporate LMS — Requirements Baseline

Version: 0.1
Status: Synthesized implementation baseline

## 1. Requirement hierarchy

Business objective
  -> Capability
  -> Module
  -> User story
  -> Acceptance criteria
  -> Test case
  -> Evidence

No requirement should exist only in chat.

## 2. Must-have release capabilities

### Identity
- Login
- Logout
- Password reset
- Email verification where enabled
- Session expiry
- Account lock/rate limiting
- User profile
- Role assignment
- Tenant assignment

### Organization
- Company/tenant
- Business unit
- Department
- Location
- Team
- Reporting line

### Learning catalog
- Course creation
- Course editing
- Draft/publish
- Categories
- Tags
- Prerequisites
- Course owners
- Visibility

### Learning delivery
- Enrollment
- Course player
- Content completion
- Progress
- Attendance
- Completion
- Due dates
- Reminders

### Assessment
- Question bank
- Assessment builder
- Attempts
- Scoring
- Pass rules
- Feedback
- Manual grade override with audit

### Certification
- Certificate templates
- Issue
- Expiry
- Revocation
- Verification
- QR code
- Evidence history

### Compliance
- Requirement definitions
- Target audience
- Assignment
- Due date
- Recurrence
- Completion status
- Expiry
- Exception
- Escalation
- Reporting

### Skills
- Skill library
- Competencies
- Proficiency levels
- Role requirements
- Learner skill profile
- Gap visibility
- Course-to-skill mapping

### Analytics
- Enrollment
- Progress
- Completion
- Assessment
- Compliance
- Certificate
- Skills
- Learner engagement
- Manager/team
- Executive

## 3. Secondary capabilities

- Cohorts
- Learning paths
- Programs
- Workshops
- Instructor management
- Calendar
- Waitlists
- Bulk import/export
- Saved reports
- Scheduled reports
- Notification templates
- Knowledge base
- External learners
- Client organizations

## 4. Future/controlled capabilities

- AI tutor
- AI recommendation engine
- Generative course authoring
- Semantic search
- Skills inference
- Advanced workforce capability analytics
- LRS
- xAPI event processing
- LTI Advantage certification
- Advanced mobile offline learning
- Marketplace

## 5. Core user journeys

### Learner
Login -> dashboard -> assigned learning -> course -> lesson -> assessment -> completion -> certificate -> skill evidence.

### Manager
Login -> team dashboard -> overdue/at-risk learners -> learner detail -> assign/recommend learning -> monitor completion.

### L&D admin
Create course -> publish -> create program -> define audience -> assign/enroll -> monitor -> report -> improve.

### Compliance admin
Create requirement -> define applicability -> assign -> monitor -> escalate -> export evidence.

### Instructor
View sessions -> roster -> attendance -> facilitate -> grade -> feedback -> completion.

### Executive
Dashboard -> learning KPIs -> compliance risk -> capability trends -> drill-down within authorized scope.

## 6. Acceptance principles

A feature fails acceptance when:
- unauthorized data is visible;
- state changes are not persisted;
- refresh loses critical state;
- duplicate requests cause duplicate business records;
- required validation can be bypassed;
- audit evidence is missing where required;
- destructive actions lack safeguards;
- error states leave the UI misleading;
- test evidence is absent.

## 7. Data-quality requirements

- Foreign keys must be valid.
- Required identifiers must not be null.
- Status transitions must be explicit.
- Timestamps must be stored consistently.
- Duplicate business records must be prevented with appropriate constraints.
- Imports must produce row-level validation results.
- Bulk operations must be traceable.
- Soft-delete use must be deliberate and documented.

## 8. Permission model

Minimum roles:
- Platform Super Admin
- Tenant Admin
- HR/L&D Admin
- Compliance Admin
- Instructor
- Manager
- Learner
- Report Viewer
- Auditor
- Support Operator

Roles may be combined or extended per tenant.

Every endpoint and every protected data query must enforce authorization server-side.

## 9. UI requirements

Global:
- Responsive
- Keyboard usable
- Accessible labels
- Consistent navigation
- Global search
- Notifications
- Profile
- Context breadcrumbs
- Loading states
- Empty states
- Error states
- Confirmation dialogs
- Toast feedback

Data surfaces:
- Pagination
- Sorting
- Filtering
- Saved views where useful
- Bulk actions
- CSV export where authorized

## 10. API requirements

All APIs:
- OpenAPI documented
- Authenticated where required
- Authorized
- Validated
- Version-aware
- Consistent error envelope
- Pagination conventions
- Correlation/request ID
- Rate-limit policy
- Idempotency for critical commands where required

## 11. File/content requirements

- Virus/malware scanning boundary
- MIME validation
- File size limits
- Safe filenames
- Access-controlled downloads
- Signed/private object URLs where appropriate
- Metadata
- Ownership
- Audit records
- Retention rules

## 12. Notifications

Notification types:
- assignment
- due soon
- overdue
- completion
- certificate issued
- certificate expiring
- manager escalation
- assessment result
- system/security event

Notification delivery must be observable and retryable.

## 13. Reporting principles

Reports must distinguish:
- actual persisted records
- derived metrics
- estimates
- AI-generated narrative

AI-generated narrative must never silently become an authoritative business metric.

## 14. Integration principles

No integration is considered complete because code exists.

A live integration requires:
- credentials/configuration
- successful handshake
- real request/response evidence
- failure handling
- retry strategy
- audit/logging
- data mapping
- privacy review
- test environment strategy

## 15. AI requirements

AI must never:
- bypass permissions
- expose one tenant's content to another
- fabricate completion, compliance or certification evidence
- silently make disciplinary/employment decisions
- present generated content as verified fact without provenance

AI features must support:
- feature-level enable/disable
- tenant policy
- prompt/version tracking
- model configuration
- retrieval boundary
- output safety checks
- human review where consequential

## 16. Traceability IDs

Requirement IDs will follow:
AUTH-xxx
TEN-xxx
ORG-xxx
USER-xxx
RBAC-xxx
CAT-xxx
CONT-xxx
COURSE-xxx
ENR-xxx
ASSESS-xxx
CERT-xxx
COMP-xxx
SKILL-xxx
DEV-xxx
NOTIF-xxx
REPORT-xxx
INT-xxx
AI-xxx
SEC-xxx
A11Y-xxx
OPS-xxx

Each ID will ultimately map to code, tests and release evidence.
