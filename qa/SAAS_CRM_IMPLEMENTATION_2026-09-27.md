# Kalam SaaS CRM Implementation — 27 September 2026

## Purpose
Kognivon now has a dedicated operator-plane CRM for managing the SaaS business separately from customer tenant administration. Commercial records live under the dedicated `kalam` tenant and are protected by `saas.crm.read` / `saas.crm.manage` permissions.

## Operator-plane security
- Dedicated operations tenant: `kalam`.
- Roles bootstrapped: SaaS Administrator, Sales Operations, Sales Viewer.
- No production operator credentials were fabricated; credentials must be provisioned explicitly through the approved user process.
- Customer tenant administration remains separate from commercial CRM data.
- Public catalogue records are exposed only through explicit publication rules.

## CRM domains implemented
- CRM accounts: prospects, clients and partners.
- Contacts and primary stakeholder tracking.
- Sales ownership using real Kognivon operations users.
- Opportunities and pipeline stage/value/probability.
- Sales activity timeline: note, call, email, meeting, proposal, contract.
- SaaS plans with currency, monthly/annual prices, billing model, seat bounds, trial duration, features and public visibility.
- Offers/discounts with type, value, status, validity window and publication.
- Trials with plan, seats, dates and lifecycle.
- Subscriptions with list price, discount, server-derived net price, cycle, currency, seats, contract reference and renewal.
- Tenant provisioning from CRM account and technical tenant activation/inactivation.
- Corporate certification register with evidence and publication controls.
- Customer onboarding tasks/checklists.
- Renewal horizon.
- Marketing inquiry to CRM conversion.
- Public clients catalogue driven by approved CRM customer records.

## Public SaaS pages
- `/pricing`
- `/free-trial`
- `/contact-sales`
- `/clients`
- `/trust`

Public pricing, offers, clients and certifications are data-driven from the CRM catalogue. Empty states remain intentional until commercial or evidence records are approved.

## Internal SaaS Operations pages
- `/dashboard/saas` — executive commercial overview
- `/dashboard/saas/inquiries` — leads & inquiries
- `/dashboard/saas/clients` — account registry
- `/dashboard/saas/clients/[id]` — client 360
- `/dashboard/saas/tenants` — provisioned customer tenants
- `/dashboard/saas/pricing` — plans & offers
- `/dashboard/saas/pricing/[id]` — plan pricing/editor
- `/dashboard/saas/trials`
- `/dashboard/saas/subscriptions`
- `/dashboard/saas/onboarding`
- `/dashboard/saas/renewals`
- `/dashboard/saas/team`
- `/dashboard/saas/pipeline`
- `/dashboard/saas/certifications`

## Commercial integrity rules
- Mixed currencies are never combined into a single pipeline or subscription-value total.
- Subscription net price is derived server-side from list price minus discount.
- Discounts cannot exceed list price.
- Percentage offers cannot exceed 100%.
- Fixed-value offers must be linked to a plan/currency context.
- Offer start/end windows are validated; expired or future offers are not exposed as current public offers.
- Trial date windows and plan seat limits are enforced.
- Public client showcase requires customer lifecycle stage.
- Public certifications require registered/active status plus a registration number or verification URL.
- Expired certifications are excluded from public display.
- Certification issued/expiry windows are validated.
- Inquiry conversion is idempotent and permanently linked to its CRM account.
- Free Trial / Sales / Demo request type, requested plan and source are stored as structured fields.

## Customer onboarding
A standard checklist can be generated per CRM account:
1. Commercial scope and internal handoff.
2. Tenant provisioning and validation.
3. Administrator / identity approach.
4. People, role and organizational data readiness.
5. Required integrations and data flows.
6. Representative workflow validation / UAT.
7. Go-live readiness and operating ownership.
8. Customer success handoff and review cadence.

## Database
Current Alembic head: `z1a2b3c4d5e6`.

Recent commercial migrations:
- `v7w8x9y0z1a2_saas_commercial_crm.py`
- `w8x9y0z1a2b3_add_saas_crm_permissions.py`
- `x9y0z1a2b3c4_link_marketing_inquiries_to_crm.py`
- `y0z1a2b3c4d5_structured_marketing_inquiry_routing.py`
- `z1a2b3c4d5e6_saas_customer_onboarding.py`

## Validation
- Python compile: PASS.
- Ruff targeted CRM/marketing/model checks: PASS.
- Web TypeScript: PASS after clearing stale generated Next.js dev types.
- Focused CRM + marketing regression tests: 5 passed.
- Next.js 16.3.6 production build: PASS, exit code 0.
- Production build includes 70 application routes.

## Known follow-up work
- Provision approved Kognivon operator user credentials.
- Add invoice/payment ledger only if Kognivon will manage billing internally rather than through an external billing provider.
- Add contract/document storage and approval workflow if required.
- Add automated renewal reminders and task assignment.
- Add CRM search/filter/export and pagination for scale.
- Add account-level opportunity owner editing and richer sales forecasting.
- Add trial provisioning automation with explicit start/end dates when commercial policy is finalized.
- Add approved pricing/plan data; do not publish placeholder commercial figures.
- Add approved customers and certifications only when real evidence/authorization exists.
- Add analytics for lead source, conversion funnel, trial conversion and retention after sufficient production data exists.


## CRM Expansion — 28 September 2026

### Commercial finance layer
Implemented:
- CRM contracts with account/subscription linkage, contract reference, status, currency, value, start/end/signed dates, renewal terms and notes.
- CRM invoices with subscription/contract linkage, amount, tax, server-derived total, issue/due/paid dates and external reference.
- CRM payments with invoice linkage, amount, currency, method, reference, received/reversed status and audit history.
- Invoice reconciliation derives paid and outstanding balance from received payments.
- Payment currency must match invoice currency.
- Overpayments are rejected.
- Paid invoices cannot be voided while received payments remain.
- Payment reversal recalculates invoice status and balance.
- Contract/invoice currency is checked against linked subscription/contract context.
- Client 360 includes contracts, invoices and payments.
- Dedicated internal workspaces added:
  - /dashboard/saas/contracts
  - /dashboard/saas/billing
  - /dashboard/saas/forecast

### Forecast integrity
- Removed an older duplicate GET /crm/forecast registration by retaining the finance-aware forecast at /crm/forecast and moving the pipeline-only view to /crm/pipeline-forecast.
- Route-integrity audit confirms no duplicate SaaS CRM method/path registrations.
- Pipeline forecast remains grouped by currency and stage.
- Weighted pipeline = opportunity value × manually configured probability; it is explicitly not represented as a revenue prediction.
- Receivables forecast now aggregates actual outstanding invoice balances after payment reconciliation, rather than invoice face value.

### Commercial tasks & renewal workflow
Implemented:
- Generic CRM tasks with account, subscription, owner, type, priority, status, due date and completion date.
- Tasks workspace: /dashboard/saas/tasks.
- Task filters by status and task type.
- 90/60/30-day renewal milestone generation.
- Renewal tasks are deduplicated using a stable source key so repeated generation does not create duplicates.
- Renewal milestones inherit the CRM account owner when available.
- Renewals workspace now exposes a Generate renewal tasks action and a link to renewal tasks.
- SaaS Operations overview now surfaces open tasks, overdue tasks and overdue invoice counts.

### Operational UI safeguards
- System-reconciled invoice statuses (paid, partially paid, overdue) are not presented as manually editable states.
- Payments can be explicitly reversed through CRM; reversal is audited and immediately reconciles the linked invoice.
- Client, contract, billing, forecast, task and renewal workflows remain isolated inside the Kognivon operations tenant.

### Database
Current Alembic head: b3c4d5e6f7g8.

New migrations:
- a2b3c4d5e6f7_saas_contracts_billing.py
- b3c4d5e6f7g8_saas_crm_tasks.py

### Validation — 28 September 2026
- Python compile: PASS.
- Ruff targeted CRM/model/test checks: PASS.
- Web TypeScript: PASS.
- Focused SaaS CRM + marketing regression tests: 7 passed.
- Finance regression covers:
  - server-derived invoice totals,
  - currency mismatch rejection,
  - partial payment reconciliation,
  - overpayment rejection,
  - paid invoice reconciliation,
  - payment reversal,
  - void protection while payments exist,
  - outstanding receivables forecast.
- Renewal regression covers deduplicated 90/60/30-day task generation.
- SaaS route duplicate audit: NO_DUPLICATES.
- Next.js 16.3.6 production build: PASS, exit code 0.
- Production build generated 75 pages/routes.
- Local API /docs: HTTP 200.
- Local public pages /, /pricing, /free-trial, /contact-sales, /clients and /trust: HTTP 200.
- Frontend dev server restored on port 3000 after production build.


## CRM verification and billing hardening — 28 September 2026

- Consolidated active finance endpoints under `saas_commercial`; `/crm/finance/overview` remains available. SaaS method/path registration audit reports no duplicates.
- Issued invoices require a positive amount; invoice statuses paid/partial/overdue are server-derived and cannot be set directly.
- Draft/void invoices cannot accept payments; paid invoices cannot return to draft or be reduced below received payments.
- Payment restoration checks invoice state and remaining balance. Invoice rows are locked during invoice/payment mutations to serialize balance decisions in PostgreSQL.
- Clients CSV export moved to `/api/v1/saas/crm/export/accounts.csv`, avoiding collision with account detail routing. Export follows search and stage filters; text fields escape spreadsheet formula prefixes.
- Finance regression checks invoice/payment reconciliation, rejected transitions, account/invoice display labels, export routing and filters. CRM + marketing focused suite: 7 passed. TypeScript check, targeted Ruff, and SaaS route uniqueness: passed.

### Operational dependencies before production CRM sign-off
- Provision named Kognivon operations users and approve actual plans, prices, offers, clients and certification evidence. Demo records remain isolated and must not be represented as production customers.
- Confirm billing provider, tax and invoicing rules, legal approval for contracts and public client testimonials, and trial provisioning policy. These require owner-approved inputs; no placeholder commercial figures were published.
- Validate production deployment, role boundaries, cross-tenant access, backup/restore and full release gates as part of Phase 8. Local CRM regression passing is not a production release approval.

- Broader API regression (`python -m pytest tests -q`): 112 passed in 105.40 seconds on 28 September 2026.


## Audit remediation — 28 September 2026

- Demo CRM can no longer list, provision or change shared customer tenants. Operators can change technical status only for customer tenants linked to their operations CRM; operations and demo tenants are excluded.
- Account creation and editing reject links to operations/demo tenants or tenants already linked to another CRM account. Subscription and onboarding tenant IDs must match the owning CRM account.
- Subscription creation validates active plan, plan currency and seat bounds, offer validity, and customer tenant association. Selected offer discounts are derived server-side; negotiated discounts remain available without an offer. Plan edits revalidate seat bounds.
- Active trial status requires a current start/end window and an active provisioned customer tenant. Scheduled trials remain available for commercial review.
- Inquiry conversion now stores the resolved requested plan on new accounts. Public offers linked to hidden or inactive plans are excluded.
- Regenerating renewal tasks refreshes open milestones after a subscription renewal date changes; completed tasks retain their history.
- Added regression coverage for demo tenant access, tenant linkage, plan/offer/subscription validation, active trial activation, and renewal date refresh.

### Further work
- Configure reviewed production plans, legal/customer publication approval, named operations roles, automated renewal scheduling, and scalable pagination after commercial policy and operations ownership are defined.
- Phase 8 deployment, recovery and external provider gates remain independent of this local CRM remediation.

- Direct tenant linking now requires the tenant provenance to identify the same CRM account. New accounts obtain a customer tenant through the provision-tenant workflow; adoption of existing external tenants needs a separately governed workflow.
- Final API regression after remediation: 113 passed; SaaS route uniqueness, Ruff and web TypeScript checks passed. Focused security/commercial regression after the provenance guard: 5 passed.


## Renewal automation and account scale — 28 September 2026

- Moved renewal milestone reconciliation into a shared service used by the manual CRM action and the production worker. The worker runs it once per normal cycle for the configured active operations tenant. A PostgreSQL transaction advisory lock serializes overlapping manual and scheduled runs; stable source keys prevent duplicate 90/60/30-day tasks. Open tasks follow changes to the subscription renewal date; completed tasks retain their history.
- Added a tenant-scoped, database-paginated account endpoint with search and lifecycle filters, a total count, and a maximum page size of 100. The Clients workspace displays 25 records per page with previous/next navigation. CSV export continues to use the active filters.
- Validation: focused CRM, marketing and worker tests 9 passed; full API suite 119 passed (one upstream Starlette deprecation warning); targeted Ruff, web TypeScript, and SaaS route uniqueness checks passed.
- The first host test command used system Python and stopped at import because it lacked `joserfc`; rerunning with `apps/api/.venv/Scripts/python.exe` completed successfully. This was an environment selection issue.
- The running production worker image needs a normal build/deploy to execute these source changes. This source-level validation does not establish live production behavior.

### Remaining decision and release gates

- Approve named operations users and the final plan, price, offer, trial and publication policies. Public customer names and certification claims require real authorization/evidence.
- Confirm billing provider, tax treatment, contract approval, and whether external tenant adoption is permitted and how it is verified. No placeholder commercial records were published.
- Run release deployment, role-boundary checks, worker observation, and backup/recovery gates before production sign-off. Other CRM lists may still need pagination as record volumes grow.


## Subscription register pagination — 28 September 2026

- Added `/api/v1/saas/crm/page/subscriptions` with operations-tenant isolation, optional account/status filters, total count, stable ordering and a maximum page size of 100. The Subscriptions workspace now renders 25 entries per page and retains status filters during navigation. The existing list endpoint remains available to dependent workflows.
- Regression checks include filtered first and empty next pages. Focused CRM/worker tests: 6 passed. Targeted Ruff and SaaS route uniqueness: passed. Web TypeScript: passed after fixing a union-prop narrowing error in `public-button.tsx` encountered during validation.
- Remaining scale work includes pagination of tasks, invoices, contracts and select controls that currently request complete account lists. Production deployment and approval gates above still apply.


## Task queue pagination — 28 September 2026

- Added a tenant-scoped `/api/v1/saas/crm/page/tasks` endpoint with status, task type, owner and account filters; stable order; total count; and a 100-record maximum page size. Database aggregates supply open, due-soon, overdue and completed counts over the entire filtered result set, so metrics stay accurate while paging.
- The Tasks workspace now displays 25 tasks per page and preserves status/type filters during navigation. Its existing complete-list endpoint remains available to dependent workflows.
- Regression covers renewal tasks spread across two pages, filtered counts and an empty completed result. Focused CRM tests: 5 passed; targeted Ruff, web TypeScript and SaaS route uniqueness: passed.
- Other finance registers and large account selectors still use complete lists; publication and production deployment gates remain open.


## Contract register pagination — 28 September 2026

- Added tenant-scoped `/api/v1/saas/crm/page/contracts` with account/status filters, stable ordering, total count and a maximum page size of 100. Database aggregates provide signed/active, expiring within 90 days, and draft/review counts over all matching records.
- The Contracts workspace now shows 25 contracts per page, status filtering and navigation that retains the filter. The existing list endpoint still serves dependent billing forms.
- Focused CRM regression tests: 5 passed, including count/filter/page checks for a new contract. Web TypeScript, targeted Ruff and route uniqueness: passed. Full API suite: 119 passed (one Starlette deprecation warning).
- Billing invoices/payments and large form selectors remain scale gaps. Contract approval policy and deployment observation still need owner-approved decisions and release checks.
