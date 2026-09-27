# ADR-011 — Learning Standards Boundary

Status: Accepted
Date: 2026-09-24

## Decision
Keep standards integrations behind adapters for LTI, xAPI and optional SCORM/cmi5 support rather than embedding standards-specific logic throughout the core learning domain.

## Why
Preserves a clean internal model while allowing external content/activity ecosystems.

## Consequences
Imported learning activity must still map to tenant/user authorization and durable records. A standards adapter is not considered production-complete until handshake, mapping, failure and audit evidence exists.