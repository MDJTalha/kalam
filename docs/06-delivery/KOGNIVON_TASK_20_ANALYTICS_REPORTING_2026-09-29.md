# Kognivon Task 20 — Analytics and Reporting

Date: 2026-09-29
Status: Complete

## Audit scope

- Summary KPIs, learning trends, course performance, learning effectiveness, engagement, assessments, organization performance, compliance risk, and capability signals.
- Tenant and role visibility, pagination, search/sort filters, date windows, drill-down links, and CSV exports.
- Report library, saved reports, schedules, worker execution, and distinction between persisted metrics and future AI narratives.

## Findings and changes

- Active metrics are derived from persisted tenant-scoped enrollments, completions, assessments, certificates, compliance assignments, users, and capability records. The UI labels unavailable data instead of substituting simulated values.
- Existing report APIs provide bounded pagination, controlled sort fields, tenant filters, and evidence-model labels for derived measures.
- The Reports page advertised People and Enrollment CSV exports, but the endpoints were absent and the links bypassed the `/api/lms` authenticated proxy.
- Added tenant-scoped `/api/v1/reports/export/people` and `/api/v1/reports/export/enrollments` endpoints and corrected the web links to `/api/lms/reports/export/...`.

## Verification

- Report metrics and export contract test — passed.
- Web typecheck — passed.
- Python compilation — passed.
- Export data is filtered by the authenticated tenant and includes stable CSV headers.
