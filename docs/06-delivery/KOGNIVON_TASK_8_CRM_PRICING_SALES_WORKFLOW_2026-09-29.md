# Kognivon Task 8 — CRM → Pricing → Sales Workflow

Date: 2026-09-29

## Scope

Trace public pricing and evaluation CTAs through inquiry capture, attribution, CRM conversion, account/contact creation, plan linkage, opportunity creation and trial scheduling.

## Existing contract verified

- Public pricing reads active, explicitly published CRM plans and offers.
- Pricing CTAs carry the selected plan code into guided evaluation or Contact Sales.
- Inquiry capture stores request type, plan code, source, UTM fields, landing path, organization qualification and consent.
- CRM conversion creates or reuses the account, creates the primary contact, preserves attribution metadata, links the plan, creates an opportunity and optionally schedules a trial.
- Conversion is tenant-scoped and protected by SaaS CRM permissions.

## Change

Inquiry conversion no longer creates an unqualified zero-value opportunity through a one-click action. The CRM operator now supplies opportunity amount, currency and (for guided evaluations) trial seats before converting the inquiry. Existing inquiry plan-code resolution and attribution retention remain server-controlled.

## Verification

- `pnpm --filter web typecheck` — passed.
- `git diff --check` — passed; repository-wide line-ending warnings are working-tree normalization warnings.
- API conversion coverage exists in `apps/api/tests/test_saas_commercial.py`; local execution depends on the complete API dependency environment.
- Web lint/build remain environment-blocked because `apps/web/node_modules` is absent (`eslint` and `next` unavailable).
