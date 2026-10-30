# Kalam Phase 5A — Development Intelligence

**Status:** Implementation complete; Phase 5A v2 enhancement, stale-state reconciliation, and focused regression QA passed locally.
**Date:** 2026-10-01
**Environment:** Local Kalam development environment on MDT.

## Objective
Upgrade the existing Development Engine from the established Skill Gap → Published Course pathway into governed intervention intelligence. Phase 5A consumes Phase 5 core capability gaps and capability risk and expands recommendations across multiple development modalities.

## Implemented
- Added persistent development_recommendations model.
- Tenant-scoped recommendation records with provenance, score, priority, timeframe and rationale.
- Preserved the existing capability/skill → published-course pathway.
- Added intervention intelligence across learning, coaching, mentoring, experiential/stretch assignments, and evidence-building.
- Recommendation scoring considers gap magnitude, required vs demonstrated level, severity, criticality, capability risk, evidence confidence/freshness, assessment history, prior course/enrollment history, prior development-plan interventions, role context, published-course skill fit, configured development preferences, and urgency/timeframe.
- Learning recommendations now support published courses, learning paths, programs, and scheduled sessions; acceptance enrolls the relevant published course set without treating completion as capability achievement.
- Capability, competency, and skill gaps are all eligible recommendation targets; competency gaps resolve through governed capability-to-skill mappings where available.
- Added explainable recommendation rationale.
- Added accept workflow: learning recommendation creates a published-course enrollment; other modalities create/update an active development-plan goal.
- Added audit event when an intervention is accepted.
- Added recommendation versioning (phase6.v2).

## API
- GET /api/v1/development/recommendations
- GET /api/v1/development/recommendations?user_id={id}
- GET /api/v1/development/recommendations?intervention_type={type}
- POST /api/v1/development/recommendations/{recommendation_id}/accept

## UI
The existing Development Plans workspace now contains Intervention Intelligence — Recommended development actions.
Users can see recommendations, modality, priority, rationale and timeframe; accept an intervention; refresh recommendations; and continue using development plans, milestones and feedback.

## Security
New permissions:
- development.recommendations.read
- development.recommendations.manage

Recommendations are tenant-scoped. Users can access their own recommendations. Manager access is constrained by existing user-read and manager scope; enterprise management permission can administer recommendation acceptance.

## Migration
apps/api/alembic/versions/q6r7s8t9u0v1_phase6_development_intelligence.py

Alembic upgrade to head: PASS.

## Validation
- Backend Python compilation: PASS after stale-state reconciliation.
- Backend Ruff check for the Phase 6 route: PASS.
- Alembic head remains a single merged head (`h5i6j7k8l9m0`), including Phase 6 migration: PASS.
- Phase 6 API contract/security tests: 4 passed.
- Runtime recommendation generation against local data: 184 recommendations generated across 46 material gaps, covering coaching, mentoring, experiential and evidence-building modalities without errors.
- Persisted recommendation reconciliation: PASS; recommended records no longer generated from the current governed gap/source state are marked `superseded`, preventing stale actionable recommendations from surviving gap closure.
- Frontend TypeScript check: PASS.
- Full frontend lint remains a tooling exception: workspace ESLint execution stalls without diagnostics; no lint error has been established.
- Local catalog data currently contains 200 published courses but 0 course-skill mappings, so learning recommendations are correctly absent rather than fabricated. The engine supports course/path/program/session recommendations when governed mappings exist.

## Acceptance focus
Runtime QA should verify: Skill Gap → Published Course continuity; course-fit scoring; prior-learning de-prioritization; critical/high-risk urgency; generation of all five intervention modalities; correct enrollment on learning acceptance; correct plan-goal creation for non-learning interventions; manager/user scope; recommendation provenance/rationale; and no recommendations when no governed capability gaps exist.

## Next phase
Phase 5B — Coaching, Mentoring & Experience can build the operational execution layer around the multi-modal intervention engine: actual coach/mentor relationships, sessions, experiential assignments, progress reviews and evidence capture.
