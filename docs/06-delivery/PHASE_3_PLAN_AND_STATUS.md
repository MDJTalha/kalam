# Kalam Phase 3 — Capability Assessment & Reassessment Engine

**Status:** Core Phase 3 implementation complete; QA gate green.  
**Date:** 2026-09-30  
**Environment:** Local Kalam development environment on MDT.  
**Scope:** Capability Assessment & Reassessment Engine from the Kalam 9.9 transformation plan.

## Objective

Connect assessment activity directly to governed capability measurement:

Baseline Assessment → Demonstrated Capability → Evidence → Development/Reassessment Due → Reassessment → New Demonstrated Level → Improvement Analysis.

Phase 3 preserves the existing assessment/quiz runtime and adds a governed capability measurement layer around it.

## Implemented

### Assessment instrument governance

Assessments now support governed configuration for:

- Self assessment
- Manager assessment
- Assessor assessment
- 360 assessment
- Knowledge test
- Practical evaluation
- Evidence review

Measurement methods are standardized to:

- Score-based
- Level-based
- Review-based
- 360 aggregate

Assessment controls also include validity days and reassessment interval.

### Capability measurement targets

A single assessment may be mapped to governed:

- Organizational capability
- Competency
- Skill

Each mapping has a required target level on the canonical 1–5 scale and a weight.

Target mappings lock after assessment attempts exist to protect historical measurement integrity.

### Assessment cycles

A persistent AssessmentCycle tracks:

- assessed person
- assessment instrument
- target
- required level
- baseline level
- current demonstrated level
- baseline attempt
- latest attempt
- lifecycle status
- reassessment due date
- optional development plan reference
- creator

Supported lifecycle states include baseline due/in progress, development in progress, reassessment due/in progress, and completed.

### Assessment outcomes and confidence

Each attempt can produce governed target-level outcomes with:

- demonstrated level
- score where applicable
- confidence
- evidence notes/reference
- assessor

Demonstrated levels support decimals to two places.

For score-based measurements, Kalam uses a governed continuous conversion from the 0–100 score domain to the 1–5 capability domain.

### Reviewer workflows

360 assessment cycles support explicit reviewer assignment:

- self
- manager
- assessor
- peer

Reviewer completion is tracked. A 360 cycle reaches its aggregated baseline/current state only when all assigned reviewers for that stage have completed.

### Evidence integration

Completed capability assessment outcomes generate verified CapabilityEvidence records with:

- assessment source provenance
- cycle and stage
- demonstrated level
- confidence
- assessor
- observation time
- expiry/validity
- audit verification metadata

This preserves the rule:

Learning activity ≠ capability evidence ≠ capability achievement.

### Reassessment

The engine now supports:

Baseline → mark due → reassessment → new demonstrated level.

Improvement is calculated explicitly as:

Current Level − Baseline Level

Example verified in automated QA:

2.60 → 3.70 = +1.10 improvement

### Authorization and tenant isolation

New permissions:

- capability_assessments.read
- capability_assessments.manage
- capability_assessments.execute
- reassessment.manage

Execution rules distinguish self, manager, assessor and 360 workflows.

Evidence access was also tightened so employees may view their own evidence without receiving unrestricted tenant-wide evidence access.

All Phase 3 records are tenant-scoped.

## API surface

Primary namespace:

/api/v1/capability-assessments

Implemented operations include:

- assessment target mapping
- assessment target removal with historical lock
- cycle creation
- cycle listing/detail
- reviewer assignment
- baseline/reassessment attempt creation
- outcome capture
- attempt completion
- reassessment transition
- attempt detail

Existing assessment administration was extended so assessment measurement mode, validity and reassessment controls can be configured through the product UI.

## UI

New tenant-facing route:

/dashboard/capability-assessments

The workspace provides:

- measurement instrument configuration
- target mapping
- baseline cycle creation
- cycle monitoring
- baseline execution
- reassessment execution
- demonstrated-level capture
- confidence capture
- improvement visibility
- empty/error/success states
- existing Kalam design-system components and navigation integration

Navigation entry:

Assessment & Credentials → Capability Assessments

## Data model changes

Added:

- assessment_targets
- assessment_cycles
- assessment_reviewer_assignments
- assessment_outcomes

Extended:

- assessments
- assessment_attempts

Updated:

- capability_evidence.demonstrated_level to governed decimal precision.

## Migrations

Phase 3 migration:

apps/api/alembic/versions/f6a7b8c9d0e1_phase3_capability_assessment_engine.py

Role-alignment migration:

apps/api/alembic/versions/f7b8c9d0e1f2_phase3_role_permission_alignment.py

The existing Alembic mergepoint remains intact. Final migration state:

f7b8c9d0e1f2 (head)

## QA evidence

### Phase 3 automated regression

apps/api/tests/test_phase3_capability_assessments.py

Verified:

1. Baseline → reassessment → +1.10 improvement.
2. 360 reviewer aggregation: 3.0 + 4.0 → 3.5.
3. Tenant isolation.

Result:

3 passed

### Phase 2 regression

apps/api/tests/test_phase2_evidence.py

Result:

3 passed

### Python compilation

Modified backend modules compiled successfully.

### Frontend lint

Focused lint across Phase 3 files:

0 errors / 0 warnings

### Production frontend build

Next.js production build:

Compiled successfully
TypeScript completed
84/84 static page generation completed
Exit code 0

The build output includes:

/dashboard/capability-assessments

### Local runtime smoke checks

GET /dashboard/capability-assessments

200

Unauthenticated:

GET /api/v1/capability-assessments/cycles

401

This confirms the API route is registered and protected in the active local runtime.

## Phase 3 acceptance status

The following Phase 3 business chain is now operational:

Assess Person
→ target governed measurement
→ demonstrated capability level
→ confidence
→ verified evidence
→ baseline/current state
→ reassessment due
→ reassessment
→ improvement calculation.

## Remaining work outside the Phase 3 core gate

The following belong to later phases or broader enterprise QA:

- deep integration of every legacy quiz/question workflow with every capability-cycle scenario
- coaching/mentoring interventions
- capability gap intelligence
- capability risk intelligence
- executive capability intelligence
- performance/outcome relationships
- capability AI advisor
- enterprise-scale performance optimization
- full cross-role desktop/tablet/mobile/accessibility audit for the new route
- final production release gate.

Phase 3 itself is not being used to declare Kalam 9.9 complete. Its purpose is to establish the governed assessment/reassessment measurement layer required by subsequent phases.

## Implementation files

Core backend:
- apps/api/app/db/models.py
- apps/api/app/api/routes/assessments.py
- apps/api/app/api/routes/evidence.py
- apps/api/app/api/routes/capability_assessments.py
- apps/api/app/main.py

Frontend:
- apps/web/src/components/capability-assessment-workspace.tsx
- apps/web/src/app/dashboard/capability-assessments/page.tsx
- apps/web/src/components/workspace-nav.tsx

QA:
- apps/api/tests/test_phase3_capability_assessments.py
