# Phase 1 — API Permission Matrix

As of: 2026-09-24

## Route-level permissions currently enforced

| Permission | Protected API operations |
|---|---|
| tenant.read | tenant settings read; integration registry read |
| tenant.manage | tenant settings update; role administration; permission catalog; role-permission administration; org-unit creation |
| users.read | org-unit read; role read; people/team read; role-skill read; manager development drill-down |
| users.manage | invitation; user lifecycle administration; org-unit creation in organization API; role assignment/removal; cohort membership |
| courses.manage | course create/update/module/lesson/publish; program/path/cohort administration; live session and attendance administration |
| assessments.manage | assessment creation/question management; attempt review; manual grade override |
| certificates.manage | certificate revocation |
| compliance.manage | compliance requirement/assignment administration; exceptions; evidence verification; administrative completion |
| skills.manage | skill creation; skill evidence; course-skill mapping; role-skill mapping |
| capabilities.read | capability framework/category read; capability detail and level read |
| capabilities.manage | capability/category creation/update; governed capability levels and relationships |
| strategic_objectives.read | strategic objective read |
| strategic_objectives.manage | strategic objective creation and capability mapping |
| competencies.read | competency framework, levels and capability relationships read |
| competencies.manage | competency creation and governed five-level definitions/mappings |
| role_requirements.read | governed role requirement read |
| role_requirements.manage | governed capability/competency/skill role requirements |
| reports.read | executive summary; CSV report exports; xAPI statement read |
| audit.read | audit log access |
| files.read | governed file listing and download |
| files.manage | governed file upload and scan-result administration |
| integrations.manage | integration configuration/disable; webhook administration |

## Intentionally authenticated self-service surfaces

The following are protected by the authenticated-user boundary and then constrain records to the current user/tenant rather than requiring an administrative permission:

- authenticated profile and logout
- current user's sessions
- current user's notifications
- own course enrollment/progress
- own assessment attempts/submission
- own compliance status/evidence/completion
- own certificates
- own development plan
- own skills
- global search
- learner-facing course/assessment/program views

## Negative-access evidence

The automated Phase 1 matrix test exercises 16 privileged operations as the Learner role. All returned HTTP 403.

The test also verifies that the permission catalog contains every permission key currently referenced by `require_permission(...)` in the route layer.

## Tenant-boundary evidence

Tenant-owned resource queries are expected to include the authenticated user's tenant identifier. Existing regression coverage verifies cross-tenant course detail access returns HTTP 404 and administrative target lookups reject missing/cross-tenant resource identifiers.

## Known Phase 1 completion gaps

This matrix is an implementation evidence artifact, not a declaration that Phase 1 is closed. Remaining work includes:

1. Expand negative-access coverage to resource-specific IDOR/BOLA cases across all tenant-owned families.
2. Verify privileged frontend actions against the same permission requirements.
3. Complete user/session lifecycle evidence.
4. Perform the formal Phase 1 exit review.
