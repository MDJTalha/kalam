# Corporate LMS — Phase 0 Exit Evidence

Version: 0.1
Date: 2026-09-24
Status: Evidence record for Phase 0 review

## Required outputs
- Master plan: `docs/01-governance/PROJECT_MASTER_PLAN.md`.
- Requirements baseline: `docs/02-product/REQUIREMENTS_BASELINE.md`.
- Requirements traceability: `docs/02-product/REQUIREMENTS_TRACEABILITY_MATRIX.md`.
- Domain model: `docs/02-product/DOMAIN_MODEL.md`.
- Architecture baseline: `docs/03-architecture/ARCHITECTURE_AND_TECHNICAL_PLAN.md`.
- Critical architecture diagrams: `docs/03-architecture/ARCHITECTURE_DIAGRAMS.md`.
- Security baseline: `docs/04-security-compliance/SECURITY_COMPLIANCE_BASELINE.md`.
- QA strategy: `docs/05-quality/QA_TEST_STRATEGY.md`.
- CI baseline/evidence: `docs/05-quality/CI_BASELINE.md` and `.github/workflows/ci.yml`.
- Delivery roadmap/status: `docs/06-delivery/`.
- ADR index + 13 required records: `docs/07-decisions/`.
- Monorepo skeleton: `apps/`, `packages/`, `database/`, `infra/`, `tests/`.
- Environment templates: `.env.example`, `.env.platform.example`, application templates.
- Project controls: change control, risk register, environment matrix.

## Verified evidence
- Git repository exists on `master` and resolves successfully.
- Alembic migration check: PASS.
- Demo seed: PASS.
- Ruff: PASS.
- mypy: PASS.
- API pytest: 15 passed.
- Frontend typecheck: PASS.
- Frontend lint: PASS — current local run completed without reported warnings/errors.
- Frontend production build: PASS — `npm --prefix apps/web run build`, exit code 0; 42 routes generated.
- API pytest: PASS — 15 tests passed.
- Current documentation reviewed against the repository structure and implementation status.
- Frontend design direction reconciled as a controlled Phase 0 UX baseline. Phase 1 visual implementation now follows the approved bright blue-first enterprise theme, with deep navy navigation, restrained gold identity accents and green reserved for semantic success states.

## Exit interpretation
Phase 0 baseline evidence is complete for the local development gate. Remote CI remains a separate authoritative signal. Phase 0 does not imply that Phase 1+ product functionality or production release is complete. Phase 1+ functionality is not considered Phase 0 exit evidence.
## 2026-09-28 — Formal closure verification
Status: **LOCAL TECHNICAL GATE PASSED HISTORICALLY; FORMAL HOSTED-CI GATE OPEN**.
The 2026-09-24 and 2026-09-25 records above are historical snapshots. The current checkout is `release/phase8-rc1-20260927` with substantial uncommitted Phase 8 and SaaS CRM work; it is not the 42-route historical baseline.
- Required foundation documents, repository layout, environment templates, workflow and 13 ADR records were found. The previous QA baseline labelled OPEN has been identified as a dated snapshot; the later re-baseline is the local gate record.
- `.github/workflows/ci.yml` now starts a ClamAV service, checks the scanner transport and sets `FILE_SCAN_PROVIDER=clamd` for the API tests. YAML parsing and the scanner configuration contract passed locally. The active ClamAV instance returned PONG using the same health command.
- The two API tests blocked on the stopped host scanner passed against the healthy ClamAV instance through a temporary local port relay: 2 passed, 1 dependency deprecation warning. Full current-tree API regression is being rerun separately; record its final result before promoting the local gate.
- No Git remote is configured for this checkout. The connected GitHub account has no identifiable Kognivon/CorpLMS repository. A hosted workflow URL/result for the exact candidate is unavailable. Do not mark the roadmap's CI exit criterion PASS or change formal status to CLOSED until an authorized repository/remote and successful hosted CI run are recorded here.
- Formal evidence required: exact commit SHA, repository/branch, hosted CI run URL, all job conclusions, approver and date. Local ClamAV and tests are supporting evidence only.

### Current-tree validation result (2026-09-28)
- One complete API suite passed **111/111** with real ClamAV access before further concurrent SaaS finance edits. Its exact source tree was uncommitted and has since changed, so it is not a release-candidate certificate.
- The later current-tree run after the finance changes reported **110 passed, 1 failed, 1 dependency warning**. The failing seeded learner login returned 401 in `test_phase2_capacity_waitlist_promotes_on_completion`; subsequent read-only inspection showed the account active and unlocked. This intermittent test-data/session interaction needs an isolated rerun and root-cause resolution. No green full-suite claim applies to the later tree.
- Targeted SaaS commercial regression after fixing duplicate payment fields and invoice payment/void guards: **3 passed**, one dependency warning. Current API mypy: **PASS, 54 source files**; Ruff: **PASS**. Scoped diff check and Python syntax compilation: PASS. The marketing inquiry ORM now maps the three columns in migration `y0z1a2b3c4d5`.
- The temporary local ClamAV relay was removed after each run. The production-style candidate stack was not redeployed or mutated.
- **Formal Phase 0 status remains OPEN**: source snapshot is uncommitted and evolving, the latest complete regression is not green, and a hosted CI run cannot be produced without an approved Git repository/remote.

### Isolated CI-equivalent attempt and remaining gate
- Two separate temporary PostgreSQL databases were created for verification, migrated to `b3c4d5e6f7g8`, and seeded. A separate Redis namespace was used. A clean database revealed that CI had omitted the Kognivon SaaS operator bootstrap; the workflow now runs `scripts/bootstrap_saas_ops.py` and sets `SAAS_OPS_TENANT_SLUG` for tests, without creating an operator account.
- The governed AI retrieval test had mocked only capability retrieval although its Q&A path calls authorized learning retrieval. The test now mocks both relevant paths. All five affected AI and SaaS CRM tests passed against the isolated database.
- Final clean-database full suite: **111 passed, 1 failed, 1 dependency warning**. The sole failure was `test_clamd_scans_clean_file`: the temporary Windows host port relay exited before that test, while the existing ClamAV container stayed healthy. This is local relay infrastructure failure, not a green CI run. Earlier direct scanner-dependent tests passed against ClamAV.
- The temporary relay and both verification databases were removed. The checked-out source is still uncommitted and no Git remote or hosted CI run is available. **Formal Phase 0 remains OPEN** until an immutable candidate and hosted CI evidence satisfy the roadmap exit criterion.

## 2026-09-28 — Current-tree local closure pass

Status: **LOCAL PHASE 0 FOUNDATION GATE PASSED ON CURRENT TREE**.

A new repeatable root command, `npm run validate:phase0`, now validates required Phase 0 artifacts, the 13 ADR records, canonical environment values, Docker Compose parsing/readiness, migration head, API static/type/test gates, web type/lint/build gates and repository state.

Current evidence:
- Required Phase 0 documents/repository skeleton: PASS.
- Requirements traceability matrix upgraded to v0.2 with module, implementation/design and verification mappings.
- Canonical endpoints/ports: PASS — web 3000, API 8000, PostgreSQL 55434, Valkey 56379, ClamAV 55000.
- PostgreSQL, Valkey and ClamAV readiness: PASS.
- Alembic migration head: `b3c4d5e6f7g8 (head)` — PASS.
- Ruff: PASS.
- mypy: PASS — 54 source files.
- API pytest: **112 passed, 1 dependency deprecation warning, 0 failures**.
- Web TypeScript: PASS.
- Web ESLint: PASS.
- Next.js production build: PASS — **75 routes generated**.
- Generated browser-profile path `.phase8rc-browser/` is now excluded from Git status.

### Defects found and closed during the current run

- Full-web lint exposed an impure request-time calculation in the SaaS Contracts screen; the clock use is now explicit and documented for the server-rendered operational snapshot.
- Forecast contained an unused UI import; removed.
- The canonical local ClamAV volume lacked a usable database after an offline update attempt. It was bootstrapped from the already healthy local Phase 8 ClamAV database, the canonical container was recreated on port 55000, and the clean-file scanner regression now passes.
- The Phase 0 validator now starts/checks PostgreSQL, Valkey and ClamAV instead of assuming dependencies are already healthy.

### Remaining external evidence

No Git remote is configured for this checkout. Therefore a hosted GitHub Actions result for the exact candidate cannot be produced locally. This is an external governance/deployment evidence dependency, not an unresolved local Phase 0 engineering defect.

Formal hosted-CI promotion still requires: repository/remote, exact commit SHA, successful workflow URL/job conclusions, approver and date.


## 2026-09-30 — Current-tree engineering closure pass
Status: **LOCAL PHASE 0 FOUNDATION GATE PASSED; ENGINEERING BASELINE CLOSED**.

Current verification after Phase 1 QA:
- Required Phase 0 artifacts and 14 ADR records: PASS.
- Canonical environment contract and dependency readiness: PASS.
- Alembic migration head: cc33dd44ee55.
- Ruff: PASS.
- mypy: PASS — 58 source files.
- Full API regression: 124 passed, 1 dependency deprecation warning, 0 failures.
- Web TypeScript: PASS.
- Web ESLint: PASS with 0 warnings.
- Next.js production build: PASS — 82 routes.
- Current-tree defect fixed in capabilities.py (undefined level variable).
- Phase 1 QA hardening completed without reopening the Phase 0 foundation model.

### Formal hosted-CI note
The checkout still has no Git remote configured. Therefore hosted CI cannot be independently evidenced from this machine. The local engineering closure is complete; formal hosted release promotion remains an external repository/CI governance step requiring an immutable commit and successful hosted workflow evidence.

