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
```

The generator writes:

- `qa/generated/KALAM_BRAND_SURFACE_INVENTORY.md` — human-readable discovery summary and route-state/metadata coverage
- `qa/generated/kalam-brand-surface-inventory.csv` — one row per discovered file
- `qa/generated/kalam-brand-surface-findings.csv` ? line-level automated matches and their recorded dispositions
- `qa/generated/kalam-brand-surface-inventory.json` — full inventory, findings, metadata checks and inherited route-state detail

The JSON file is the detailed evidence source. Generated outputs must be refreshed after source or documentation changes.

## Automated scans

The generator scans for:

- legacy customer-facing brand names
- obsolete slogans
- legacy brand-color literals
- placeholder/coming-soon language in source and public assets
- unsupported-claim candidates in source, public assets and relevant documentation
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
