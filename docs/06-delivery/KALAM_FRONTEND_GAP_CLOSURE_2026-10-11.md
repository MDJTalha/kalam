# Kalam Frontend Gap Closure — 2026-10-11

Status: **IN PROGRESS — NOT RELEASE READY**
Candidate branch/HEAD: `main` / `fc872e50b2007cc0f365d7acba0d18dfd928ac7a`
Worktree: dirty before this increment; all pre-existing changes were preserved. This report describes the current uncommitted source, not a deployed build.

## Scope and disposition

The attached frontend brief was treated as implementation context under the user's existing instruction to fix gaps that can be safely resolved and report the rest. The approved synthesized requirements baseline remains the scope control. This is a focused increment, not completion or endorsement of the full brief.

| Finding | Severity | Surface | Remediation | Evidence / status |
|---|---|---|---|---|
| Public mega-menu could only be opened by pointer hover; touch and keyboard users had no reliable disclosure control. | P1 | `apps/web/src/components/public-header.tsx`, `public-chrome.module.css` | Replaced menu labels with accessible disclosure buttons; added click/tap toggling, focus opening, focus-exit closing, Escape-to-close/return-focus, `aria-expanded`/`aria-controls`, persistent hidden menu regions, and visible keyboard focus. Existing hover behavior remains. | TypeScript passed; targeted ESLint passed; full frontend ESLint passed. Browser interaction/screenshot regression is not yet run. |
| Password sign-in could be disabled for a tenant without any discovered SSO provider, while the UI instructed the user to use an SSO action that was not rendered. | P1 | `apps/web/src/app/login/login-client.tsx` | The method-unavailable state now distinguishes configured SSO from no available sign-in method and directs the latter to the tenant administrator. | TypeScript and targeted ESLint passed. Browser state regression is not yet run. |
| Organization discovery could display the previous tenant's name/SSO options while a new ID was being checked; an in-flight response could also race with the changed input. | P1 | `apps/web/src/app/login/login-client.tsx` | Tenant-specific details are cleared synchronously on input change; a request-generation guard ignores stale results; checking, unrecognized, and unavailable states are separately announced. | TypeScript and targeted ESLint passed. Browser/deferred-response regression is not yet run. |

## Verification

- `npm run typecheck` in `apps/web`: **PASS** (exit 0).
- `npx eslint src/components/public-header.tsx` in `apps/web`: **PASS** (exit 0).
- `npx eslint src/app/login/login-client.tsx` in `apps/web`: **PASS** (exit 0).
- Repeated `npm run typecheck` and targeted login ESLint after the organization-discovery change: **PASS** (exit 0).
- `npm run lint` in `apps/web`: **PASS** (exit 0).
- `git diff --check` on the two menu files: **PASS** (only Git line-ending warnings).
- Source review confirms the contact-sales form orders organization size before country, requires work email, validates country selection, sends through the same-origin marketing endpoint, and surfaces the endpoint's disabled/unavailable state as an error rather than success. This was a code inspection, not an end-to-end form submission test.
- No production build or browser test was run for this exact source. Host free memory was approximately 1 GB after checks; the running Docker web image is not this uncommitted candidate. No old-image smoke is counted as candidate-build evidence.
- Computer-use browser inventory returned no available apps, browsers, or tabs, so exact-candidate UI interaction could not be run in this session.
- Runtime smoke already recorded in `KALAM_READINESS_STEP1_BASELINE_2026-10-11.md` and the 18/18 security smoke in `KALAM_PHASE1_PRODUCT_CAPABILITY_AUDIT_2026-10-11.md` apply to the running image only.

## Open release gates

- **Frontend candidate/build provenance:** build and route/browser smoke against this exact source, then identify the resulting artifact/image digest.
- **Authentication and role journeys:** login, browser session cookie, `/auth/me`, role landing, logout, password lifecycle, and six baseline role journeys are not verified end-to-end for this exact candidate.
- **Public conversion:** sales/evaluation form success, duplicate submission, validation, network/429/5xx recovery, attribution, and persisted CRM inquiry readback require isolated end-to-end tests.
- **Coverage:** the route inventory is broad, but every major module/control, responsive breakpoint, tenant/role boundary, and workflow has not been fully reviewed or browser-tested.
- **Accessibility:** the menu remediation has semantic/keyboard source support, but keyboard/browser and screen-reader validation are outstanding. No whole-app WCAG 2.2 AA claim is made.
- **Backend/infrastructure/product dependencies:** private object storage and recovery; live provider/SSO/payment/email configuration; external TLS/monitoring; and real integration certification remain separately open as recorded in the product-capability audit.

## Release disposition

**NOT READY.** This increment closes one concrete public-navigation accessibility gap at source level and passes static frontend checks. The exact candidate has not passed a production build, browser journey suite, full role/tenant matrix, or release acceptance. No completion percentage or 100% endorsement is assigned.
