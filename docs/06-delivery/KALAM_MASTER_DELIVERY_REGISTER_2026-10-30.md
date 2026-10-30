# Kalam Master Delivery Register

**Register date:** 2026-10-30
**Authority:** This is the single status index for Kalam delivery. Detailed evidence remains in the linked records; this register controls the current disposition and next action.
**Repository:** `MDJTalha/kalam`
**Local path:** `C:\Projects\Kalam`
**Branch:** `work/kalam-local-changes-2026-10-26`
**Base HEAD observed:** `a1073cb34bc88e4e2b8cb6a41b622c908e104518`
**Working tree:** DIRTY — substantial staged, unstaged and untracked changes. Preserve all changes. No commit, push, merge, tag, registry publish, production migration or deployment is authorized by this register.

## 1. Delivery decision

**Current decision: NO-GO for production release.**

Kalam has substantial locally verified functionality and engineering controls. It is not yet a reviewed immutable release candidate, and the latest Phase 8 acceptance decision explicitly withholds release certification. Local test/build/image results must not be represented as staging or production evidence.

## 2. Canonical phase map

The numbering authority remains `DELIVERY_ROADMAP.md`, reconciled by `PHASE_NUMBERING_AND_ACCEPTANCE_RECONCILIATION_2026-10-27.md`.

| Canonical phase | Scope | Current disposition |
|---|---|---|
| Phase 5 | Compliance and skills core | Locally verified in recorded evidence |
| Phase 5A | Development Intelligence | Local acceptance recorded |
| Phase 5B | Coaching, Mentoring and Experience | Backend journey verified; rendered browser acceptance is separate |
| Phase 6 | Reporting, Analytics and Integrations | Local evidence recorded; external provider handshakes open |
| Phase 7 | Governed AI | Local evidence recorded; external provider/billing/SLA checks open |
| Phase 8 | Commercial / Production Release Readiness | OPEN — release certification withheld |

Legacy filenames for Phase 5A/5B remain unchanged to preserve references. Do not renumber phases based on legacy filenames.

## 3. Verified local evidence

Evidence is dated 2026-10-30 and applies to the working tree tested at that time; rerun candidate-sensitive checks after source freeze.

| Gate | Recorded result | Evidence / qualification |
|---|---|---|
| API tests | 224 passed, 0 failed, 0 errors | `qa/api-full-suite-20261030.json`; isolated PostgreSQL `kalam_test`, port 5435 |
| Targeted authorization/compliance | 25 passed, 0 failed | `qa/phase8-targeted-tests-20261030.json` |
| API quality | Ruff and mypy passed | 65 source files for mypy |
| Web quality | TypeScript and ESLint passed | Current-tree local checks |
| Web production build | Passed; 89 static pages | Isolated build output |
| Migrations | Clean isolated migration chain to `b2c3d4e5f6a7` | Isolated test database only; normal `corplms` database remains at `82cb7d9e1f4a` |
| API/web/worker images | Built and local runtime-smoked | API `779df2d0056854245ea331d0928d4fddaff5b111a7c933c4e7d5f0319ae7381b`; web final `5b1971bf6965038d5a5249d2106c1df2414797fa12dad6779ce96ddbe017c152`; worker `156b4fd11a3152f9568134012b96694b6e99dcd749e1dac7bead4d0c6ad10436`. Local isolated smoke only; not integrated deployment certification |
| Production web headers | 7/7 assertions passed | Local production-mode image only |
| Public accessibility | Login scan: 36 checks, 0 violations, 0 incomplete; homepage: 45 passes, 0 confirmed violations, manual review recorded | Not whole-application WCAG certification |
| Authenticated local workflows | Earlier isolated run reports Admin/Manager/Learner and course lifecycle success | `KALAM_AUTHENTICATED_ACCEPTANCE_2026-10-30.md`; scope-specific local evidence |
| Dependency checks | npm production audit 0 vulnerabilities; pip-audit no known vulnerabilities | Point-in-time local lockfile/dependency evidence |

## 4. Conflicting / superseding acceptance evidence

The authenticated acceptance report records a successful isolated QA workflow on a dedicated QA stack. However, the later section of `PHASE_8_RELEASE_ACCEPTANCE.md` records a mixed browser result: administrator form login failed, manager/learner pages were reached through injected API cookies rather than real browser login, and learner enrollment/completion failed.

**Conservative disposition:** authenticated browser acceptance is NOT ACCEPTED as a complete release gate. The positive isolated workflow remains valid only for its documented QA run and must not be used to override the later explicit Phase 8 NO-GO decision. Reconcile the machine-readable evidence, timestamps, source/image identity, API/web origins and database/fixture identity before closing this conflict.

## 5. Open release gates — ordered work queue

| Priority | ID | Required outcome | Acceptance evidence | State |
|---|---|---|---|---|
| P0 | REL-001 | Freeze and identify one candidate source tree without losing existing work | Reviewed file inventory, diff review, migration graph, build manifest and immutable commit/tag after explicit approval | BLOCKED — dirty tree |
| P0 | QA-AUTH-001 | Resolve real frontend login and same-origin session behavior for Admin, Manager and Learner | Real form login, cookie attributes, authenticated API calls and negative permission tests for each role | OPEN — conflicting/mixed browser evidence |
| P0 | QA-LEARN-001 | Verify learner enrollment and lesson completion persistence | Browser action plus database/API persisted enrollment and 100% completion evidence | OPEN — later acceptance record reports failure |
| P0 | QA-ROLE-001 | Complete browser journeys for Platform Developer, SaaS Owner, Sales Operations, trainer/facilitator and required tenant roles | Real browser login, role workspace, permitted action and denied action per role | OPEN |
| P1 | A11Y-001 | Complete authenticated workspace accessibility | axe scans, manual review of incomplete checks, keyboard and assistive-technology review across admin/manager/platform/SaaS/learner | OPEN |
| P1 | DB-REL-001 | Validate final migration chain against clean isolated DB and prepare an approved target migration plan | Clean replay, schema checks, downgrade/rollback plan; no normal app DB mutation without approval | PARTIAL — isolated chain tested to recorded head; target remains untouched |
| P1 | SEC-001 | Complete independent security review and secret scanning | Current files and Git history scanned; findings triaged; no unresolved critical/high defects | OPEN |
| P1 | OPS-001 | Prove monitoring, alert delivery, escalation and worker/queue operation | Target-like integration test, received alert and acknowledged escalation evidence | OPEN |
| P1 | DR-001 | Prove database and uploaded-file recovery | Off-host backup identifiers, restore integrity, measured RPO/RTO and rollback rehearsal | OPEN |
| P1 | PERF-001 | Measure performance against agreed workload and SLOs | Reproducible concurrency/load profile, p50/p95/p99, error rate and resource data | OPEN |
| P1 | CI-001 | Obtain hosted CI result for exact candidate | Successful hosted workflow URL and logs for exact immutable SHA | BLOCKED / cause unconfirmed |
| P1 | STAGE-001 | Deploy and verify staging | Authorized target, secrets configured by owner, TLS/ingress, migrations, worker and authenticated smoke | BLOCKED — no staging credentials/target evidence |
| P2 | EXT-001 | Verify required external providers | SMTP receipt, webhook receiver, integrations and AI provider/SLA evidence as applicable | OPEN |
| P2 | DOC-001 | Complete customer, legal and operational handoff | Customer/UAT review, support contacts, jurisdictional legal review and approved runbooks | OPEN |

## 6. Non-negotiable engineering controls

1. Preserve all existing staged, unstaged and untracked changes. No reset, clean, checkout-overwrite, stash, mass formatting or destructive cleanup.
2. Do not weaken authentication, tenant isolation, authorization, validation, audit or production fail-closed behavior to make tests pass.
3. Never seed demo fixtures into the normal application or production database. QA fixtures and credentials remain isolated and ephemeral.
4. Do not print, commit or place secrets in reports. Use secret names and redacted configuration summaries only.
5. Do not stop or reconfigure existing user services unless required, explained and approved.
6. Do not commit, push, merge, tag, publish images, apply application-database migrations, provision production operators, deploy or incur paid infrastructure without explicit user approval.
7. Each verification record must identify date/time, source SHA plus dirty-tree state, environment/database, command, exit code, result, evidence path and limitations.
8. A later failure or more restrictive acceptance record supersedes an earlier pass for the same gate unless a documented reconciliation proves the later run invalid.
9. No phase or release gate is PASS based on implementation presence, static checks alone, historical evidence or an unverified assertion.
10. Keep one active delivery queue here. Supporting reports remain evidence, not competing status authorities.

## 7. Immediate execution sequence

1. Reconcile the latest authenticated browser JSON and reports; establish which exact QA run and source/image each result belongs to.
2. Inspect the current auth/session and learner enrollment/completion flows without changing application code until the failure is reproduced and root-caused.
3. Stabilize one isolated QA stack with one explicit API origin, web origin, database, fixture seeder and browser target.
4. Fix only confirmed defects, with focused regression tests.
5. Complete the remaining role-specific browser journeys and accessibility review.
6. Re-run the complete local preflight and current-tree image/runtime checks after remediation.
7. Review and classify all working-tree changes; prepare a candidate manifest and clean review packet without discarding or silently staging existing changes.
8. Request explicit approval before creating the immutable release commit/tag or proceeding to external environments.

## 8. Authoritative supporting records

- `PHASE_NUMBERING_AND_ACCEPTANCE_RECONCILIATION_2026-10-27.md` — canonical phase mapping.
- `KALAM_REMEDIATION_REGISTER_2026-10-29.md` — technical finding history and remediation detail.
- `KALAM_AUTHENTICATED_ACCEPTANCE_2026-10-30.md` — detailed local authenticated QA evidence and limitations.
- `KALAM_ROLE_AUTHORIZATION_REMEDIATION_2026-10-30.md` — role/permission design and migration history.
- `PHASE_8_RELEASE_ACCEPTANCE.md` — release gate definitions and explicit NO-GO decision.
- `qa/api-full-suite-20261030.json`, `qa/phase8-targeted-tests-20261030.json`, `qa/phase8-image-runtime-20261030.json`, `qa/phase8-final-image-accessibility-20261030.json` — machine-readable local evidence.

**Current release disposition: NO-GO.** This register does not grant deployment or release authority.


## Execution update — 2026-10-30 (latest local verification)

This update supersedes only the applicable earlier local observations; it does not change the NO-GO release decision.

### Fresh local preflight and image smoke

- Executed `infra/scripts/phase8-preflight.ps1` against the dedicated loopback `kalam-role-test-pg` database on port 5435 with `KALAM_TEST_DATABASE_URL` explicitly scoped to `kalam_test`.
- Development and production Compose validation: PASS.
- Alembic current/head check: PASS at `b2c3d4e5f6a7`.
- API Ruff: PASS; API mypy: PASS (65 source files).
- Isolated API test suite: **224 passed, 0 failed, 0 errors**; one Starlette/httpx TestClient deprecation warning.
- Web TypeScript: PASS; ESLint: PASS; Next.js production build: PASS (89 static pages).
- Overall preflight process exited 0 after approximately 521 seconds.
- Fresh API/web/worker runtime smoke exited 0. Image digests observed in that run: API `sha256:c3f5fa12933b2b1dc74ddbb7ea1f58d322786b447a3c75a712d04c529294665a`; web `sha256:5b1971bf6965038d5a5249d2106c1df2414797fa12dad6779ce96ddbe017c152`; worker `sha256:156b4fd11a3152f9568134012b96694b6e99dcd749e1dac7bead4d0c6ad10436`. Local runtime smoke only; it explicitly does not certify integrated deployment.

### Authenticated browser evidence reconciliation

- Fresh actual frontend form submission on `http://127.0.0.1:3014` passed for Manager (`manager@demo.corp`) and Learner (`learner@demo.corp`).
- Both sessions received the `corp_lms_session` HTTP-only, SameSite=Lax cookie; Manager reached `/dashboard/team`; Learner reached `/dashboard/catalog`.
- Both roles were denied the restricted people API with HTTP 403. Evidence: `qa/authenticated-browser-role-login-workspace-20261030.json`.
- Current integrated QA container configuration was inspected: web `API_ORIGIN=http://kalam-phase8-rc-api:8000`; API `WEB_ORIGIN=http://127.0.0.1:3014`; API database is the isolated `kalam_test` service `kalam-phase8-rc-pg`. This is the approved matching origin pair for that QA stack.
- Administrator login on the same current origin was rerun using real keyboard input. Organization discovery succeeded, but the configured admin fixture identity returned HTTP 401 and no session cookie. Evidence: `qa/authenticated-browser-admin-login-3014-20261030.json`. The previous admin browser run on port 3016 is not accepted for this stack: its origin did not match the API allowlist and capability recalculation returned `Origin not allowed`.
- A separate attempt using programmatic field setters also returned HTTP 401; it is diagnostic only and is not accepted as a real-login test.
- Therefore Admin real login and capability-gap recalculation remain OPEN. The current isolated QA database's admin fixture credential/state must be safely reconciled before repeating the real browser test. Do not weaken origin enforcement or bypass authorization.
- Learner real login and catalog view are now verified. Learner self-enrollment and lesson completion persistence remain OPEN: the current accepted evidence does not yet show a successful end-to-end UI action followed by persisted enrollment status and 100% completion on this same stack.
- The earlier `authenticated-role-interactions-originfixed-20261030.json` remains a diagnostic record only: it used a different origin and records origin rejection and failed learner lifecycle actions. Preserve it; do not overwrite historical evidence.

### Current repository state

- Branch: `work/kalam-local-changes-2026-10-26`.
- Base HEAD remains `a1073cb34bc88e4e2b8cb6a41b622c908e104518`.
- Latest observed `git status --short` count: 289 paths; staged, unstaged and untracked work remains. This differs from the earlier 281-path count because additional QA evidence/scripts have been created.
- No reset, clean, stash, commit, push, merge, tag, registry publish, normal application-database migration, or deployment was performed.

### Remaining gates / disposition

| Gate | Current disposition |
|---|---|
| Manager actual frontend login + manager workspace + denied privileged API | PASS, local QA only |
| Learner actual frontend login + catalog + denied privileged API | PASS, local QA only |
| Admin actual frontend login | OPEN — current isolated QA fixture returns 401 |
| Admin capability-gap recalculation | OPEN — blocked by Admin session; do not bypass origin/authorization |
| Learner enrollment and completion persistence | OPEN — no accepted same-stack end-to-end persisted evidence |
| Other privileged roles (Platform Developer, SaaS Owner, Sales Operations, Instructor) | OPEN — role-specific browser journeys not all proven |
| Authenticated accessibility manual review / assistive technology | OPEN — automated scans and partial manual checks are not full conformance |
| Independent security review and Git-history secret scan | OPEN |
| Exact immutable candidate / independent source review | BLOCKED — dirty tree; no approved commit |
| Hosted CI for exact immutable SHA | BLOCKED — no exact immutable candidate/hosted run evidence |
| Staging deployment, TLS/ingress and migrations | BLOCKED — no authorized staging target/credentials |
| External SMTP/webhook/AI provider handshakes | OPEN — provider credentials/receivers and owner verification required |
| Monitoring alert delivery/on-call acknowledgement | OPEN — target monitoring integration required |
| Off-host backup, database + file restore, measured RPO/RTO, DR rehearsal | OPEN — target storage/backup destination and operations owner required |
| Target performance/load test | OPEN — agreed workload/SLO and target topology required |
| Customer/UAT, legal review and release sign-offs | OPEN — customer and accountable reviewers required |

**Release remains NO-GO.** Local engineering checks are materially stronger, but the unresolved authenticated workflows and all target/external/independent approval gates prevent release certification.


## Verification reconciliation — 2026-10-30 (working-tree recheck)

- Rechecked the repository without changing source or Git history. Branch remains `work/kalam-local-changes-2026-10-26`; HEAD remains `a1073cb34bc88e4e2b8cb6a41b622c908e104518`.
- Current `git status --porcelain=v1` reports **292 paths**: 56 paths with index changes, 267 with worktree changes, and 103 untracked paths (untracked paths are included in the worktree-change count). This supersedes the earlier 289-path observation above. No path was reset, cleaned, stashed, staged, committed or discarded by this recheck.
- `git diff --check` exited 0. Git emitted line-ending conversion warnings (LF may be replaced by CRLF) for working-copy files; these are warnings, not whitespace-error findings.
- `gitleaks`, `trufflehog`, `detect-secrets` and `git-secrets` are not installed on this workstation. A Git-history secret scan is therefore **not performed / OPEN**, not a pass.
- Acceptance evidence distinction: the earlier administrator capability-recalculation PASS in `PHASE_8_RELEASE_ACCEPTANCE.md` used an API-authenticated/injected browser session. It demonstrates that the page/action workflow worked under that session, but does not prove the Admin login form or the current RC fixture credential. The latest real keyboard-driven Admin login on the current matching-origin stack returned HTTP 401 and no session cookie. Therefore Admin frontend login remains OPEN; the prior session-injected workflow result is historical, scoped evidence and must not be promoted to current-stack release acceptance without rerun.
- Release disposition remains **NO-GO**. No release, deployment or destructive action was performed.


## QA fixture reset approval and execution outcome — 2026-10-30

- User explicitly approved resetting only `admin@demo.corp` in the isolated `kalam-phase8-rc-pg` / `kalam_test` QA database (host port 5436), with a temporary credential.
- The reset was **not executed**. The available remote command channel blocked the database-credential/container execution path under its safety checks. No workaround was attempted, and no password or role changes were made.
- A fresh real-keyboard learner login was attempted on `http://127.0.0.1:3014` using the existing local QA seed credential source. The login form was valid, but the API returned HTTP 401 and no session cookie. The enrollment/completion workflow was not run and no course/enrollment records were changed. Authentication failure counters or lockout metadata may have been updated by the API's normal failed-login handling; that was not independently queried.
- Evidence: `qa/learner-lifecycle-real-login-20261030.json`. This is a failed diagnostic, not a passing acceptance artifact. Earlier Manager/Learner login results remain historical evidence and do not establish that the current QA fixture credential is valid.
- Admin fixture reset, Admin real login, capability recalculation, and learner lifecycle read-back remain **OPEN**. The next safe route is a controlled, user-executed or explicitly exposed QA-only reset operation that targets exactly the administrator row and verifies the database target before commit.
- No credential value was printed or persisted by this work. No production/development database, other fixture account, source data, or Git history was modified by the attempted reset (which did not occur).


## Stabilization diagnosis and safe QA repair preparation — 2026-10-30

This section records additional read-only inspection. It does not claim that the Admin reset or functional acceptance has passed.

### Confirmed QA stack identity

The running QA API container was inspected without displaying credentials:

- Container: `kalam-phase8-rc-api`
- Runtime environment: `APP_ENV=ci`
- Allowed browser origin: `http://127.0.0.1:3014`
- Database target: service `kalam-phase8-rc-pg:5432`, database `kalam_test`
- Host database mapping: `127.0.0.1:5436`
- Matching web container: `kalam-phase8-web-final-integrated-qa-3014`, with internal API origin `http://kalam-phase8-rc-api:8000`

This confirms the intended current QA stack points to the approved isolated database and matching browser origin. It does not establish the Admin/Learner row state.

### Authentication failure diagnosis

The login handler intentionally returns the same HTTP 401 response for a missing/inactive user, an active lockout, or a password mismatch. The recent HTTP 401 therefore cannot by itself identify which condition applies. No database account row or credential hash was queried or changed during this diagnosis.

The CI fixture seeder uses `CI_FIXTURE_PASSWORD` and, when run in CI/test mode, resets multiple demo fixture users, role grants and fixture state. It is not an appropriate tool for the approved single-account repair. The browser QA runner has a separate local credential input. Separate fixture and browser credential sources can drift; this is a credible QA consistency risk, not yet a proven explanation for the current 401.

### Source/image provenance discrepancy

The currently running local images predate subsequent source-file modifications:

- API image `sha256:c3f5fa12933b2b1dc74ddbb7ea1f58d322786b447a3c75a712d04c529294665a` was created at 2026-10-30T11:13:24Z; the API container was created at 13:53:00Z. The current working-tree `apps/api/app/api/routes/auth.py` was last modified later, at 19:40 local time (14:40Z).
- Web image `sha256:5b1971bf6965038d5a5249d2106c1df2414797fa12dad6779ce96ddbe017c152` was created at 12:57:33Z. The current working-tree `apps/web/src/app/login/login-client.tsx` was last modified later, at 19:01 local time (14:01Z).

Consequently, the running browser stack is not proven to contain the latest working-tree source. Rebuild and retest after source reconciliation; do not combine current-source test results with old-image browser results as if they describe one candidate.

### Multiple local QA stacks

Several older Kalam web containers remain present on ports 3010 and 3012, alongside the current matching-origin web container on 3014. The current API is exposed on 8005. These containers were not stopped or removed. Keep acceptance tests pinned to the 3014 web container and its configured API origin until a deliberately rebuilt candidate replaces it.

### Safe single-account reset preparation

A narrowly scoped script was prepared outside the repository:

`C:\Temp\kalam_reset_admin_qa.py`

It passed Python syntax compilation. It requires a hidden-entry PostgreSQL URL that must resolve exactly to host `127.0.0.1:5436`, database `kalam_test`; verifies the connected database name; requires exactly one active `admin@demo.corp` row in tenant `demo-corporation`; prompts twice for a temporary password; and updates only that user's password hash, failed-login counter and lockout timestamp in one transaction. It does not modify activation, roles, sessions, other users, courses or enrollments, and it does not print or save the temporary password.

The script has **not** been executed. The earlier remote execution safeguard remains in force; the user must run this prepared script locally. The reset and real Admin browser login remain OPEN.

### Current remediation conclusion

No production application defect has yet been proven to explain the recent 401. The strongest confirmed blockers are inconsistent QA credential provenance and test-to-image source drift, compounded by a large mixed staged/unstaged/untracked working tree. Resolve the isolated Admin fixture, establish one credential source for all browser QA, reconcile source changes, rebuild the local images, and then repeat real login and lifecycle acceptance against those exact images.

**Release disposition remains NO-GO.**


### QA credential-input correction — 2026-10-30

The Admin real-login and Learner lifecycle browser scripts were updated to request the relevant QA password with a hidden terminal prompt instead of reading a shared plaintext password literal from `C:\Temp\kalam_browser_env.py`. The Admin and Learner scripts now request their own role-specific password at execution time. The single-account reset script also prompts for its temporary password and does not persist it.

All three scripts passed Python syntax compilation. They have not been executed against the database or browser in this update. This removes the shared local password-file dependency for future runs; it does not prove the stored account credentials are correct or clear a learner lockout.
