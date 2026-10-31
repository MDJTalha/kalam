# Kalam 9.9 Brand Surface Audit Manifest

**Branch:** `kalam/brand-9-9-implementation`
**Purpose:** reproducible repository-level inventory and terminology/claim scan.

## Required inventory

The audit must enumerate:

- all `apps/web/src/app/**/page.tsx` routes
- all route-level loading/error/not-found pages
- all reusable files under `apps/web/src/components/`
- all CSS/design-token files
- public brand assets
- metadata and structured-data declarations
- transactional/public communications
- customer-facing documentation

For each item record:

`surface_id | route/file | audience | type | states | brand status | terminology status | accessibility status | claim status | test status | evidence | owner`

## Automated scans

At minimum scan source and public content for:

- legacy customer-facing brand names
- obsolete slogans
- obsolete category descriptions
- competing capability models
- unsupported claims
- placeholder/coming-soon language
- dead links/actions
- hard-coded brand colors
- inconsistent Kalam capitalization
- missing page metadata
- duplicate/contradictory terminology

## Legacy identity rule

Matches for historical names are not automatically defects. Classify each match as:

- customer-facing defect
- technical compatibility
- migration/historical evidence
- test fixture
- documentation history
- approved exception

Technical identifiers such as `corplms` may remain where changing them would break compatibility. They must not leak into customer-facing brand surfaces.

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

## Completion rule

No audit report may claim 100% surface coverage unless every discovered route/file/surface has a recorded disposition.

No brand score may be inflated to 9.9 solely because automated scans pass. Browser, accessibility and functional evidence remain required.

