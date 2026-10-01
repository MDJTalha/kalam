# Kognivon Task 14 — Tables, Filters and Bulk Workflows

Date: 2026-09-29

## Scope

Standardize enterprise table semantics across CRM and operations surfaces, including searchable/filterable registers, pagination, exports, row actions, empty states and accessible column structure.

## Findings

- CRM registers already provide scoped search/filter controls, pagination, exports where appropriate, row actions and useful empty states.
- The shared `DataTable` component did not provide a consistent table caption or column header scope, leaving screen-reader users without reliable table context.

## Changes

- Added an optional accessible caption contract to `DataTable`.
- Added `scope="col"` to all shared table headers.
- Applied captions to the primary CRM accounts, pipeline, tasks, contracts, subscriptions and renewals tables.

## Verification

- `pnpm --filter web typecheck` — passed.
- `git diff --check` — passed; repository-wide line-ending warnings are working-tree normalization warnings.
- Web lint/build remain environment-blocked because `apps/web/node_modules` is absent (`eslint` and `next` unavailable).
