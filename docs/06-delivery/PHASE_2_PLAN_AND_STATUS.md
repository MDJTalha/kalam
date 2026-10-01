# Kalam — Phase 2: Evidence Engine

Status: CLOSED — PHASE 2 GREEN
Start date: 2026-09-30

## Objective
Establish the canonical evidence layer connecting people to demonstrated capability: People → Evidence → Competency / Capability / Skill → Demonstrated Level → Confidence → Verification → Current Capability State.

## Implemented
- Tenant-scoped evidence ownership.
- Person/learner target.
- Target type: capability, competency, skill.
- Demonstrated level: governed 1–5 scale.
- Confidence: 0–100.
- Evidence type and source type.
- Source reference.
- Observation and expiry dates.
- Assessor.
- Notes and metadata.
- Verification/rejection state.
- Verification actor/time and rejection reason.
- Audit events.
- Tenant isolation and RBAC.

## Assessment integration
- Assessment → Competency mapping.
- Target competency level and weight.
- Mapping review/update/removal.
- Assessment attempt → capability evidence generation.
- Evidence retains assessment attempt provenance.
- Verified current evidence summary per person.

## API
New route family: /api/v1/evidence
Core operations: list evidence; create evidence; verify/reject evidence; evidence summary by person; map assessments to competencies; list assessment competency mappings; remove assessment competency mappings; generate evidence from a completed assessment attempt.

## Governance
New permissions: evidence.read, evidence.manage, evidence.verify.
Assigned to: Tenant Owner; Tenant Administrator; Platform Developer.

## Database
Migrations: dd44ee55ff66_phase2_evidence_engine.py; ee55ff66aa77_phase2_evidence_idempotency.py; f0a1b2c3d4e5_reconcile_assessment_governance_columns.py
Current Alembic head: f0a1b2c3d4e5 (mergepoint).

## Engineering validation so far
- Ruff: PASS
- mypy: PASS
- Migration upgrade: PASS
- Application import: PASS
- Evidence route module loaded successfully.
- Web targeted ESLint: PASS.
- Web production build: PASS after resolving the existing standalone-server build lock and fixing the new evidence component type error.

## UI delivered
- Capability Evidence operations workspace with evidence capture, filtering and verification actions.
- Assessment Studio competency mapping with target level and weight.
- Person profile current verified evidence summary.
- Navigation entry under Risk & Evidence.

## Governance hardening
- Exact source provenance duplicate guard is enforced in both the API path and PostgreSQL uniqueness constraint.
- Assessment-derived evidence is idempotent by tenant + learner + target + assessment-attempt provenance.
- Assessment attempts are tenant-scoped and may be converted by an authorized evidence manager for the attempt owner; the evidence remains owned by the learner and the actor is retained as assessor.
- Assessment scores map deterministically to the canonical five-level scale: <50 → 1, 50–69 → 2, 70–79 → 3, 80–89 → 4, 90–100 → 5.
- Evidence decisions are immutable after the first decision; replacement evidence is required for a changed finding.
- Verified current summary excludes expired evidence and uses the governed 1–5 level scale.

## Validation completed
- Dedicated Phase 2 regression: **3 passed**.
- Evidence lifecycle, provenance duplicate protection, immutable decisions and expired-evidence filtering: PASS.
- Assessment competency mapping, learner assessment attempt, assessment-derived evidence generation and idempotent regeneration: PASS.
- Cross-tenant assessment/evidence access controls: PASS.
- Ruff: PASS.
- mypy: PASS.
- Alembic upgrade to new evidence idempotency revision: PASS.
- Web production build: PASS — 83 routes generated.

## Phase 2 release gate — GREEN
- Dedicated Phase 2 regression: **3 passed**.
- Ruff: **PASS**.
- mypy: **PASS — 60 source files**.
- Alembic: **PASS — f0a1b2c3d4e5 mergepoint is current**.
- Web ESLint: **PASS — exit code 0**.
- Web production build: **PASS — 83 routes generated**.
- Assessment schema drift found during regression was repaired by applying the existing Phase 3 assessment-engine migration branch and reconciling Alembic heads; this was required to align the production database schema with the current assessment model.
- The broad platform regression remains a separate platform-wide gate because the suite contains unrelated long-running/legacy tests; it is not used to invalidate the Phase 2-specific acceptance gate.

Phase 2 is **CLOSED — GREEN** on its defined evidence-engine acceptance criteria.


