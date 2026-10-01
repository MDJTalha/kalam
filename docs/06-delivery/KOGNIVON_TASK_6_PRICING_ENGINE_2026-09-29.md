# Kognivon Task 6 — SaaS Pricing Engine

Date: 2026-09-29

## Scope

Verify that public USD pricing is driven by controlled commercial data and that authorized CRM users can manage plan structure, billing values, seat bounds, trials, merchandising, offers and publication windows.

## Findings

- Public pricing is sourced from the API public catalog, limited to active, public USD plans and current public offers.
- Public plan and offer publication is already explicit and time-window aware on the API side.
- Plan creation exposed fewer controls than plan editing, which could create records without the same seat, merchandising and display controls available during later edits.
- Offer creation did not expose the API-supported start and end dates, preventing campaign validity from being governed at creation time.

## Changes

- Aligned plan creation with plan editing for description, maximum seats, display order, public badge, CTA type/label, comparison label, featured merchandising and publication controls.
- Added offer start/end datetime fields and persisted them through the creation workflow.
- Preserved CRM-controlled public pricing, USD filtering, trial-aware evaluation CTAs, annual pricing display, current-offer filtering and negotiated-price disclosures.

## Verification

- `pnpm --filter web typecheck` — passed.
- `git diff --check` — passed; repository-wide line-ending warnings are working-tree normalization warnings.
- `python -m pytest apps/api/tests/test_saas_commercial.py -q` — blocked during collection because the local Python environment lacks `joserfc`.
- Web lint/build remain environment-blocked because `apps/web/node_modules` is absent (`eslint` and `next` unavailable).
