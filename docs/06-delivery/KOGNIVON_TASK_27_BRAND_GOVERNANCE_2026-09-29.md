# Kognivon Task 27 — Brand Governance

Date: 2026-09-29  
Status: Complete.

## Brand decision

`Kognivon` is the master product and company-facing name. `KVON` is not used in the current product experience and must not be introduced casually as a replacement or abbreviation.

## Audit findings

- No `KVON` references were found in the application or delivery documentation searched for this task.
- Public header, footer, authentication screens, dashboard shell, verification page, and error/loading surfaces use Kognivon naming or the shared `KognivonBrand` component.
- Root metadata, Open Graph metadata, Twitter metadata, application name, manifest, sitemap, robots rules, favicons, app icons, and social preview assets use Kognivon.
- The logo component centralizes the light/dark asset choice, accessible home label, descriptor behavior, and compact/full variants.
- Dashboard and public CSS include explicit Kognivon brand-system comments and shared logo sizing rules.

## Governance rules

- Use `Kognivon` in page titles, navigation, public copy, authentication, trust content, support content, and application chrome.
- Use `Kognivon` in asset filenames and metadata unless a technical compatibility requirement requires an existing historical identifier.
- Treat `CorpLMS` as a repository/technical continuity identifier only; it is not customer-facing brand copy.
- Do not introduce `KVON` without an explicit future brand decision and an updated asset/content system.

## Verification

- Static repository search found no KVON references in the audited scope.
- Existing shared brand assets and metadata paths were inspected.
- `pnpm --filter web typecheck` passed in the preceding Task 26 verification.

## Follow-up

Any future visual brand change should update the shared `KognivonBrand` component and source assets first, then validate public, authentication, dashboard, favicon, and social-preview surfaces together.
