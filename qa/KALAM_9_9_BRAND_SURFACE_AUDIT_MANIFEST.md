# Kalam 9.9 Brand Surface Audit Manifest

**Branch:** `work/final-production-readiness-2026-10-31` (original local checkout)
**Purpose:** reproducible repository-level inventory, identity/terminology scan and verification traceability. The dedicated validation branch and PR #36 contain the corresponding reviewed implementation.

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
- `qa/generated/kalam-brand-surface-findings.csv` - line-level automated matches and their recorded dispositions
- `qa/generated/kalam-brand-route-smoke.json` - per-route HTTP smoke results and status distribution
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

Latest original-local-checkout run: axe-core 4.13.0; 92/92 requested route paths scanned; 0 scan errors; 0 automated WCAG 2.2 A/AA violation instances. 78 protected-route requests resolved to the login fallback, so this is not authenticated dashboard coverage. This is automated evidence only, not a complete WCAG conformance declaration.

## Latest original-local-checkout evidence

- Production build: PASS (Next.js 16.4.3; isolated `.next-kalam-brand-local` output).
- TypeScript: PASS.
- ESLint: PASS.
- Brand contract and palette assertions: PASS; 492 web/public source and asset files scanned.
- Local inventory: 593 rows; 92 routes; 83 reusable components; 280 public assets; 97 documentation files; 49 historical records; 47 internal governance/delivery files; 2 canonical source-of-truth documents reviewed.
- HTTP smoke: 92/92 requested routes; 89 HTTP 200 and 3 HTTP 307 redirects; zero HTTP 5xx/request errors.
- axe-core 4.13.0: 92/92 requested route paths; zero scan errors; zero automated WCAG 2.2 A/AA violations. 78 requests resolved to the login fallback.
- Responsive/keyboard smoke (post-cleanup production build): 92 route requests × 4 viewport widths = 368 checks; 17 routes reached non-login destinations; 75 resolved to login. Zero horizontal-overflow findings, zero keyboard findings and zero scan errors.

## Certification remains separate from automation

The current generated inventory still requires manual disposition. Brand/visual review remains open for 200 active surfaces; terminology review for 177 surfaces; accessibility review for 190 surfaces; and claim-evidence review for 94 content-bearing surfaces. 271 generic flag assets, 49 historical records and 45 internal governance/delivery records are excluded from customer-facing brand scoring. Automated browser scans do not clear these human-review registers. Human screen-reader/visual review, authenticated role workflow testing, and brand/claim approvals remain outstanding. Do not claim 9.9 certification or 100% completion until those tasks are evidenced and signed off.

The original local checkout was independently rebuilt and also passed 92/92 route smoke checks and 92/92 axe-core route scans with zero scan errors and zero automated WCAG 2.2 A/AA violation instances.
