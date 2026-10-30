# Kalam Phase 5 — Capability Risk Intelligence

**Status:** Implementation complete; local build/compile/migration validation passed.
**Date:** 2026-09-30
**Environment:** Local Kalam development environment on MDT.

## Objective
Upgrade capability risk from basic risk-band logic into a governed organizational risk engine consuming Phase 4 capability-gap output.

## Implemented
- Canonical capability_risks snapshot model.
- Tenant-scoped risk records, one current snapshot per capability.
- Governed risk dimensions covering gap severity, criticality, strategic importance, people exposure, critical roles, evidence confidence, assessment age, development inactivity, certification expiry, concentration, compliance impact and trend.
- Deterministic normalization to 0–100 for every dimension.
- Weighted composite risk score with documented weights.
- Risk bands: Low, Moderate, High, Critical.
- Explainability payload: risk → reason → evidence/exposure → impact → recommended action.
- Capability drill-down to affected people, roles, required/current levels, gap severity and evidence confidence/freshness.
- Manager visibility remains limited to the manager and direct reports.
- Tenant administrators and risk managers can recalculate enterprise snapshots.
## Governed calculation
Risk Score = weighted sum of normalized risk dimensions (0–100).

Weights:
- Gap severity 20%
- Criticality 15%
- Strategic importance 15%
- People exposure 10%
- Critical-role exposure 10%
- Evidence confidence 8%
- Assessment age 6%
- Development inactivity 5%
- Certification expiry 3%
- Concentration 5%
- Compliance impact 2%
- Trend 1%

Bands:
- Low: 0–24.99
- Moderate: 25–49.99
- High: 50–74.99
- Critical: 75–100

The score is an exposure indicator, not an unexplained business verdict. Every displayed risk exposes its component dimensions and recommended review action.

## API
- GET /api/v1/capability-risks
- GET /api/v1/capability-risks/{capability_id}
- POST /api/v1/capability-risks/recalculate

## UI
New route:
- /dashboard/capability-risk

The workspace provides risk-level metrics, search/filtering, recalculation, capability drill-down, dimension-level explanation and action guidance.

Navigation:
Capability → Capability Risk.
## Security
Permissions:
- capability_risk.read
- capability_risk.manage

All risk calculations are tenant-scoped. Manager reads are restricted to the manager and direct reports. Recalculation requires manage permission and is audited.

## Migration
apps/api/alembic/versions/p5a6b7c8d9e0_phase5_capability_risk.py

Alembic upgrade to head: PASS.

## Validation
- Backend Python compilation: PASS.
- Phase 5 API/model import: PASS.
- Alembic migration upgrade: PASS.
- Frontend TypeScript check: PASS.
- Frontend ESLint: PASS.

## Acceptance status
Phase 5 implementation is complete. The next release-gate QA should verify seeded runtime data across:
1. high/critical capability exposure;
2. tenant isolation;
3. manager scoping;
4. evidence confidence and stale evidence effects;
5. development inactivity;
6. certification-expiry signal;
7. strategic capability weighting;
8. risk recalculation persistence;
9. explainability and drill-down consistency.

## Next phase
Phase 5A — Development Intelligence consumes governed capability gaps/risk and connects them to development interventions rather than course matching alone. Phase 5B — Coaching, Mentoring & Experience executes accepted non-learning interventions. Canonical Phase 6 remains Reporting, Analytics & Integrations.
