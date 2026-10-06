# ADR-010 — Governed AI Provider Abstraction

Status: Accepted
Date: 2026-09-24

## Decision
AI is an optional application service behind a policy gateway and provider abstraction. It is disabled by default in the current baseline.

The first production target is the OpenAI-compatible adapter, which supports a
managed OpenAI endpoint or an approved compatible gateway. Anthropic Claude is
also supported through its native Messages API adapter. Ollama remains a local
development option and is not a production dependency.

## Why
Model vendors change, and AI must not bypass tenant permissions or turn generated text into authoritative records.

## Consequences
AI requests carry tenant/user/feature context, allowed sources, model and prompt versions. Output must have provenance/safety status where applicable. Consequential use cases require human review. Provider credentials are environment secrets.

The authorized tenant administrator configures the provider, model and policy
through the Kalam AI workspace after deployment. A connection test must pass
before the tenant policy is enabled.

## 2026-10-04 model evaluation candidate (not activated)

For an initial benchmark of frequent, grounded text Q&A, evaluate `gpt-6-luna`
against `gpt-6.1-sol` as the quality-oriented alternative. This is a test
shortlist, not a production selection: decide only after representative Kalam
evaluations of groundedness/citations, refusal behavior, latency and total cost.
See [OpenAI model selection](https://developers.openai.com/api/docs/guides/model-selection)
and the [GPT-6 Luna model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna).

The direct `api.openai.com` Chat Completions adapter uses the current
`developer` instruction role and `max_completion_tokens`; other
OpenAI-compatible gateways retain their configured compatibility contract.
This behavior is covered by mocked tests only. No real provider handshake was
performed, no production model was registered, and deployment-level AI remains
disabled until secrets, staging validation and policy approval are in place.
