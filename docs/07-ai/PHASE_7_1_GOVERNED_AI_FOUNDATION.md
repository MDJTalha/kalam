# Phase 7.1 — Governed AI Foundation

Date: 2026-09-25
Project: C:\\Projects\\CorpLMS

## Objective

Establish the persistent governance and configuration boundary required before enterprise AI features are expanded.

## Implemented

- Tenant-scoped AI provider registry.
- Tenant-scoped AI model registry.
- Versioned AI prompt-template registry.
- Tenant-scoped AI governance policy.
- Dedicated ai.manage permission.
- Tenant-aware administrative API controls.
- Environment-reference-only handling for provider secrets.
- Provider endpoint validation with HTTPS enforcement outside development.
- Prompt-template variable and size validation.
- Governance policy limits for input and output size.
## Runtime enforcement

- Learner AI requests require learning.access.
- AI execution requires an enabled tenant governance policy.
- A tenant must have an enabled provider and enabled model before AI generation is considered configured.
- Provider types are restricted by the tenant governance policy.
- Grounding remains tied to authorized published course content.
- Employment decisioning remains disabled by default.
- Raw prompt and raw response persistence remain disabled by default.
- AI interactions retain source identifiers, prompt hash, decision state, latency and a bounded response summary.
- Administrative mutations produce audit events.

## Database

Migration: l7m8n9o0p1q2_add_governed_ai_registry.py
Applied head: l7m8n9o0p1q2

Tables:
- ai_providers
- ai_models
- ai_prompt_templates
- ai_governance_policies

## Validation evidence
- Migration upgrade: PASS.
- Demo seed after migration: PASS.
- Phase 7.1 AI governance regression: 4 passed, 1 warning.
- Combined Phase 6 + Phase 7 governance/integration regression: 25 passed, 1 warning.
- Full API regression: 78 passed, 1 warning in 4m23s.
- Ruff on modified backend, governance service, seed and AI tests: PASS.

Known warning:
- Starlette/httpx TestClient deprecation warning; non-failing and unrelated to governance correctness.

## Explicit boundaries

- No real third-party model/provider certification is claimed until a deployment secret and live connection test are supplied.
- No external API-key secret is stored in the database.
- OpenAI-compatible and Anthropic execution adapters are implemented; Ollama remains available for local development. Azure OpenAI and custom provider types remain registry-ready but require a dedicated runtime adapter or approved compatible gateway. The deployment kill switch remains closed until a production credential, model, policy, and live provider handshake are approved.
- Phase 7 overall remains IN PROGRESS.
