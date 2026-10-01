# Kalam — Phase 2 Exit Evidence

Date: 2026-09-30
Status: CLOSED — GREEN

## Scope
Phase 2 establishes the governed evidence chain:

People → Evidence → Competency / Capability / Skill → Demonstrated Level → Confidence → Verification → Current Capability State.

## Delivered
- Tenant-scoped CapabilityEvidence model and API.
- Governed target types: capability, competency, skill.
- Canonical demonstrated level 1–5.
- Confidence 0–100.
- Evidence provenance, source/reference, observation and expiry dates.
- Pending → verified/rejected decision workflow.
- Immutable decisions after first decision.
- Exact provenance duplicate protection in API and PostgreSQL.
- Verified current-state summary excluding expired evidence.
- Assessment → Competency mapping with target level and weight.
- Assessment attempt → evidence generation.
- Assessment-derived evidence is idempotent and owned by the learner; assessor actor is retained.
- Tenant isolation and RBAC permissions: evidence.read, evidence.manage, evidence.verify.
- Evidence operations UI, Assessment Studio mapping UI, and person-profile evidence summary.

## Validation
- Phase 2 dedicated regression: 3 passed.
- Ruff: PASS.
- mypy: PASS — 60 source files.
- Alembic current: f0a1b2c3d4e5 (mergepoint).
- Web ESLint: PASS — exit code 0.
- Web production build: PASS — 83 routes.

## Regression repair discovered during gate
The broader regression exposed schema drift: the database lacked assessment governance columns already required by the current Assessment model. The existing Phase 3 assessment-engine migration branch (f6a7b8c9d0e1) contained those columns but was not applied. A mergepoint migration (f0a1b2c3d4e5) was reconciled and the database was upgraded to the merged head. This restored schema/model alignment without duplicating the existing migration operations.

## Release decision
Phase 2 acceptance criteria are GREEN and Phase 2 is CLOSED.

The platform-wide regression suite contains unrelated long-running/legacy coverage that is tracked separately from the Phase 2 evidence-engine acceptance gate. No hosted CI/repository promotion is claimed by this local exit evidence.
