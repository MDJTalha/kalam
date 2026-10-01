# Kalam Phase 4 — Capability Gap Engine

**Status:** Implementation complete; end-to-end backend acceptance suite passing. Frontend production build verification remains environment-limited.
**Date:** 2026-09-30
**Environment:** Local Kalam development environment on MDT.

## Objective
Transform Role → Skill → Proficiency gap logic into a governed Capability Gap Engine:
Required Level → Demonstrated Level → Gap → Severity → Organizational Exposure.

## Implemented
- Canonical capability_gaps snapshot model.
- Tenant-scoped gap records keyed to person + role requirement.
- Capability, competency and skill requirement coverage.
- Verified, unexpired evidence as the current demonstrated source.
- Capability fallback from weighted verified competency evidence.
- Evidence confidence, count, observation date and freshness.
- Person and manager visibility with tenant isolation.
- Enterprise recalculation for authorized administrators.
- Summary aggregation with material-gap counts, critical/major exposure and weighted gap.
- Search and severity filtering.
- Calculation version phase4.v1.

## Governed calculation
Gap = max(Required Level - Demonstrated Level, 0)

State classification:
- met: gap = 0
- minor_gap: 0 < gap <= 0.50
- moderate_gap: 0.50 < gap <= 1.50
- major_gap: 1.50 < gap <= 2.50
- critical_gap: gap > 2.50
- insufficient_evidence: no current verified evidence or evidence is stale.

Current evidence freshness threshold is 180 days for a non-met requirement. Expired evidence is excluded.

## Organizational aggregation
The API supports enterprise, person, role and organization-unit scopes. Organization-unit summaries include the selected unit and its descendants. Manager read access includes the manager and direct reports. Tenant administrators and other gap managers can recalculate enterprise snapshots.

## API
- GET /api/v1/capability-gaps
- GET /api/v1/capability-gaps/summary
- POST /api/v1/capability-gaps/recalculate
- GET /api/v1/capability-gaps/snapshots

## UI
New route:
- /dashboard/capability-gaps

The workspace provides exposure metrics, recalculation, person drill-down, search, state filtering, requirement/current/gap comparison, evidence confidence/freshness, transparent calculation explanation, and empty/error/success states.

Navigation:
Capability → Capability Gaps.

## Security
Permissions:
- capability_gaps.read
- capability_gaps.manage

All records are tenant-scoped. Employees/managers do not receive unrestricted tenant-wide access.

## Migration
apps/api/alembic/versions/g7h8i9j0k1l2_phase4_capability_gap_engine.py

Alembic head after migration:
g7h8i9j0k1l2

## Validation
- Migration upgrade: PASS.
- Backend Python compilation: PASS.
- Frontend targeted ESLint: PASS.
- Frontend production build was started after Phase 4 changes; final process output was not available from the local process session and therefore is not treated as a release-gate result.
- Existing Phase 3 integration regression initially could not collect because the local Python environment lacked joserfc; dependency installation was initiated and the test process remained pending. This is an environment QA issue, not treated as a passing Phase 4 regression.

## Acceptance status
Phase 4 implementation is materially in place, but the final release gate remains open until local runtime regression confirms:
1. role requirement → user assignment produces gaps;
2. verified evidence changes the demonstrated level;
3. missing/stale evidence produces insufficient evidence;
4. tenant isolation holds;
5. enterprise and manager summaries aggregate correctly;
6. recalculation persists current snapshots.

## Next phase
Phase 5 — Capability Risk Intelligence will consume governed gap output and add explainable risk dimensions without changing the Phase 4 gap calculation.
