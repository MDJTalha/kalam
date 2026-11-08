# Kalam 9.9 Brand Surface Audit Manifest

**Branch:** `kalam/brand-9-9-surface-audit`
**Purpose:** reproducible repository-level inventory, identity/terminology scan and verification traceability.

## Required inventory

The audit must enumerate:

- all `apps/web/src/app/**/page.tsx` routes
- route-level and inherited loading/error/not-found/global-error states
- all reusable files under `apps/web/src/components/`
- all CSS/design-token files
- public brand and product assets
- metadata and structured-data declarations
- transactional/public communications
- customer-facing and governance documentation
- shared layouts and application source files

For each discovered file record:

`surface_id | route/file | audience | type | states | brand status | terminology status | accessibility status | claim status | test status | evidence | owner`

Each discovered file must appear exactly once in the inventory. A file may carry multiple pipe-separated surface types.

## Reproducing the inventory

Run from the repository root:

```powershell
node qa/brand-surface-inventory.mjs
# Start the web app first, then smoke-test all inventoried routes:
node qa/brand-route-smoke.mjs http://127.0.0.1:3000
```

The generator writes:

- `qa/generated/KALAM_BRAND_SURFACE_INVENTORY.md` — human-readable discovery summary and route-state/metadata coverage
- `qa/generated/kalam-brand-surface-inventory.csv` — one row per discovered file
- `qa/generated/kalam-brand-surface-findings.csv` ? line-level automated matches and their recorded dispositions
- `qa/generated/kalam-brand-route-smoke.json` ? per-route HTTP smoke results and status distribution
- `qa/generated/kalam-brand-surface-inventory.json` — full inventory, findings, metadata checks and inherited route-state detail

The JSON file is the detailed evidence source. Generated outputs must be refreshed after source or documentation changes.

## Automated scans

The generator scans for:

- legacy customer-facing brand names
- obsolete slogans
- legacy brand-color literals
- placeholder/coming-soon language in source and public assets
- unsupported-claim candidates in source, public assets and relevant documentation
- dead-anchor (`href="#"`/`to="#"`), empty-href and empty-click-handler candidates in application source
- route metadata candidates and inherited route states

Regex matches are candidates, not automatic defects. Dead links/actions, contradictory terminology, rendered metadata, visual quality, accessibility and workflow behavior still require dedicated tests and human review.

## Legacy identity rule

Matches for historical names are not automatically defects. Classify each match as:

- customer-facing defect
- technical compatibility
- migration/historical evidence
- test fixture
- documentation history
- approved exception
- policy reference

Technical identifiers such as `corplms` may remain where changing them would break compatibility. They must not leak into active customer-facing brand surfaces. Historical delivery records remain immutable evidence; active product guidance and customer-facing documentation must use Kalam.

## Canonical terminology checks

Preferred concepts include:

- workforce capability
- role expectation
- skill
- competency
- evidence
- readiness
- development
- learning
- assessment
- credential
- compliance evidence
- workforce intelligence
- governed AI

## Route-state and metadata requirements

Every route must resolve to an intentional loading, error, not-found and global-error experience through its own segment or an ancestor boundary. Static metadata detection is only a source-level hint; rendered metadata must be verified in a browser.

## Completion rule

No audit report may claim 100% surface coverage unless every discovered route/file/surface has a recorded disposition.

No brand score may be inflated to 9.9 solely because automated scans pass. Browser, accessibility and functional evidence remain required. Generated inventory rows begin in `NEEDS_MANUAL_REVIEW`; discovery does not imply approval or certification.


## Browser accessibility smoke (axe-core)

Start the production server and run the automated WCAG 2.2 A/AA rules across every inventoried application route:

```powershell
node qa/brand-accessibility-smoke.mjs http://127.0.0.1:3000 --all
```

The browser runner uses the installed axe-core version and Chrome DevTools Protocol. It records each route, axe rule results, node-level evidence and scan errors in:

- `qa/generated/kalam-brand-accessibility-smoke.json`

Latest recorded run: axe-core 4.13.0; 92/92 inventoried routes scanned; 0 scan errors; 0 automated WCAG 2.2 A/AA violation instances. This is automated evidence only, not a complete WCAG conformance declaration. Protected routes may render unauthenticated states, and the scan does not replace keyboard-only, screen-reader, zoom/reflow, cognitive or manual interaction testing.

## Latest runtime evidence

- Production build: PASS (Webpack; Next.js 16.4.3).
- TypeScript: PASS.
- ESLint: PASS with two existing unused-variable warnings in `apps/web/src/app/dashboard/people/admin/page.tsx`.
- Brand contract and palette assertions: PASS.
- HTTP smoke: 92/92 routes; 89 HTTP 200 and 3 HTTP 307 redirects; zero HTTP 5xx/request errors.
- axe-core: 92/92 routes; zero scan errors; zero automated WCAG 2.2 A/AA violations.

## Scope-correct disposition and certification status

The 593-row discovery inventory is not 593 equivalent customer-facing brand surfaces. The dedicated review ledger now distinguishes actual customer-facing/rendered surfaces from generic assets and internal/historical evidence.

Latest automated dispositions:
- 271 generic country-flag assets excluded from Kalam brand scoring.
- 49 dated historical delivery records retained as explicit historical exceptions; they are not active customer-facing identity.
- 45 internal governance/delivery files excluded from customer-facing brand scoring.
- 4 canonical source-of-truth documents read and reconciled: the claim registry, Kalam brand governance standard, global enterprise brand system, and ADR-014.
- 2 canonical Geist font assets confirmed in use.
- 200 active rendered/source surfaces still require human brand/visual review.
- 177 user-facing copy/component surfaces still require terminology review.
- 190 route/component/state/style/document surfaces still require manual accessibility review.
- 94 content-bearing routes/communications/documents still require claim evidence review.
- Zero high-risk unsupported-claim pattern matches remain in active customer-facing source; this is a pattern scan, not proof of claim substantiation.
- Browser experience smoke: 92/92 route paths; 368 viewport checks at 320, 390, 768 and 1440 CSS pixels; zero horizontal overflow findings, zero keyboard findings and zero scan errors.
- 13 distinct non-login route destinations (14 route requests) received direct responsive and keyboard coverage. 78 route requests resolved to the login fallback; authenticated dashboard screens still require authorized test sessions.

New evidence:
- qa/generated/kalam-brand-surface-review.json
- qa/generated/kalam-brand-surface-review.csv
- qa/generated/KALAM_BRAND_SURFACE_REVIEW.md
- qa/generated/kalam-brand-route-experience-smoke.json
- qa/brand-surface-review.mjs
- qa/brand-route-experience-smoke.mjs

Automated browser evidence remains: HTTP smoke 92/92 routes (89 HTTP 200, 3 HTTP 307 redirects; zero 5xx/request errors) and axe-core 4.13.0 on 92/92 routes (zero scan errors, zero automated WCAG 2.2 A/AA violation instances).

## Canonical asset remediation

The previous kalam-logo.svg and kalam-symbol.svg were corrupted six-byte files. They have been rebuilt as valid SVGs. PWA icons previously named 192x192 and 512x512 were actually 64x64 and 128x128; they have been regenerated at their declared dimensions. Favicon, Apple touch icon and 1200x630 Open Graph image were also regenerated. The PWA manifest now uses the Kalam canvas and declares icon purpose. Seven unreferenced legacy Kognivon raster assets and five unused framework-starter SVGs were removed after repository-wide reference checks.

Verification:
- Brand contract: PASS, including SVG source and PNG dimension validation.
- Live asset smoke: 10 current brand asset/manifest endpoints PASS, including the multi-resolution ICO favicon; 12 removed legacy/starter URLs return 404; homepage metadata points to the canonical logo.
- Production Webpack build: PASS (Next.js 16.4.3).
- TypeScript: PASS.
- ESLint: PASS with two existing unused-variable warnings in apps/web/src/app/dashboard/people/admin/page.tsx.
- Original local checkout previously passed the 92/92 HTTP and axe route checks independently.

Manual keyboard and screen-reader sign-off, authenticated workflow checks, visual sign-off, legal name clearance and human brand/claim approvals remain open. Automated results do not replace those approvals. Do not claim 9.9 certification or 100% completion until the remaining evidence and sign-offs are recorded.
