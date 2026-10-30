# Kalam Frontend Remediation — 2026-10-29

## Status

**In progress — not a complete frontend acceptance sign-off.** This increment remediates several concrete data-state, permission-feedback, and accessibility issues and establishes a generated inventory for the 92 discovered `page.tsx` routes.

## Repository safety

- Local repository: `C:\Projects\Kalam`
- Branch: `work/kalam-local-changes-2026-10-26`
- Existing staged, unstaged, and untracked work was preserved; no reset, clean, commit, push, merge, or deployment was performed.
- The generated route inventory is a static source scan. It is not a claim that every route has been manually audited or functionally verified.

## Implemented in this increment

1. **Manager dashboard:** distinguishes unavailable team follow-up data from an empty follow-up queue, preventing an API outage from appearing to mean that no action is needed.
2. **Integration console:** removed unsupported "registry operational" language; labels the view as a request snapshot; distinguishes webhook management from integration registry health; bases the connected-card styling on the `connected` state; clarifies what the connected count means; uses a neutral blue status marker rather than implying health.
3. **Tenant administration:** distinguishes HTTP 403 access denial from API/network failures; hides support actions when their backing service cannot be verified and shows a non-sensitive service-unavailable state.
4. **Reports:** distinguishes an explicit permission denial from service/network errors instead of describing every failure as a generic reporting outage.
5. **Learning paths:** distinguishes access denial and service failure from an empty published-path list.
6. **Webhooks:** no longer displays an empty registry when the API failed; reports access denial, network failure, or HTTP failure and hides creation controls when registry data cannot be verified.
7. **Notifications:** distinguishes permission denial and service/network errors from a valid empty notification feed.
8. **Accessibility:** corrected low-contrast small text on login, password-recovery, password-reset, and pricing-notice surfaces based on current axe findings.
9. **Catalog, audit, and compliance:** distinguish access denial and service failures from valid empty results; compliance indicators retain unavailable markers for failed data sources while still showing any successfully loaded section.
10. **Notification actions:** mark-read and mark-all failures now surface actionable error feedback; duplicate in-flight updates are prevented; notification action links are restricted to safe internal paths.
11. **Reusable resource forms:** required custom lookup fields now receive client-side validation; lookup request failures and empty results are distinguished, stale search results are cleared, selected record labels are retained, and lookup errors are associated with the input for assistive technology.
12. **Integration console:** test results are interpreted using the returned success flag, failed checks are reflected in the local status, connection tests are blocked until edited configuration is saved, numeric configuration fields use numeric input, and editing a verified configuration resets it to a configurable state.

## Current-turn verification

| Check | Result | Scope / limitation |
|---|---|---|
| `npm run typecheck` | PASS | Current frontend working tree at the time of the final run |
| `npm run lint` | PASS | `apps/web/src` |
| `npm run build` | PASS | Next.js 16.4.3; 88 static pages generated; route manifest emitted |
| Backend integration unit subset | PASS | `tests/test_integrations.py` selection: 14 passed, 2 deselected; one Starlette/httpx deprecation warning. This is not the full API suite. |
| Frontend unit/component tests | NOT CONFIGURED | `apps/web/package.json` has no test script and `src` has no `*.test.*` or `*.spec.*` files; no new test framework dependency was added in this increment. |
| `git diff --check` | PASS | Targeted files; line-ending conversion warnings only |
| `git diff --cached --check` | PASS | Targeted files; no whitespace errors |
| Public browser smoke | PASS | Six public/authentication routes; 12 desktop/mobile viewport checks; no missing headings, page-error markers, or horizontal overflow |
| axe-core public accessibility scan | PASS after correction | Six public routes; zero detected WCAG 2/2.1/2.2 A/AA and best-practice violations in the rerun; automated checks are not a full manual WCAG audit |
| Unauthenticated route guard smoke | PASS | 12 protected dashboard routes redirected to login/denied/unavailable without rendering protected page content; this does not verify authenticated role access. |
| Authenticated role browser scan | BLOCKED | An initial attempt against the currently running local API returned 401 for the supplied isolated-QA fixture accounts. No authenticated role journey or role-based accessibility pass is claimed for the exact current source. |

## Inventory artifact

- `qa/frontend-route-inventory-20261029.csv` — 92 route files, with source path, literal API endpoint references, permission string references, and simple control counts.
- `qa/frontend-role-screen-matrix-20261029.csv` — an initial audience hypothesis for each route. All rows are explicitly marked unverified until checked against backend authorization and authenticated browser journeys.
- Static scan totals: 71 route files contain literal API endpoint references; 41 contain literal permission checks. These counts are heuristic and do not prove that an endpoint exists, that a form persists data, or that a permission is enforced by the backend.
- `qa/public-browser-qa-20261029.json` — public browser viewport and axe evidence.
- `qa/unauthenticated-route-guard-20261029.json` — 12 protected-route redirect checks.
- `qa/authenticated-browser-accessibility-20261029-ui-remediation.json` — records the blocked authenticated attempt; it is not passing acceptance evidence.

## Remaining required work

1. Complete manual review of all 92 routes and their shared client components, including route-to-role and route-to-API mapping.
2. Verify Developer/Platform Operator, Tenant Administrator, Manager, Learner, and additional roles with a correctly isolated authenticated browser environment and role-appropriate test fixtures.
3. Exercise all important forms, mutation actions, file operations, filters, sorting, pagination, exports, dialogs, and error-recovery paths against the actual API contracts.
4. Verify end-to-end workflows including course publication/enrollment/completion, assessment submission, compliance evidence/review, development intervention/reassessment, tenant administration, and integration/webhook operations.
5. Complete authenticated responsive and accessibility testing, including manual keyboard/focus checks and representative mobile/desktop routes.
6. Run the full backend/API regression suite and establish a supported frontend component-test strategy; the current frontend workspace has no configured unit-test runner.
7. Keep production release approval separate from local frontend checks; hosted CI, staging deployment, integrated deployment smoke, security analysis, and operational/recovery acceptance remain independent gates.

## Release disposition

**Partially verified.** Local frontend typecheck, lint, and production build pass. Six public routes passed desktop/mobile smoke, and the rerun of automated accessibility checks reported zero violations. The full role-based screen inventory, authenticated workflows, and all-route acceptance remain open. No commit, push, or deployment occurred.
