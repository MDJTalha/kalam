# Kalam Remaining QA/QC Execution Plan — 2026-10-11

Status: **ACTIVE — RELEASE ACCEPTANCE OPEN**
Scope: user-approved synthesized requirements baseline (must-have and secondary capabilities, plus applicable security, tenant, accessibility, data, operations and integration controls).
Safety: preserve the dirty worktree; never test-write to `kalam-prod` or `kalam-tunnel` data; do not delete/stop containers or volumes; no deployment, commit, credential reset, or real external submission.

## Execution method

For each gate: identify the exact candidate and isolated environment, map requirements to a journey/API/data owner, run tests, fix in-scope defects with regression coverage, retest, and record evidence. A passing health endpoint, source file, unit test, or old container image does not prove a workflow. Mark each item **PASS**, **FAIL**, **BLOCKED**, or **NOT IN SCOPE** with its evidence and owner. Re-score only from the acceptance matrix; do not infer feature completion from route/test counts.

## Ordered gates

| Gate | Priority | Work and pass criteria | Dependencies / owner | Current status |
|---|---:|---|---|---|
| 0. Candidate + test environment | P0 | Freeze an identifiable source snapshot without discarding changes; obtain sufficient memory; build web/API/worker candidate; record digests; provide browser and disposable PostgreSQL/Redis/ClamAV environment; verify no live DB is targeted. | Local environment / developer operator | **BLOCKED:** dirty worktree; ~0.62 GB free RAM, no browser session; no approved disposable DB endpoint. No process/container will be killed or repurposed to create capacity. |
| 1. API and schema regression | P0 | Full API suite, migration upgrade/rollback policy check against disposable DB, isolation/authorization tests, migration head check, storage/scanner integration, worker tests. Zero unresolved test failures; persisted test results are read back. | Isolated test services / backend QA | **PARTIAL:** 21 DB-independent tests pass; Ruff and offline migration SQL pass. Full DB suite and migration application remain open. |
| 2. Identity and access | P0 | Browser: organization discovery/race states, login cookie + `/auth/me`, reload, protected route, role-specific landing, logout/re-entry, password recovery invalid/expired/used/success. Cover learner, manager, L&D, compliance, instructor, executive, tenant owner/admin and platform developer; direct unauthorized URL/API and tenant-isolation denials. | Candidate browser + seeded test identities / identity and backend owners | **OPEN:** source fixes and static checks pass; no exact-candidate browser or DB authorization run. |
| 3. Core learning and capability workflows | P0/P1 | Learner enrollment → course player/progress → assessment → certificate; L&D author/publish → program/path/session → assign/monitor/report; manager team scope/action; compliance requirement/evidence/status/escalation; capability gap → intervention → evidence → reassessment. Verify database persistence/readback, permissions, duplicates, error/retry states. | Candidate + disposable seeded DB / product and module owners | **OPEN:** several API tests/source features exist; full workflows not verified end-to-end. |
| 4. Public conversion and SaaS operations | P1 | Pricing/catalog states; contact sales/guided evaluation required validation; submit/suppress duplicate; 4xx/429/5xx/offline recovery; attribution/consent; confirm CRM inquiry record and authorized operator readback. Verify no false success when inbox/provider is disabled. Check trial redirect and all public links/claims. | Candidate + isolated CRM/inbox configuration / commercial product owner | **OPEN:** form/source inspection only; no submission or record readback. No real prospect data will be submitted. |
| 5. Shared UX, responsive, accessibility | P1 | Browser routes at 320/360/375/390/768/1024/1280/1440+; 200% zoom; keyboard focus/order/Escape and focus return; menus, dialogs, tables and forms; automated axe plus manual screen-reader spot checks. Inspect actual screenshots and console/network errors. | Browser + built candidate / frontend and accessibility QA | **OPEN:** static TS/lint pass; no browser available. Do not claim WCAG certification from automated scan alone. |
| 6. Files, integrations, AI and operations | P1 | Private S3-compatible upload/download/delete + malware scan + tenant isolation; real provider handshake for each claimed integration; AI provider gating, grounding/citations, permissions and failure behavior; TLS/headers, security tests, performance, monitoring, backup/off-host restore and rollback evidence. Clearly label provider-dependent functions. | Provider credentials, test tenant/bucket, target infrastructure / platform and operations owners | **OPEN:** S3 adapter/config unit tests use fakes; no configured private provider or off-host restore evidence. External provider, production, and backup gates require authorized services/credentials. |
| 7. Release acceptance | P0 | Re-run all checks on the exact candidate; zero P0/P1 failures; route/workflow matrix complete; no secrets/artifacts; limitations accepted by product owner; record artifact digests and final release disposition. | All prior gates / release owner | **OPEN — cannot endorse release.** |

## Work completed before this plan

- Frontend TypeScript and ESLint pass; public navigation keyboard/touch behavior and login tenant-discovery states have source-level fixes.
- Focused database-independent API suites: **21 passed**; Ruff passes; Alembic has one head and pending migration offline SQL generates.
- Production Compose config and running Nginx syntax check pass.
- Read-only `kalam-prod` gateway root/live/ready routes return HTTP 200. `kalam-prod` and `kalam-tunnel` core containers report healthy; the separate `docker` project has unhealthy API/ClamAV containers.
- Detailed current evidence is in `KALAM_QA_QC_AUDIT_2026-10-11.md`. Running image evidence is not candidate-source evidence.

## Immediate next actions

1. Obtain a supported browser session and a disposable test DB/services target, or restore enough local capacity under the operator's control. Do not kill processes or use persistent Kalam databases as substitutes.
2. Build the exact worktree candidate and record its artifact IDs; run route and visual checks against that candidate.
3. Run API tests and migration tests against the disposable database, then browser identity journeys.
4. Continue module workflows in the order above, fixing confirmed source defects and adding regression tests.
5. Update the gate table and QA/QC report after each completed gate; release remains **NOT READY** until Gate 7 passes.

## Release disposition

**NOT READY.** The environment dependencies at Gate 0 currently prevent meaningful end-to-end confirmation. No external credentials, customer submissions, production writes, or destructive runtime actions are authorized by this plan.
