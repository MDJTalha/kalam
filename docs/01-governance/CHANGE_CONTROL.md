# Corporate LMS — Change Control

Version: 0.1
Status: Phase 0 baseline

## Rule
No material scope or architecture change is accepted only through chat or code. The change must be recorded and traceable.

## Required change record
- Change ID.
- Date and owner.
- Requirement ID(s) affected.
- Business reason.
- Impacted modules/data/API/UI surfaces.
- Security and privacy impact.
- Testing/regression impact.
- Architecture/ADR impact.
- Migration/data impact.
- Target phase/release.
- Evidence and disposition.

## Decision classes
- Minor: implementation detail with no requirement/architecture impact.
- Controlled: requirement, data, API, security or UX behavior change.
- Major: tenancy, authorization, architecture, migration or release-policy change.

Controlled and major changes require review of the Requirements Traceability Matrix and relevant ADRs before implementation.

## Current baseline
The Phase 0 baseline is the governing reference as of 2026-09-24. Later changes must preserve historical evidence and should not silently rewrite prior decisions.