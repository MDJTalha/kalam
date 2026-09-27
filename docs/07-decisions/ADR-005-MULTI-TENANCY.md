# ADR-005 — Multi-Tenancy

Status: Accepted
Date: 2026-09-24

## Decision
Use explicit tenant ownership on tenant business records with server-side tenant filters and authorization checks.

## Why
- Clear data ownership.
- Easier audit and debugging.
- Strong compatibility with relational constraints and modular monolith deployment.

## Consequences
Every tenant-owned query is responsible for the tenant boundary. Cross-tenant administration is an explicit privileged workflow. Negative cross-tenant tests are release evidence. Future database row-level security may add defense in depth but cannot replace application authorization.