# Kognivon Task 4 — Global Shell Hardening

Date: 2026-09-29

## Scope

Harden the authenticated application shell across desktop and mobile states: account access, notification dismissal, organization visibility, route transitions, and header layout consistency.

## Changes

- Added an accessible account menu with settings, active sessions, help, and sign-out actions.
- Added Escape and outside-click dismissal plus explicit popup semantics to the header notification control.
- Restricted the organization switcher to users with `users.read`, matching the organization route permission contract.
- Close the mobile workspace navigation when the pathname changes.
- Rebalanced responsive header grids after removing the standalone Help header action.

## Verification

- `pnpm --filter web typecheck` — passed.
- `git diff --check` — passed; repository-wide line-ending warnings are pre-existing working-tree normalization warnings.
- `pnpm --filter web lint` — not runnable in this checkout because `apps/web/node_modules` is absent (`eslint` unavailable).
- `pnpm --filter web build` — not runnable in this checkout because `apps/web/node_modules` is absent (`next` unavailable).
- Browser visual smoke was not available because no browser surface was exposed in the computer-use environment.

## Files

- `apps/web/src/components/account-menu.tsx`
- `apps/web/src/components/dashboard-shell.tsx`
- `apps/web/src/components/notifications-center.tsx`
- `apps/web/src/components/workspace-nav.tsx`
- `apps/web/src/app/globals.css`
