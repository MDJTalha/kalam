# Kognivon Task 16 — Authentication and Account Lifecycle

Date: 2026-09-29
Status: Complete

## Audited lifecycle

- Tenant-aware password login with inactive-user rejection and temporary failed-login lockout.
- Logout, cookie-backed sessions, session expiry, current-session protection, revoke-other-sessions, and session listing.
- Password reset request/confirmation, one-time expiry-bound tokens, and session revocation after reset.
- Authenticated password changes with current-password verification and other-session revocation.
- Invitation creation, expiry, one-time acceptance, tenant role assignment, and duplicate-user protection.
- Disabled users, tenant status, role/permission resolution, SSO discovery/OIDC, profile preferences, and account settings UI.

## Changes made

- `get_current_user` now joins the tenant and rejects sessions when the tenant is no longer active. This closes the gap where an already-issued session cookie could remain usable after tenant deactivation.
- Invitation acceptance now requires an active tenant and verifies that the invitation role belongs to the invitation tenant before creating the user.
- Added `apps/api/tests/test_auth_account_lifecycle.py` with isolated regression cases for deactivated-tenant session rejection and invitation tenant/role integrity.

## Existing product coverage confirmed

- Login and password reset are exposed through branded web routes.
- Account settings expose password change, profile/preferences, notification preferences, and active-session management.
- Administrative user deactivation revokes active sessions and prevents self-deactivation.
- Role assignment and invitation creation are protected by tenant-scoped permissions.

## Verification

- Python compilation of the changed API modules — passed.
- `pnpm --filter web typecheck` — passed.
- Targeted pytest execution could not start because `pytest` is not installed/available in the current shell environment; the new regression module passes Python compilation.
- Browser smoke verification remains unavailable because no browser surface is exposed in the current computer-use environment.
