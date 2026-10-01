# Kognivon Task 18 — Database and Domain-Model Audit

Date: 2026-09-29
Status: Complete

## Audit scope

- Tenant, user, role, organization, learning, assessment, capability, development, compliance, notification, support, AI, interoperability, and SaaS CRM relationships.
- Foreign-key ownership and delete behavior.
- Tenant-scoped uniqueness and lifecycle constraints.
- Query-supporting indexes and ORM/migration alignment.
- Alembic migration chain, seed alignment, and current database head.

## Findings and changes

- The domain model consistently represents tenant ownership on LMS and CRM records, with scoped uniqueness for users, roles, courses, skills, programs, plans, offers, CRM accounts, contracts, invoices, and generated tasks.
- Foreign keys use deliberate cascade, restrict, or set-null behavior for the main lifecycle relationships.
- Alembic had drifted from the ORM metadata: several foreign-key indexes declared by `index=True` were missing from the database migration history, while five older indexes existed in the database but were not declared in the ORM metadata.
- Added migration `i5j6k7l8m9n0_reconcile_domain_indexes.py` for the missing CRM/AI indexes.
- Restored the five retained index declarations on `Notification`, `MarketingInquiry`, and `SupportCase` so future schema checks do not attempt to remove them.

## Verification

- Local database upgraded to Alembic head `i5j6k7l8m9n0` — passed.
- `alembic check` — passed with `No new upgrade operations detected`.
- Migration head check — passed.
- Targeted tenant-isolation regressions — 2 passed.
- Python compilation — passed.
- Web typecheck — passed previously in this hardening cycle.
