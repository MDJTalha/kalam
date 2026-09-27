# Corporate LMS — Domain Model

Version: 0.1
Status: Phase 0 baseline
Date: 2026-09-24

## 1. Domain ownership
- Identity: tenants, users, sessions, invitations, password reset tokens.
- Authorization: roles, permissions, user-role and role-permission mappings.
- Organization: org units and reporting relationships.
- Learning: courses, modules, lessons, enrollments, lesson progress.
- Assessment: assessments, questions, attempts and grading overrides.
- Credentials: certificates and verification lifecycle.
- Compliance: requirements, assignments, evidence and exceptions.
- Capability: skills, user skills, role requirements and course mappings.
- Development: development plans and goals.
- Delivery: programs, cohorts, learning paths, sessions and attendance.
- Communications: notifications.
- Platform: files, audit logs, integrations and webhooks.
- Interoperability: xAPI learning statements.

## 2. Core relationships
Tenant -> User -> Enrollment -> Course -> Module -> Lesson -> LessonProgress.
Course -> Assessment -> Question -> AssessmentAttempt -> Certificate.
Tenant -> ComplianceRequirement -> ComplianceAssignment -> Evidence/Exception.
User -> Role -> RoleSkillRequirement -> Skill; Course -> CourseSkill -> Skill.
Program -> ProgramCourse -> Course; Program -> Cohort -> CohortMember -> User.
LearningPath -> LearningPathItem -> Course; LiveSession -> AttendanceRecord -> User.

## 3. Invariants
- Tenant-owned business records are tenant-scoped and server-authorized.
- Cross-tenant reads and writes fail closed.
- Primary business identifiers use UUIDs; public verification codes are distinct credentials.
- Foreign keys and unique constraints protect referential integrity and idempotency.
- Completion, grading, certification and compliance evidence remain persisted-record sources of truth.
- Audit records are append-oriented evidence, not mutable business state.

## 4. Planned extensions
Categories/tags, certificate templates, competencies, bulk assignment, waitlists, recurrence/escalation and richer applicability rules remain roadmap work and must extend this model through controlled changes.