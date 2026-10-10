# Kalam 9.9 — Complete Workflow / Screen / Frontend–Backend Gap Audit
Date: 2026-10-04

## Continuation update — 2026-10-10

- Added a tenant-scoped, searchable, bounded course-page API with learner enrollment status and integrated the learner catalog's search, scope filters, and incremental loading. Added regression assertions for page-size bounds, search results, and invalid scope.
- Course Studio now uses server-side search and incremental pagination, including validated all/draft/review/published/archived filtering. Capability Framework, equivalency management, and live-session scheduling now use bounded course lookups and explicitly withhold mapping/scheduling controls when their 100-item catalog window would be incomplete.
- The new course catalog integration test was attempted but could not reach PostgreSQL: login fails with a connection-refused error. No DB-backed assertion or browser interaction is certified by this run.
- Environment diagnosis: Kalam is configured for PostgreSQL at `127.0.0.1:55434`; that port still refuses connections. A separate Windows PostgreSQL service listens at `5432`, but the configured `lms` credentials fail there, so it is not a safe substitute. Docker Desktop was started, but its engine did not become responsive during the check; no database or volume was changed.
- Skills & Development and Assessment Operations now preserve HTTP status/error details for all required datasets and withhold empty-looking profile/library states when a read fails.
- Added tenant-scoped `GET /api/v1/capability-domain/competencies/page` with bounded page size, escaped name/code search, total count, and batched proficiency-level hydration.
- Added integration assertions for competency search/pagination, included level data, and rejected over-limit page sizes. These database-backed assertions remain unexecuted because the local API/database runtime is unavailable.
- Evidence Admin, Capability Assessments, and Capability Framework now use the bounded competency endpoint. Screens explicitly withhold incomplete catalog workflows when more than 100 records exist rather than silently presenting partial target choices.
- The Assessment Builder detail screen now uses the same bounded competency page, reports HTTP/error details for required editor datasets, and withholds mapping controls if the catalog is larger than the loaded page.
- API Ruff passed for the changed route/tests; Web TypeScript typecheck and `git diff --check` passed. Local API and web ports remain unavailable, so browser/integration verification is still open.
- Other full competency-list consumers and unrelated enterprise datasets still require review/migration; this does not close the broader unbounded-data audit gate.

## Closure update — 2026-10-06

This audit is a living record; the findings below describe historical risks unless explicitly marked open. Source-level remediation completed since the original audit:

- Authentication handling now routes 401 to sign-in and 403 to the access-denied page.
- Capability Assessment now passes the selected `assessment` query value through to the client workspace. The workspace initializes settings and target state from that same assessment, avoiding a first-assessment/selected-target mismatch.
- Evidence Admin reads its initial evidence queue through a tenant-scoped paginated endpoint and no longer downloads the entire people directory; person capture/filter controls use the tenant-scoped searchable people page endpoint.
- Evidence page results include the associated learner's display name/email in the same tenant-scoped query, so large directories are not needed for queue labels.
- Compliance Admin's review queue now supports `limit`/`offset` pagination (default 50, hard maximum 100), returns `{total, items}`, and the screen has independent evidence-page navigation.
- Capability Assessment and Skills Admin person selectors now use a bounded first page and searchable person lookup instead of fetching all users.
- Administration, Capability Gaps, and Cohort management now use the same bounded searchable people lookup/directory; the last remaining dashboard `/api/v1/people` full-directory call was removed. The cohort-member action returns tenant-scoped display details so adding a person found beyond the first directory page remains correctly rendered.
- Capability Framework, Capability Assessments, and Administration now retain HTTP status/error details on critical server reads and withhold controls when required data cannot be loaded, instead of displaying zero/empty governance data or mislabeling backend failure as access denial. Support-context detection checks the explicit `active` flag.
- Added integration assertions for Compliance Admin evidence pagination, response shape, and maximum page-size enforcement. These assertions are committed as coverage but could not be run here because the current database/API runtime is unavailable.
- API Ruff passed for the changed evidence/compliance/program routes; mypy passed for those three routes; Web TypeScript type-check completed; `git diff --check` passed. Focused compliance integration tests stalled without output and were stopped. ESLint started but did not complete within the available run window. The API health endpoint refused connection on localhost, so no live browser/API verification was possible.

| Audit finding | Current disposition |
|---|---|
| 401 versus 403 handling | Closed in source; runtime role checks remain to certify. |
| Assessment initial selection | Closed in source; selected ID, settings, and target state now initialize together. |
| People Admin / Admin / Capability Gap / Cohort unbounded people fetch | Closed in dashboard source; searchable bounded lookup/directory adopted. |
| Evidence Admin unbounded evidence and people | Evidence and people are bounded; competency reference list remains unbounded. |
| Compliance Admin unbounded evidence-review queue | Closed in source with independent offset pagination; other compliance/library selectors still need bounds. |
| Skills/Capability Framework unbounded reference data | Open; people lookup is bounded, but skills, courses, competencies, objectives, roles, and governance reads still need a broader scale review. |
| Generic nullable API helper and error semantics | Open across many screens; only selected critical screens preserve HTTP status results. |
| End-to-end lifecycle, tenant matrix, browser, scale, deployment, AI | Open; requires working services, clean test data, role accounts, and/or production-authorized infrastructure. |

Still open: Capability Framework and several learning screens still load broad reference lists; Compliance course/requirement/reference reads are not all bounded; generic `apiJson()` callers still lose HTTP error distinctions; many workflows have not been run against a live disposable database; cross-tenant, authenticated browser, scale, backup/restore, production deployment, and real AI provider certification remain external/runtime gates. The unbounded `/people` API remains for compatibility, but dashboard pages have been migrated off it. Do not interpret source fixes or a type-check as end-to-end release certification.

## Executive conclusion
Kalam is broad and structurally mature: the dashboard route surface is implemented, the major capability-development domains exist, and substantial API/security/regression work is already complete. The remaining gaps are not primarily missing screens. They are contract, scale, workflow-state, authorization semantics, and operational-certification gaps.

## Confirmed residual gaps

## Remediation update — 2026-10-05

The following source-level items have now been addressed:

- `requireUser()` distinguishes unauthenticated (401 → sign-in) from authenticated but forbidden (403 → access-denied screen).
- Capability Assessments accepts a validated `assessment` query parameter and loads targets for that assessment, with a stable default when absent/invalid.
- Evidence verification/rejection recalculates the persisted capability-gap snapshot within the same transaction. The lifecycle test no longer performs a manual recalculate between decision and assertion.
- Evidence Admin starts from a bounded page and supports loading further evidence; the new API page is tenant-scoped, filterable, and capped at 100 rows.
- People Administration uses the existing tenant-scoped page/search endpoint, with pagination and person search rather than the unbounded directory endpoint.
- Organization renders a tenant-scoped aggregate hierarchy with direct active-member counts instead of loading the full people dataset.
- SaaS task/onboarding account selectors use the searchable bounded account lookup. Onboarding rows return their account names from a tenant-scoped batch lookup.
- Executive Analytics retains per-request HTTP status/error results and differentiates restricted metrics from missing/empty data.

Web TypeScript type-check, ESLint, Ruff, and mypy passed after these edits. API integration tests could not be completed in this environment: the focused evidence test stalled while executing against the local service stack and was stopped. The remaining items below are still open, especially Skills/Compliance data bounds, full browser/security/scale certification, and runtime-dependent lifecycle/regression checks. No production or live-provider certification is implied by these source fixes.

### P0 — Frontend/API error contract
The shared \`apiJson()\` helper converts every non-2xx response into \`null\`. This prevents callers from distinguishing 403, 404, 409, 422, 429 and 5xx unless they use \`apiJsonResult()\`.
Affected/at-risk current screens include Administration, Capability Assessments, Compliance Admin, Evidence Admin, Organization, Skills Admin, People Admin, SaaS Onboarding/Tasks and several learning/catalog screens.
Required: migrate business-critical reads/mutations to \`apiJsonResult()\` or a typed domain-state helper.

### P0 — Authentication vs authorization
\`requireUser()\` redirects both HTTP 401 and HTTP 403 to \`/login\`.
Impact: authenticated-but-forbidden users can be presented with a login flow instead of an authorization state.
Required: 401 -> login/session recovery; 403 -> permission-denied UI.

### P0 — Capability Assessment initial-state coupling
\`dashboard/capability-assessments/page.tsx\` selects \`assessments[0]\` and loads targets for that assessment server-side.
Impact: multi-assessment tenants can receive an initial target set tied to the first returned assessment.
Required: explicit selected-assessment state and verified target/cycle synchronization.

### P0 — Evidence/Admin enterprise data loading
Evidence Admin loads complete \`/people\`, \`/capability-domain/competencies\`, and \`/evidence\` arrays.
Impact: large tenants can create high memory, latency, serialization and render costs.
Required: paginated/searchable people, competency and evidence endpoints; bounded server queries.

### P1 — People Administration unbounded data
User Administration loads complete people, roles and units arrays.
Required: paginated people + bounded role/unit lookup endpoints; server-side search.

### P1 — Organization unbounded people
Organization loads the complete people dataset to render organizational structure.
Required: organization hierarchy endpoint with server-side aggregates/children and bounded person lookup.

### P1 — Capability Framework unbounded reference datasets
Skills Admin loads complete skills, roles, courses, people, objectives, capabilities, competencies and proficiency levels.
Required: bounded lookups plus server-side governance aggregates.

### P1 — Compliance Admin broad datasets
Compliance Admin still uses complete-list API calls for evidence/courses and several reference datasets.
Required: paginated evidence/courses and bounded selectors; retain aggregate summary endpoints.

### P1 — SaaS onboarding/task selectors
SaaS onboarding/tasks still request complete account lists even though major SaaS registers have already been paginated.
Required: searchable bounded account lookup; continue pagination of remaining finance/task selectors.

### P1 — Dashboard data truth model
Several dashboard/analytics screens still use \`apiJson()\` for independent metrics.
Impact: backend failure can become indistinguishable from an empty dataset.
Required: metric-level states such as AVAILABLE, EMPTY, FORBIDDEN, UNAVAILABLE, STALE.

### P1 — End-to-end lifecycle certification
The source path exists for Recommendation -> Intervention -> Execution -> Evidence -> Verification -> Capability Evidence -> Gap Recalculation -> Reassessment, but live execution has historically been blocked by local DB/runtime availability.
Required: one clean seeded tenant run with persisted before/after assertions at every transition.

### P1 — Cross-tenant security matrix
Course object-ID isolation is proven. Broader negative-object tests exist in several domains, but a complete matrix across People, Enrollment, Assessment Attempts, Evidence, Gaps, Development, Compliance, Certificates, Programs, Sessions, Reports, Files, Integrations and Webhooks remains a certification requirement.
Required: tenant A object IDs accessed by tenant B must be verified for every sensitive resource.

### P1 — Enterprise-scale runtime
A 10,001-user seed caused the local PostgreSQL container to exit with signal 9 / exit 137. This is classified as local capacity/infrastructure evidence, not an application assertion failure.
Required: repeat scale test in a resource-sized environment with measured p95 latency, DB memory/CPU, query count, payload size and concurrent-user behavior.

### P1 — Full regression closure
The latest isolated regression reached 161 passed tests, but certification records identify remaining external Ollama checks and environment/runtime dependencies. A final clean rerun after fixture corrections is still required.
Required: clean disposable DB, deterministic seed, full suite, archived result.

### P1 — Authenticated browser certification
Source/build/API gates are strong, but the release record explicitly leaves authenticated pixel-level browser/CDP signoff open.
Required: role-matrix browser run covering Platform Developer, Tenant Owner, Tenant Admin, L&D Admin, Manager, Instructor/Trainer and Learner at desktop/mobile widths.

### P1 — AI provider certification
AI governance and adapters are implemented fail-closed, with AI disabled by default. Live provider handshake remains intentionally unverified.
Required before production AI activation: provider connection test, model readiness, policy activation, secret-reference validation, grounded-answer tests, safety tests and tenant isolation.

## Workflow-specific gaps requiring proof
1. Strategy -> Objective -> Capability -> Competency -> Role -> Required Level: verify versioning/effective dates and downstream impact after changes.
2. Role -> People -> Assessment: verify assignment scope and manager/tenant boundaries.
3. Assessment -> Attempt -> Result: verify refresh, duplicate submit, expiry, attempt limits, authorization and evidence creation.
4. Evidence -> Verification: verify approve/reject/resubmit transitions and rejection reason persistence.
5. Verification -> Capability Evidence -> Gap: verify recalculation uses only governed/verified evidence.
6. Gap -> Recommendation -> Development: verify recommendation provenance, stale recommendation handling and idempotency.
7. Development -> Execution: verify plan/intervention/goal transitions and evidence requirements.
8. Reassessment -> Improvement: verify baseline/current/improvement/next-due values are derived from persisted records.
9. Capability -> Performance/Business Outcome: verify executive outcome metrics have authoritative formulas and do not imply causal impact without evidence.
10. Learning -> Compliance/Credentials: verify completion, expiry, recertification and evidence linkage.
11. SaaS Inquiry -> CRM -> Tenant -> Onboarding -> Renewal: source coverage is strong; production commercial policy, approved real data, deployment/worker observation and external billing/legal decisions remain open.

## Highest-risk screens
- /dashboard/capability-assessments
- /dashboard/evidence/admin
- /dashboard/people/admin
- /dashboard/organization
- /dashboard/skills/admin
- /dashboard/compliance/admin
- /dashboard/saas/onboarding
- /dashboard/saas/tasks
- /dashboard/analytics
- /dashboard

## Already substantially closed
- Dashboard route/domain completeness.
- Placeholder/TODO/mock-data cleanup in dashboard source.
- Shared Kalam branding direction.
- Next.js route generation/typecheck/build.
- API compile/Ruff/mypy gates.
- Major SaaS CRM pagination work.
- Course tenant object-ID isolation.
- Facilitator session authorization correction.
- Learning Catalog assignment/prerequisite/approval safeguards.
- AI fail-closed architecture and provider adapters.
- Public page HTTP/rendering baseline.
- Accessibility automated coverage has been substantially expanded.

## Definition of complete
Kalam should not be declared fully green until:
- every critical screen preserves HTTP status semantics;
- every sensitive workflow has a persisted end-to-end test;
- every tenant-sensitive object has negative cross-tenant coverage;
- no enterprise-critical screen loads unbounded datasets;
- the complete capability lifecycle executes on a disposable clean database;
- full API/web/browser regression passes;
- 10,000+ employee scale is measured in a representative environment;
- production migration/backup/restore/observability gates pass;
- real AI provider certification is completed before AI activation.
