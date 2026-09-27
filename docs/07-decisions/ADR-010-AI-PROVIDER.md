# ADR-010 — Governed AI Provider Abstraction

Status: Accepted
Date: 2026-09-24

## Decision
AI is an optional application service behind a policy gateway and provider abstraction. It is disabled by default in the current baseline.

## Why
Model vendors change, and AI must not bypass tenant permissions or turn generated text into authoritative records.

## Consequences
AI requests carry tenant/user/feature context, allowed sources, model and prompt versions. Output must have provenance/safety status where applicable. Consequential use cases require human review. Provider credentials are environment secrets.