# Corporate LMS — Phase 7 Governed AI Progress Evidence

Date: 2026-09-25

## Scope

Phase 7 is defined by the delivery roadmap as **Governed AI**:
- AI gateway
- content assistance
- summaries
- recommendations
- learner Q&A over authorized content
- skill-gap explanations
- AI evaluation and audit

Mandatory governance rules:
- no permission bypass
- no unsupported authoritative claims
- no hidden consequential employment decisions

## Implemented increment

### Governed AI gateway

- Added `apps/api/app/api/routes/ai.py`.
- Added `GET /api/v1/ai/status`.
- Added `POST /api/v1/ai/query`.
- Gateway is permission protected.
- Retrieval is tenant scoped and limited to published courses in which the signed-in user has an active/completed enrollment.
- AI prompt explicitly requires answers to remain grounded in authorized LMS content.
- Unsupported authoritative claims and employment decisioning are explicitly prohibited in the provider instruction.
- Provider integration is fail-closed until `AI_PROVIDER=ollama` and `AI_MODEL` are configured.

### Audit/evidence model

Added `AIInteraction` persistence with:
- tenant/user scope
- request type
- provider/model
- authorized source IDs
- SHA-256 prompt hash
- allowed flag
- response summary
- latency
- timestamp

Raw prompts and raw AI responses are intentionally not persisted by this layer.

AI requests also create tenant-scoped audit log records.

### Database

Migration:
`ad141803eb2c_phase7_governed_ai_foundation.py`

Applied successfully.

Current Alembic revision:
`ad141803eb2c`

### Web experience

Added:
- `/dashboard/ai`
- `governed-ai-workspace.tsx`

The workspace exposes:
- provider/configuration state
- governance controls
- authorized-content Q&A
- evidence/source display
- explicit unavailable-provider state

## Validation

- API regression: **60 passed, 1 warning** (latest full-suite run)
- Governed AI dedicated tests: **2 passed**
- Governed AI Ruff: **PASS**
- Governed AI now explicitly treats retrieved course material as untrusted reference content and instructs the provider not to follow commands embedded in that material; QA/summary behavior is separated at the provider instruction layer.
- Phase 6 saved-report compatibility regression: **1 passed** after accepting both hyphenated and underscored report type names and canonicalizing persistence.
- API compile/import: **PASS**
- Alembic migration: **PASS**
- Alembic current/head: **ad141803eb2c**
- Existing warning remains the Starlette/httpx TestClient deprecation warning.
- Frontend dependency tree was found inconsistent: the repository referenced local `next-16.3.6.tgz` and `eslint-config-next-16.3.6.tgz` archives that were absent. Matching registry archives were restored and their SHA-512 values were verified against the previously captured lockfile values. The package manifest remains on the original local-archive contract; the lockfile is currently being recovered by the workstation's concurrent npm recovery processes and is not yet a validated gate. Frontend lint/build are therefore not re-gated.
- Browser-level end-to-end validation remains unavailable through the current remote-control toolset.

## Phase 7 status

**IN PROGRESS**

This is the first Phase 7 implementation increment, not a phase closure. Remaining Phase 7 work includes:
- provider abstraction hardening
- content chunking/retrieval quality
- summaries and content-authoring assistance
- recommendation and skill-gap explanation workflows
- AI evaluation/evidence suite
- adversarial/authorization tests
- prompt-injection defenses
- model/provider observability
- frontend navigation/information architecture integration
- final UI/UX quality gate
- end-to-end runtime validation
- final Phase 7 exit evidence


## 2026-09-25 — Phase 7.3–7.7 hardening increment

Implemented in this increment:
- Added request-side prompt-injection detection for common instruction-override, secret-exfiltration, role-escalation and authorization-bypass patterns.
- Added deterministic grounded-response evaluation helpers and a reusable six-case evaluation dataset/runner.
- Added tenant-scoped AI interaction human-review persistence, Alembic migration, review queue API, review decision API and audit logging.
- Added a tenant-scoped AI telemetry API covering request counts, allowed/blocked outcomes, average latency, provider/model usage and human-review counts.
- Added an OpenAI-compatible governed generation adapter using environment-reference-only credentials; unsupported adapters continue to fail closed.
- Removed the four frontend lint warnings discovered in Analytics and Team during the Phase 7 quality gate.

Verified evidence:
- AI evaluation/provider unit regression: 6 passed.
- Existing non-database AI governance unit subset: 3 passed, 3 deselected.
- Phase 7 evaluation runner: 6/6 cases passed, score 100% for the current deterministic baseline corpus.
- Ruff on modified Phase 7 backend/tests: PASS.
- Frontend ESLint: PASS with no reported warnings.
- Frontend TypeScript: PASS.
- Next.js production build: PASS, 49/49 application routes.

Open validation boundary:
- The canonical CorpLMS PostgreSQL endpoint expected at 127.0.0.1:55434 is currently unavailable.
- Human-review migration application and database-backed AI integration regression are therefore not claimed as passing in this increment.
- The unrelated PostgreSQL listener on port 5432 rejects the CorpLMS credentials and has not been substituted for the project database.
