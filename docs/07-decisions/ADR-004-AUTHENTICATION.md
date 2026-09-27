# ADR-004 — Authentication Model

Status: Accepted
Date: 2026-09-24

## Decision
Use server-managed session records with an HTTP-only session cookie. Passwords are verified using Argon2id hashing.

## Why
- Reduces browser exposure of bearer tokens.
- Supports server-side session invalidation and lockout.
- Fits the same-origin web proxy boundary used by the current frontend.

## Consequences
Session expiry, revocation, password reset and account-lockout policy remain server responsibilities. Secure cookie flags become environment-specific; production requires HTTPS and `Secure` cookies. SSO/MFA are extension boundaries, not bypasses.