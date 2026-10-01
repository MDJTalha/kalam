# Kognivon Task 13 — Enterprise Forms and Data Entry UX

Date: 2026-09-29

## Scope

Use the public Contact Sales form as the reference standard for labels, required/optional clarity, validation, grouping, save states, errors, success messaging and accessibility across shared administrative forms.

## Findings

- The public inquiry form already provides strong grouped fields, validation, consent, error messaging and success recovery.
- The shared `ResourceForm` centralizes API persistence, JSON transforms, loading states, errors, success messages and optional connection tests.
- Shared resource forms lacked protection against accidental browser/tab closure after edits and did not visually identify required fields consistently.

## Changes

- Added unsaved-change protection to `ResourceForm` through a `beforeunload` guard that is removed after save or while the form is busy.
- Added `aria-busy` to the form during save/test operations.
- Added visible `*` and `aria-required` semantics for required shared-form fields.

## Verification

- `pnpm --filter web typecheck` — passed.
- `git diff --check` — passed; repository-wide line-ending warnings are working-tree normalization warnings.
- Web lint/build remain environment-blocked because `apps/web/node_modules` is absent (`eslint` and `next` unavailable).
