# Kognivon screen-by-screen gap audit — 28 September 2026

## Scope and confidence
- Current source inventory: 84 `apps/web/src/app/**/page.tsx` screens (70 dashboard, 14 public/auth/verification).
- Reviewed the route source and shared shell/navigation; tested public GET responses at localhost:3000. Existing 27 September axe evidence covers 36 dashboard routes at two viewports, with zero reported violations but unresolved/incomplete checks. It is historical evidence, not current sign-off.
- No authenticated role-by-role visual run was performed in this audit. “QA pending” below means source review found no specific defect, not that the screen is perfect. Dynamic [id]/[code] flows and mutating actions need separate data-backed role testing.
- API tests passing do not establish UX quality or factual integrity of dashboard copy.

## Priority findings
| ID | Priority | Confirmed gap / risk | Evidence and required correction |
|---|---|---|---|
| F01 | Critical | Overview displays fabricated Recent Activity timestamps and fixed Upcoming Activity rows as operational records. | `dashboard/page.tsx` maps four hard-coded events with “hours ago” and renders scheduled/attention labels without event queries. Replace with persisted event/schedule APIs or an explicit empty state. |
| F02 | High | Overview KPI labels and readiness figures do not match the data. | “Active Learners” is enrollment count; “Programs” is course count; “Last 30 days” has no date filter. Readiness uses an arbitrary skill-gap formula and subtracts two points for “Workforce readiness.” Define governed measures and remove unsupported labels. |
| F03 | High | Several screens turn API failure/denial into zeros or an empty state. | Overview, Certificates, Development Plans and parts of Analytics use null coalescing. Distinguish empty data, 403 and service failure; do not show false zero figures. `apiJson` currently returns null for every non-2xx response. |
| F04 | High | Reports export cards remain visible even when summary access is restricted. | `dashboard/reports/page.tsx` renders People/Enrollment CSV links outside the summary permission branch. Gate links with permission and explain denied access; backend authorization remains essential. |
| F05 | Medium | Global search has no clear failed-search or zero-results state; people, skills and programs results are not actionable links. | `dashboard/search/page.tsx` renders result sections only when API returns a payload and uses plain divs for three result types. |
| F06 | Medium | Shared shell presents hard-coded workspace/environment labels and stale badges. | `dashboard-shell.tsx` says “Default workspace”; Settings says “Local development”; `workspace-nav.tsx` fetches badge counts only on mount. Derive labels from tenant/environment and refresh counts after relevant actions. |
| F07 | Medium | CRM billing loads all invoices and payments, plus complete account/subscription/contract options. | `dashboard/saas/billing/page.tsx`. Paginate both registers, keep aggregate counts independent of visible rows, and provide searchable entity selectors. |
| F08 | Medium | Other CRM registers and several LMS lists still rely on complete arrays. | Source scan: trials, onboarding, pipeline, certifications, renewals, teams, and some people/course/program lists. Add bounded server queries where volume or sensitivity warrants it. |
| F09 | Commercial gate | Public legal/privacy and approved publication content are incomplete. | No Privacy, Terms, DPA, Subprocessors or Accessibility page routes in the current inventory; public clients/certifications/plans require owner-approved real data. |
| F10 | Verification gate | Prior axe results have unresolved “incomplete” checks; no current full 84-screen role/viewport action run. | Review contrast/ARIA items manually and run keyboard, mobile, screen reader and authenticated flow tests for learner/manager/admin/CRM roles. |

## Screen matrix
“QA pending” marks the exact screen still requiring live role and action verification. “Source OK” means no specific defect was established from the source scan.
### Public, identity and verification (14)
| Screen | Finding / next check |
|---|---|
| `/` | Live GET 200. Shared header/footer now used; buyer journey and current mobile/keyboard QA pending. |
| `/pricing` | Live GET 200. Approved plan and offer data/publication gate F09; check empty catalogue and CTA routing. |
| `/guided-evaluation` | Live GET 200. Form appears only with trial-enabled plans; otherwise routes to Sales. Verify inquiry-to-CRM handoff and promised evaluation terms. |
| `/free-trial` | Permanent 308 redirect to guided evaluation. Verify every “free trial” promise/CTA matches this governed intake, not instant access. |
| `/contact-sales` | Live GET 200. Validate form failure, duplicate inquiry, mobile focus and confirmation flow with test submissions. |
| `/clients` | Live GET 200. Publication approval and genuine client evidence F09. |
| `/trust` | Live GET 200. Verify each security/certification statement against released evidence F09. |
| `/integrations` | Live GET 200. Verify stated connector availability against actual integration registry. |
| `/implementation` | Live GET 200. Validate delivery commitments with operations owner. |
| `/login` | Live GET 200. Tenant selection, invalid login, lockout and mobile role QA pending. |
| `/login/[tenant]` | Tenant-specific identity flow; test unknown/suspended tenant and SSO/password choices. |
| `/forgot-password` | Live GET 200. Token delivery, generic confirmation and invalid email QA pending. |
| `/reset-password` | Expired/used token and session invalidation QA pending. |
| `/verify/[code]` | Public certificate verification; test revoked, expired, unknown code and no personal-data overexposure. |

### Core workspace, people and learning (20)
| Screen | Finding / next check |
|---|---|
| `/dashboard` | F01/F02/F03 critical; fabricated activity and unsupported metrics must be corrected before executive use. |
| `/dashboard/help` | Source OK; generic administrator support only, no ticket channel; confirm intended support journey. |
| `/dashboard/settings` | F06 hard-coded “Local development” and raw tenant UUID. |
| `/dashboard/settings/sessions` | Source OK; revoke-current/other session and multi-device UX QA pending. |
| `/dashboard/notifications` | Source OK; unread badge refresh F06; mark-read and empty/error QA pending. |
| `/dashboard/search` | F05; failed/zero results and non-linkable person/skill/program matches. |
| `/dashboard/people` | Permission guard exists; verify directory pagination and profile navigation at scale F08. |
| `/dashboard/people/[id]` | Profile access and cross-tenant/role UI QA pending. |
| `/dashboard/people/admin` | Search/filter present; bulk user lifecycle and permission denial QA pending. |
| `/dashboard/team` | Manager visibility and assignment scope QA pending. |
| `/dashboard/manager` | Alias redirect to `/dashboard/team`; no separate screen. |
| `/dashboard/manager/[id]` | Direct-report authorization and development actions QA pending. |
| `/dashboard/organization` | Unit hierarchy and permission-restricted edits QA pending. |
| `/dashboard/catalog` | Explicit unavailable state exists; course list scale F08 and learner enrollment QA pending. |
| `/dashboard/catalog/[id]` | Player/progress, capacity and prerequisite states QA pending. |
| `/dashboard/catalog/[id]/studio` | Editor route; draft/publish and version restore QA pending. |
| `/dashboard/catalog/categories` | Taxonomy create/edit permission and empty/error QA pending. |
| `/dashboard/catalog/new` | Course-create permission, validation and unsaved data QA pending. |
| `/dashboard/course-studio` | Authoring list scale F08; role-gated publishing QA pending. |
| `/dashboard/course-studio/[id]` | Module/lesson/file version and scanner failure QA pending. |
### Assessment, capability, L&D and evidence (24)
| Screen | Finding / next check |
|---|---|
| `/dashboard/assessments` | F03: failed assessment API is shown as “No assessments”; distinguish failure from a true empty library. |
| `/dashboard/assessments/[id]` | Timer, autosave/submit and attempt-limit role QA pending. |
| `/dashboard/assessments/admin` | Question bank and create validation QA pending. |
| `/dashboard/assessments/admin/[id]` | Locked-after-attempt editing, grading and version rules QA pending. |
| `/dashboard/assessments/admin/[id]/attempts` | Answer-key secrecy and audit review QA pending. |
| `/dashboard/certificates` | F03: failed API is coerced to empty issued list and zero metrics. |
| `/dashboard/certificates/admin` | Issue/revoke/branding controls and expiry QA pending. |
| `/dashboard/compliance` | Error alert exists; obligations and policy lists can still show empty wording below it. Review mixed state and action outcomes. |
| `/dashboard/compliance/admin` | Dense policy/assignment/evidence/exception workflow; verify role, validation and keyboard flow. |
| `/dashboard/skills` | Null/zero distinction and learner skill-gap evidence QA pending F03. |
| `/dashboard/skills/admin` | Role skill framework, mapping validation and effective-date QA pending. |
| `/dashboard/development` | F03: unavailable plans become empty arrays and zero goals. |
| `/dashboard/learning-paths` | Explicit service-unavailable state exists; publication and list scale QA pending. |
| `/dashboard/learning-paths/new` | Draft path authoring and unsaved change QA pending. |
| `/dashboard/learning-paths/[id]` | Prerequisite progression and manager assignment QA pending. |
| `/dashboard/programs` | Partial API failure alert exists but KPI tiles still show zero; avoid conflating missing data with zero F03. |
| `/dashboard/programs/[id]` | Program course ordering, required status and cohort relationships QA pending. |
| `/dashboard/programs/cohorts/[id]` | Capacity, attendance and membership permission QA pending. |
| `/dashboard/ld-operations` | Queue pagination exists; approval/denial bulk scope and long-query UX QA pending. |
| `/dashboard/ld-operations/equivalencies` | Equivalency rules and course-mapping authorization QA pending. |
| `/dashboard/sessions` | Attendance roster and facilitator scope QA pending. |
| `/dashboard/instructor` | Alias redirect to Sessions; no separate screen. |
| `/dashboard/instructors` | Alias/entry behavior to verify; not a distinct workflow in route inventory. |
| `/dashboard/files` | Scan state, file access and failed upload QA pending. |
### Analytics and platform administration (8)
| Screen | Finding / next check |
|---|---|
| `/dashboard/analytics` | F03: nine independent API reads fall back to zero/empty without a page-level partial-failure state; verify metric provenance and date windows. |
| `/dashboard/reports` | F04 export actions visible after denied summary; report page also promises “Phase 6 Reports workspace” measures not shown here. |
| `/dashboard/ai` | F03: AI status failure is replaced with “Not configured,” which may misstate a service outage. Review prompt/review authorization. |
| `/dashboard/admin` | Role, tenant setting and organization edit audit/denial QA pending. |
| `/dashboard/admin/inquiries` | Lead assignment, duplicate/qualification and conversion role QA pending. |
| `/dashboard/audit` | Search/export retention and sensitive metadata display QA pending. |
| `/dashboard/integrations` | Test-connection, secret masking and failure/retry QA pending. |
| `/dashboard/webhooks` | Delivery history, secret rotation and webhook retry UX QA pending. |

### SaaS commercial CRM (18)
| Screen | Finding / next check |
|---|---|
| `/dashboard/saas` | Business KPIs source-backed; verify currency-separated totals, permission-specific actions and empty organization state. |
| `/dashboard/saas/inquiries` | Verify marketing-to-CRM conversion, requested plan preservation, assignment and duplicate paths. |
| `/dashboard/saas/clients` | 25-row account pagination added; form selectors still request all plans. Test page boundary and demo isolation. |
| `/dashboard/saas/clients/[id]` | Client 360 loads complete related contracts/invoices/payments; add bounded tabs when account history grows F08. |
| `/dashboard/saas/tenants` | Test linked-tenant isolation and technical status change as real operations and demo roles. |
| `/dashboard/saas/pricing` | Public visibility needs approved plan/offer figures and legal commercial policy F09. |
| `/dashboard/saas/pricing/[id]` | Validate seat bounds, currency and published plan edit against live subscriptions. |
| `/dashboard/saas/trials` | Complete-list scale F08; activation/provisioning policy requires approved dates/tenant controls. |
| `/dashboard/saas/subscriptions` | 25-row pagination added; account/plan/offer selectors still unbounded. |
| `/dashboard/saas/contracts` | 25-row pagination and aggregate counts added; contract approval/evidence workflow remains a business gate. |
| `/dashboard/saas/billing` | F07 all invoices/payments and input options load at once; test reconciliation/void/reversal UX. |
| `/dashboard/saas/renewals` | Verify scheduled worker creates/refreshes milestones in deployed environment; list scale F08. |
| `/dashboard/saas/onboarding` | Checklist generation/completion and client handoff role QA; complete-list scale F08. |
| `/dashboard/saas/tasks` | 25-row pagination and database counts added; verify owner notifications and workflow completion. |
| `/dashboard/saas/team` | Named operations users/provisioning required; demo access must remain isolated. |
| `/dashboard/saas/pipeline` | F08 complete opportunity list; validate forecast labeling and currency grouping. |
| `/dashboard/saas/forecast` | Verify weighted pipeline versus invoice receivables labels and currency grouping; keep forecasting assumptions explicit. |
| `/dashboard/saas/certifications` | F09 real registration/verification evidence and approval before public claims. |

## Recommended order and acceptance
1. **Correct Overview truthfulness (F01/F02).** Replace fabricated timelines with persisted records, remove the fake 30-day scope, map Active Learners/Programs to real distinct measures, and document readiness calculation. Acceptance: an empty tenant shows no invented activity; known fixture data reconciles with source records.
2. **Separate unavailable, forbidden and genuinely empty data (F03/F04).** Make the server API helper preserve status, render explicit retry/permission states, and hide unauthorized exports/actions. Acceptance: simulated 403 and 503 never display “0” or “No records.”
3. **Complete search and navigation behavior (F05/F06).** Add no-result/error messaging and links to authorized result details, correct workspace/environment labels, and refresh badges after actions. Acceptance: keyboard and role scenarios have predictable destinations and counts.
4. **Scale billing and remaining registers (F07/F08).** Paginate invoices/payments with database aggregate totals; replace massive selector lists with searchable bounded lookups. Acceptance: seeded 1,000+ records remain responsive and reconciliation totals match complete data.
5. **Resolve commercial/legal gates (F09).** Publish only approved plans, client references, certifications and legal pages. Acceptance: owner-approved content/evidence and link checks are attached to release record.
6. **Run current full-screen role QA (F10).** Learner, manager, instructor, tenant admin, demo admin and operations CRM personas; desktop/tablet/mobile; keyboard, screen reader, errors, empty states, mutating actions and cross-tenant access. Record screenshot, route, data fixture and pass/fail for each screen before declaring closure.

## Release judgment
The 84 routes exist, and the sampled public paths respond. The system is **not yet screen-complete or production UX signed off**: F01/F02 directly affect executive trust, while authenticated visual and action verification remains outstanding. This report identifies source-confirmed defects separately from unverified screens; it does not rate untested screens as gap-free.

## Remediation pass — 28 September 2026
- F01/F02: Rebuilt Overview around persisted enrollments, due dates, capability counts, authorized report metrics and authorized audit events. Removed fabricated timelines, unsupported readiness percentages, misleading “Last 30 days” and role-inappropriate quick actions.
- F03: Certificates, Development Plans, Assessments and Governed AI now show explicit service-unavailable states instead of false zeros/empty records. Overview uses dashes and an alert for missing core data.
- F04: Reports now hides exports when reporting access/data is unavailable.
- F05: Search now shows short-query, no-result and service-failure states; authorized people/program matches link to their details.
- Additional critical security finding: global search previously returned tenant user emails and unpublished programs to any signed-in role, and could expose private course titles. The API now gates people behind `users.read`, limits programs to published for non-managers, and uses course visibility/assigned-course checks. A learner/admin permission regression was added.
- F06: Replaced hard-coded “Default workspace” and “Local development” labels; People navigation now requires `users.read`, and navigation badges reload on route changes.
- F03 follow-up: Analytics, Programs, Compliance, Audit and Sessions now expose partial source failure; Analytics shows unavailable values as dashes and requires reporting access before fetching. Protected workforce capability data is fetched only for users with `users.read`.
- Search API also rejects whitespace-only queries. The full API suite passed (120 tests); the focused search regression passed after the whitespace change. Web TypeScript and targeted ESLint passed after the final Analytics refinement. The last typecheck also exposed a Support Operations compile error; message refresh callbacks and live response target timing were corrected, then web TypeScript and targeted ESLint passed.
- Brand identity: the repository already contains the Kognivon brand package, SVG wordmarks, app icons, metadata and the shared dashboard brand component. This is a design proposal; public/legal claims and trademark clearance remain evidence gates.
- Top-to-bottom follow-up: People now uses tenant-scoped, server-filtered 20-row pages with stable ordering, matched/tenant counts, filter-preserving navigation and a page-boundary redirect. A new permission and pagination regression passed. The unbounded people endpoint remains for other consumers and should be migrated where needed.
- Team metrics now exclude terminal compliance exceptions and count only active development plans. Teams and Organization navigation require the same users.read permission as their pages. Organization read-only guidance no longer presents an administration action; the role assignment panel distinguishes load failure from no roles.
- Learning Catalog: filter controls now use button/pressed semantics, true empty catalog copy and source-faithful descriptions. Course detail distinguishes 404 from service/access failures. Assignment-only courses no longer offer self-enrollment. Lesson content is redacted at the API until enrollment is active or the viewer has course management permission, and the player presents the approval/assignment state. The approval flow regression passed after applying the pending notification metadata migration (database advanced from g8h9i0j1k2l3 to h9i0j1k2l3m4).
- Validation this pass: People permission/pagination and manager-focused tests passed (3). Frontend TypeScript and targeted ESLint passed. API Ruff passed after the course payload correction. Full foundation suite is being run separately; no current authenticated visual role sign-off is claimed.
- Remaining: `apiJson` still collapses 403 and 5xx into null at the shared helper; more screens need tailored failure states and authenticated role/visual QA. User Administration still loads an unbounded selector list; billing/selector pagination, commercial publication and deployment gates remain open. This pass does not close the 84-screen audit.
