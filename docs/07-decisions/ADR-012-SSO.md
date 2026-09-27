# ADR-012 — SSO Strategy

Status: Accepted
Date: 2026-09-24

## Decision
Use OIDC as the first-class SSO integration boundary, with a separate adapter path for SAML where customer requirements justify it.

## Why
OIDC integrates cleanly with the current API/session model and provides standardized discovery, authorization and identity claims.

## Consequences
External identity is linked to an internal tenant/user record; it never bypasses internal authorization. Provider configuration and secrets are tenant-scoped. SSO is an integration capability, not part of the local-password trust model.