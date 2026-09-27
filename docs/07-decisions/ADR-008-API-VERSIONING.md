# ADR-008 — API Versioning

Status: Accepted
Date: 2026-09-24

## Decision
Expose external REST APIs under a versioned `/api/v1` namespace.

## Why
Allows additive evolution and controlled breaking changes while keeping OpenAPI contracts explicit.

## Consequences
Breaking API changes require a new version and migration/deprecation plan. Internal module refactors do not require a new API version when the contract remains compatible. API errors should use a consistent envelope and request/correlation identifiers.