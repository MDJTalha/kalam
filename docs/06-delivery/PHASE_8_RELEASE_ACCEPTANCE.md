# Kalam — Phase 8 Release Acceptance Register

Status: **OPEN — production/commercial release not approved**
Basis: `DELIVERY_ROADMAP.md`, `IMPLEMENTATION_STATUS.md`, `PHASE_8_PROGRESS_EVIDENCE.md`, security baseline and QA strategy.
Rule: Mark a gate PASS only after its artifact, target environment, date and accountable reviewer are recorded. A local smoke result cannot stand in for a production target check.

| Roadmap requirement | Current evidence | Remaining acceptance evidence | State |
|---|---|---|---|
| Production deployment | Compose topology, image builds, local gateway smoke | Current API/web/worker images deployed with migrations, worker-cycle and authenticated smoke in target | OPEN |
| Monitoring | Readiness/liveness and local probe behavior | Worker/queue checks, centralized logs, alert delivery and on-call acknowledgement in target | OPEN |
| Backups | Local PostgreSQL and upload-volume archives with checksums | Scheduled off-host backups for both data classes, retention and immutable identifiers | OPEN |
| Restore verification | Isolated local database/file drills | Separate target restore, integrity/metadata checks, measured RPO/RTO and owner sign-off | OPEN |
| Disaster recovery | Rollback and recovery runbook | Target rollback rehearsal and incident/tabletop record | OPEN |
| Security verification | Local API/security regression and header/CORS smoke | Independent review, target TLS/host/origin checks, secret/dependency findings and tenant-boundary E2E | OPEN |
| Accessibility verification | 26 local route/viewport axe checks without reported violations | Remaining routes, manual incomplete rules, keyboard and assistive-technology checks against candidate | OPEN |
| Performance testing | Local development smoke with idle rerun | Agreed workloads, target topology, concurrency, p95/error thresholds and bottleneck evidence | OPEN |
| Customer documentation | `CUSTOMER_ADMIN_GUIDE.md` draft, operations and deployment runbooks | Customer/UAT review, support contacts and target-specific onboarding details | OPEN |
| Release procedures | Preflight, CI configuration, image smoke, release and rollback runbooks | Hosted CI run, exact release tag, approvals and full target execution log | OPEN |
| Legal document review | `LEGAL_REVIEW_HANDOFF.md` inventory | Jurisdiction-specific counsel review and approved customer/public documents | OPEN |

## Cross-cutting no-go checks

- Zero unresolved Critical/High defects; no authentication, tenant isolation or file-access regression.
- Production credentials and external services are tested in the actual target; local demo evidence never substitutes for these.
- Database and uploaded-file restores are both proven, and release/rollback decision owners are named.
- Public HTTPS, certificate, redirect, HSTS, ingress exposure and monitoring alert delivery are verified externally.
## Evidence packet for each candidate

Record without placing secrets in the repository:

| Field | Required record |
|---|---|
| Candidate | Commit/tag, build timestamp, API/web/worker image digests and migration revision |
| Target | Environment identifier, topology, endpoint, ingress and data-region decision |
| Automated gates | Hosted CI URL/result, preflight log, API/security/web suites, dependency review |
| Business journeys | Learner, manager, L&D, instructor, compliance, report and admin acceptance |
| Accessibility | Automated and manual findings, affected versions, reviewer and dispositions |
| Performance | Dataset, users/load profile, latency/error/resource measures, reviewer |
| Recovery | Database and file backup IDs/checksums, restore times, integrity checks and rollback drill |
| External providers | SMTP mailbox receipt, webhook receiver, integration handshakes, AI provider when enabled |
| Operations | Alert delivery/on-call acknowledgement, logs, incident contact, stabilization window |
| Approval | Product, engineering, security, operations, accessibility and legal decisions |

The approver records PASS/FAIL for each gate, the linked evidence and any exception authorized through change control. An exception cannot waive a Critical/High defect or mandatory data-recovery/security gate. Commercial launch is permitted only after all applicable gates pass and the release decision is signed.


## Local verification addendum — 2026-10-30

The current Kalam working tree has the following locally verified evidence:

- Dedicated PostgreSQL test database at loopback port 5435 is at Alembic head `b2c3d4e5f6a7`.
- Full API suite: 224 passed, 0 failed, 0 errors.
- Targeted Phase 8 tenant/role/compliance/manager-scope regressions: 25 passed, 0 failed, 0 errors.
- API Ruff and mypy passed; web TypeScript and ESLint passed.
- Isolated Next.js production build passed with 89 static pages generated.
- `infra/scripts/phase8-preflight.ps1 -SkipTests -SkipBuild` passed development Compose validation, production Compose validation, migration-head verification, API Ruff/mypy, web TypeScript and web ESLint.
- Browser pre-authentication checks passed for tenant discovery, responsive login rendering at 390/768/1440px, and unauthenticated dashboard redirect. Authenticated browser workflows remain unverified.

Machine-readable evidence is stored in:
- `qa/api-full-suite-20261030.json`
- `qa/phase8-targeted-tests-20261030.json`
- `qa/kalam-owner-browser-preauth-20261030.json`

**Release state remains OPEN.** These local results do not replace hosted CI for the exact immutable candidate, authenticated role-based browser acceptance, independent security review, target deployment, alert delivery, off-host backup/restore, disaster recovery, performance, accessibility manual review, legal approval or signed release authorization. No commit, tag, push, merge or deployment is implied by this addendum.


### Current-tree API/web/worker image runtime smoke - 2026-10-30

Fresh local QA images were built from the current Kalam working tree (branch `work/kalam-local-changes-2026-10-26`, base commit `a1073cb`; working tree remains dirty):

| Image | Local tag | Image digest |
|---|---|---|
| API | `kalam-api:qa-20261030` | `sha256:779df2d0056854245ea331d0928d4fddaff5b111a7c933c4e7d5f0319ae7381b` |
| Web | `kalam-web:qa-20261030` | `sha256:c7ce4b37d19f24bdc7ec9d5af994cf2e45f03f2d4725a7856d75c38ee28f1f63` |
| Worker | `kalam-worker:qa-20261030` | `sha256:156b4fd11a3152f9568134012b96694b6e99dcd749e1dac7bead4d0c6ad10436` |

The first web prebuilt-runner smoke exposed a packaging issue specific to the alternate QA output directory: Docker's ignore rules excluded the standalone `node_modules` tree. Added narrow `.dockerignore` exceptions for `.next-phase8-final/standalone` and `.next-phase8-final/static`, rebuilt the web image, verified `require.resolve('next')` inside the image, and reran the smoke successfully.

Runtime smoke result:

- API liveness: HTTP 200.
- API readiness without external dependencies: HTTP 503 as expected.
- API docs: HTTP 404 (disabled).
- Web routes `/`, `/login`, `/dashboard`: HTTP 200.
- Worker required job entry points: present.
- Smoke containers used `--network none` and a 256 MB memory limit.
- Script output explicitly records `integrated_deployment_certified: false`.

Production dependency checks:

- `npm audit --omit=dev`: 0 vulnerabilities.
- `pip-audit -r requirements-prod.txt`: no known vulnerabilities found; pip-audit logged cache deserialization warnings but exited successfully.

Machine-readable evidence: `qa/phase8-image-runtime-20261030.json`.

These images are local QA artifacts from a dirty working tree. They are not a release candidate, have not been pushed to a registry, and have not been deployed.


### Production-mode web security headers - 2026-10-30

A fresh local production-mode web image container was queried directly (network isolated, 256 MB limit). All seven assertions passed:

- Strict-Transport-Security present.
- Production Content-Security-Policy omits `unsafe-eval`.
- `X-Frame-Options: DENY`.
- `X-Content-Type-Options: nosniff`.
- `Referrer-Policy: strict-origin-when-cross-origin`.
- `Cross-Origin-Opener-Policy: same-origin`.
- `Cross-Origin-Resource-Policy: same-origin`.

This validates the headers emitted by the local production-mode web image. It does not verify public ingress TLS, HSTS behavior at the actual domain, proxy overrides, or a deployed target.


### Container runtime identity inspection - 2026-10-30

The freshly built local QA images declare non-root runtime users:

- API: `app` (working directory `/app`).
- Web: `nextjs` (working directory `/app/apps/web`).
- Worker: `app` (working directory `/app/worker`).

The API smoke container also ran with a read-only root filesystem and a bounded temporary filesystem, as configured by the runtime smoke script. All temporary QA smoke containers were removed after checks; no smoke containers remain running.


### Final web accessibility remediation and production image verification - 2026-10-30

The homepage accessibility review found a public mobile navigation toggle whose `aria-controls` referenced a panel rendered only while open. Removed that dangling reference; the toggle retains its accessible name and `aria-expanded` state. The homepage capability illustration wrapper was also changed from a generic `div` to a labelled `section`.

After those changes:

- Web TypeScript typecheck: passed.
- Web ESLint: passed.
- Next.js production build: passed; 89 routes generated.
- Final web image rebuilt: `sha256:c7ce4b37d19f24bdc7ec9d5af994cf2e45f03f2d4725a7856d75c38ee28f1f63`.
- API/web/worker runtime smoke rerun: passed; web routes `/`, `/login`, `/dashboard` returned HTTP 200; API liveness 200; docs 404; worker job entry points packaged.
- Production web security-header assertions: all seven passed.
- axe-core WCAG 2.0 A/AA, 2.1 A/AA and 2.2 AA scan on final production image:
  - `/login`: 25 passed checks, zero violations, zero incomplete checks.
  - `/`: 28 passed checks, zero confirmed violations; axe marked one ARIA-value check and 43 contrast nodes as incomplete/manual review, not as confirmed failures. These require manual follow-up before claiming full WCAG conformance.

The final machine-readable image and accessibility evidence is in `qa/phase8-image-runtime-20261030.json`.

This remains local verification only. The working tree is dirty; no release commit, registry push, hosted deployment, or production certification was performed.


### Homepage accessibility manual follow-up - 2026-10-30

The homepage axe scan reported no confirmed violations. It retained one ARIA attribute-value item and 43 color-contrast nodes as incomplete/manual review.

Manual investigation established:

- The aria-controls reference on .iti__selected-country resolves to #iti-1__dropdown-content while the country selector is closed. The target is a role=dialog element and becomes visible when the selector is activated. axe retains this as incomplete because it cannot conclusively evaluate the popup relationship automatically; no confirmed ARIA violation was observed.
- All 43 contrast nodes were manually evaluated against computed foreground colors and conservative combinations of computed background colors and gradient stops, including alpha compositing. All 43 met the applicable WCAG AA contrast thresholds (4.5:1 for normal text and 3:1 for large text).
- Four source-level contrast refinements were applied in apps/web/src/app/landing.module.css: hero note, capability-loop labels, demo inquiry supporting text, and the country-selector placeholder.

Post-change validation:

- npm run typecheck: passed.
- npm run lint: passed.
- npm run build: passed; 89 static routes generated.

Machine-readable follow-up: qa/homepage-accessibility-manual-review-20261030.json.

**Image alignment caveat:** the previously recorded web image digest predates these final contrast CSS refinements. Rebuild the web image and rerun production-image runtime and accessibility checks before treating this accessibility follow-up as production-image evidence. The working tree remains dirty and Phase 8 is not release-certified.

### Rebuilt Phase 8 web image — 2026-10-30

The latest source tree was built into kalam-web:phase8-final-20261030 after the homepage contrast refinements and login navigation adjustment.

- Web image digest: sha256:5b1971bf6965038d5a5249d2106c1df2414797fa12dad6779ce96ddbe017c152.
- The image contains the Next.js runtime dependency and runs as non-root user nextjs.
- API/web/worker image runtime smoke passed against this web image. API liveness returned 200; readiness returned 503 because the smoke intentionally provides no database/Redis; docs returned 404; web /, /login and /dashboard returned 200; worker job entry points were present. This is an isolated image smoke, not an integrated deployment test.
- Production security headers: 7/7 assertions passed.
- axe-core 4.13.0 against the rebuilt image: homepage 45 passes, zero confirmed violations, one ARIA-value item and 43 color-contrast nodes remain axe-incomplete/manual review; login 36 passes, zero violations and zero incomplete items. At a 390px viewport, neither route had horizontal overflow.
- The 43 homepage contrast nodes were separately assessed against current CSS in qa/homepage-accessibility-manual-review-20261030.json; all 43 were assessed as passing by the documented conservative manual calculation. This does not convert axe incomplete results into axe passes or establish full WCAG conformance.
- Machine-readable production-image accessibility evidence: qa/phase8-final-image-accessibility-20261030.json.

### Authenticated browser acceptance — 2026-10-30 (not passed)

The refreshed browser role journey is recorded in qa/authenticated-role-interactions-20261030-final.json. It is a mixed result and must not be represented as a successful role-acceptance run:

- Administrator sign-in: FAIL. The real login form did not navigate to the authenticated dashboard and no browser session cookie was observed. The administrator API login succeeded in separate API setup, but that does not validate the browser form.
- Manager team page: PARTIAL. The team page rendered and its search filter worked after an API-authenticated session cookie was injected directly into the browser. The browser login form was not exercised successfully for this role.
- Learner catalog: PARTIAL. The catalog rendered and its course query returned HTTP 200 after an API-authenticated session cookie was injected. This is not a successful learner browser sign-in.
- Learner lifecycle: FAIL. The UI enrollment action did not result in a persisted active enrollment, and lesson completion did not reach 100% progress.
- Administrator capability-gap recalculation and same-origin authenticated people lookup: FAIL/NOT VERIFIED because the administrator browser session was not established.

Do not mark authenticated role-based acceptance PASS until frontend sign-in and learner enrollment/completion are corrected and the journeys are rerun against the final image.

### Phase 8 release decision — 2026-10-30

DECISION: NO-GO — Phase 8 release certification is not granted.

Local image build, runtime smoke, production security-header assertions and automated accessibility scans are positive evidence. They do not override failed/partial authenticated browser journeys. The working tree remains dirty and is not an immutable release candidate.

Outstanding mandatory work:
1. Correct and verify real frontend authentication for administrator, manager and learner roles, including same-origin cookie handling and authenticated API calls.
2. Correct and verify learner self-enrollment and lesson completion persistence; rerun administrator capability recalculation and manager/learner journeys.
3. Re-run candidate tests/builds against the exact frozen source tree and produce a clean, reviewed immutable commit/tag and image-digest manifest.
4. Obtain hosted CI evidence for that exact candidate.
5. Verify target configuration, TLS/ingress, migrations, external integrations, monitoring/alert delivery, off-host backup and restore, disaster recovery and performance.
6. Complete accessibility manual/keyboard/assistive-technology review and required product, engineering, security, operations and legal approvals.

No commit, tag, push, merge, registry publish or deployment was performed.


### Corrected integrated browser acceptance against final web image — 2026-10-30

The earlier failed role run used an unsuitable host-run standalone web process with missing Next.js static chunks and a browser origin not allowed by the isolated API. Those failures are superseded for the checks below by a run against the actual final web image, connected to the isolated RC API/database at the API-approved origin `http://127.0.0.1:3014`.

Final web image: `sha256:5b1971bf6965038d5a5249d2106c1df2414797fa12dad6779ce96ddbe017c152`.
Integrated QA API image: `sha256:c3f5fa12933b2b1dc74ddbb7ea1f58d322786b447a3c75a712d04c529294665a`.

Verified results:

- **Administrator real frontend login: PASS.** A real browser keyboard-input test populated the login form and submitted it. The frontend login request returned HTTP 200, navigation reached `/dashboard`, and the browser received the HttpOnly `corp_lms_session` cookie.
- **Administrator same-origin authenticated people lookup: PASS.** The browser-side same-origin `/api/v1/people/page` request returned HTTP 200 with the four isolated QA people records.
- **Administrator capability recalculation: PASS.** The capability-gaps page rendered, the Recalculate action was activated, and the UI displayed “Capability gaps refreshed using the governed Phase 4 calculation.”
- **Manager team workspace: PASS with session-method limitation.** The team page rendered and the direct-report search interaction completed. This run injected an API-authenticated session cookie into the browser; it did not independently validate the manager frontend login form.
- **Learner catalog: PASS with session-method limitation.** The catalog returned HTTP 200 and displayed 13 published courses. This run injected an API-authenticated session cookie; it did not independently validate the learner frontend login form.
- **Learner self-enrollment and lesson completion: PASS with session-method limitation.** In the browser UI, self-enrollment produced the confirmation message and persisted status `enrolled`. Completing the lesson produced the completion message; the API read-back confirmed status `completed`, one completed lesson and 100% progress. The learner browser session was API-authenticated rather than established through the learner login form.

Machine-readable evidence:

- `qa/authenticated-browser-login-final-image-approved-origin-20261030.json`
- `qa/authenticated-role-interactions-final-image-20261030-approved-origin.json`
- `qa/phase8-final-image-authenticated-acceptance-20261030.json`

This corrects the earlier broad statement that the administrator browser login and learner lifecycle were failing. It does **not** certify all three role login forms: manager and learner frontend sign-in still need direct browser verification. The acceptance evidence is local QA only, against the stated local image digests and isolated CI data.

### Updated release decision — 2026-10-30

**DECISION: NO-GO — Phase 8 release certification is not granted.**

The corrected local browser evidence materially closes the administrator login, administrator capability recalculation, manager team interaction, learner enrollment and lesson-completion test cases, subject to the explicit manager/learner login-session limitation above. Remaining release blockers include:

1. Independently pass manager and learner frontend login form journeys, including cookie issuance and role-scoped same-origin API access.
2. Reconcile and rerun the complete required test suite against the exact final source/image candidate; retain unambiguous test-to-digest provenance.
3. Freeze and independently review a clean immutable source candidate; the working tree is currently dirty.
4. Obtain hosted CI and hosted staging evidence for that exact candidate.
5. Verify production target configuration, TLS/ingress, migrations, external integrations, monitoring and alert delivery, off-host backup/restore, disaster recovery and performance.
6. Complete outstanding accessibility manual/keyboard/assistive-technology review and required product, engineering, security, operations and legal approvals.

No commit, tag, push, merge, registry publish or deployment was performed. The local QA containers and isolated database are not a production environment.


## Latest execution reconciliation — 2026-10-30

The master delivery register `KALAM_MASTER_DELIVERY_REGISTER_2026-10-30.md` is the current status index. This addendum records the latest same-day acceptance evidence and does not authorize release.

### Local gates now verified

- Full isolated API suite: 224 passed, 0 failed, 0 errors.
- API Ruff and mypy: passed.
- Web TypeScript, ESLint and Next.js production build: passed; 89 static pages.
- Full local Phase 8 preflight exited 0; isolated migration chain at `b2c3d4e5f6a7`.
- Fresh API/web/worker local image runtime smoke exited 0. It remains a network-isolated local smoke and records `integrated_deployment_certified=false`.
- Manager and Learner actual frontend form login on `http://127.0.0.1:3014): passed. Each received the HTTP-only session cookie, loaded its role-specific workspace, and received HTTP 403 from the restricted people API. Evidence: `qa/authenticated-browser-role-login-workspace-20261030.json`.

### Authenticated acceptance still open

- Admin login against the same current QA frontend/API stack returned HTTP 401 after successful organization discovery; no session cookie was issued. Evidence: `qa/authenticated-browser-admin-login-3014-20261030.json`.
- The current stack's configured API origin allowlist is `http://127.0.0.1:3014`. A prior Admin attempt against port 3016 returned `Origin not allowed` on a mutation and is not valid acceptance evidence for the current stack. Do not loosen the origin allowlist to make the old test pass.
- Admin capability-gap recalculation is therefore not accepted.
- Learner login/catalog are accepted locally, but same-stack UI enrollment followed by persisted enrollment status, lesson completion and 100% progress has not yet been proven. The previous failure record remains preserved; no claim of completion is made.
- Remaining role-specific journeys and full authenticated accessibility/assistive-technology review remain open.

### External release gates remain unfulfilled

No hosted CI result for an immutable candidate, independent security review, authorized staging target, public TLS/ingress verification, production migration execution, external provider receipt/handshake, monitoring alert acknowledgement, off-host backup/restore, disaster recovery rehearsal, target load/performance result, customer/UAT approval, legal review or signed release approval is recorded.

**Decision: NO-GO.** The local verification gates above are useful progress but cannot substitute for unresolved authenticated workflows, target-environment evidence or accountable release approvals. The working tree remains dirty (latest observed 289 changed paths) and no immutable release candidate exists.


## Verification reconciliation — 2026-10-30

The latest repository recheck reports 292 paths in `git status --porcelain=v1`: 56 paths with index changes, 267 with worktree changes, and 103 untracked paths (untracked paths are included in the worktree-change count); the earlier 289-path count is superseded. `git diff --check` exited 0, with Git line-ending conversion warnings only. No secret-scanning utility (`gitleaks`, `trufflehog`, `detect-secrets`, `git-secrets`) is installed, so Git-history secret scanning remains OPEN and must not be represented as passed.

The historical administrator capability-recalculation PASS earlier in this file was performed with an API-authenticated/injected browser session. It is not evidence that the Admin login form works. The latest actual keyboard-driven Admin login against the current matching-origin QA stack returned HTTP 401 and no session cookie; Admin frontend login and current-stack capability recalculation acceptance remain OPEN pending fixture reconciliation and a fresh real-login run. The historical learner lifecycle result likewise used an API-authenticated session; current same-stack learner login/catalog are verified, but a fresh same-stack end-to-end lifecycle read-back is still required before closing that gate.

**Current disposition remains NO-GO.**


## QA reset approval and fresh learner-login diagnostic — 2026-10-30

The user approved a reset limited to `admin@demo.corp` in the isolated QA database `kalam_test` on `kalam-phase8-rc-pg` (host port 5436). The reset was not executed because the remote command channel blocked the database-credential/container execution path under its safety checks. No workaround was attempted and no account/database was modified.

A fresh actual keyboard-driven learner login on `http://127.0.0.1:3014` using the existing local QA seed credential returned HTTP 401 and issued no session cookie. The learner lifecycle was therefore not attempted and remains OPEN. Evidence: `qa/learner-lifecycle-real-login-20261030.json` (failed diagnostic only). The earlier Manager/Learner login passes are historical and do not establish current credential validity.

Admin reset, Admin actual login, capability recalculation, and same-stack learner enrollment/completion remain OPEN. A controlled reset operation must verify the exact isolated database and modify only the administrator fixture row.


**Correction to the reset/login diagnostic:** no password or role changes were made and no course/enrollment records were changed. The failed learner login may have updated normal authentication failure counters or lockout metadata; this was not independently queried. This qualification supersedes any earlier wording implying that no account metadata could have changed.


## Stabilization diagnosis addendum — 2026-10-30

Read-only inspection confirmed the current QA API container uses `APP_ENV=ci`, `WEB_ORIGIN=http://127.0.0.1:3014`, and the isolated database service `kalam-phase8-rc-pg:5432/kalam_test` (host mapping `127.0.0.1:5436`). The matching web container on 3014 uses the API service origin `http://kalam-phase8-rc-api:8000`. The current 401 is therefore not explained by a mismatched configured origin or the API targeting a different database.

The authentication endpoint deliberately returns HTTP 401 for multiple conditions (unknown/inactive user, current lockout, or password mismatch). No account row was queried or changed during this inspection, so the precise cause remains unconfirmed. The CI fixture seeder resets multiple demo users and role grants using `CI_FIXTURE_PASSWORD`; it must not be used for a one-account repair. The browser runner has a separate local credential source, creating a possible credential-drift issue.

A single-account reset script was prepared at `C:\Temp\kalam_reset_admin_qa.py` and passed `py_compile`. It requires a hidden database URL for exactly `127.0.0.1:5436/kalam_test`, verifies the database identity and exactly one active Admin row, and changes only that user's password hash and lockout counters in a transaction. It has not been executed; user-local execution is required.

The currently running API and web images predate later working-tree changes to `auth.py` and `login-client.tsx`. The current browser evidence is therefore not a test of the latest source tree. Reconcile the working tree, rebuild both images from the reviewed source, and repeat role-based browser acceptance against those exact image digests.

Several older local web QA containers remain on ports 3010 and 3012; the matching-origin current QA web container is on 3014 and API is exposed on 8005. No containers were stopped or removed.

**Status remains NO-GO.** Admin reset/login, exact source-to-image candidate alignment, manager/learner fresh login and persisted learner lifecycle read-back, independent review, hosted CI/staging and production gates remain open.


### QA credential-input correction — 2026-10-30

The real Admin browser login and Learner lifecycle scripts now prompt for the respective QA password using hidden terminal input. They no longer read the shared plaintext credential literal from the temporary browser environment file. The single-account Admin reset script likewise prompts for the temporary password without printing or saving it. All three scripts passed `py_compile`; none was executed against the database or browser during this change. Credential correctness, Admin reset and learner lockout/password state remain unverified.
