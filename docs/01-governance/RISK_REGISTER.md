# Corporate LMS — Risk Register

Version: 0.1
Status: Phase 0 baseline

| ID | Risk | Impact | Likelihood | Treatment | Owner |
|---|---|---|---|---|---|
| R-001 | Scope expands before core workflows stabilize | High | Medium | Phase gates and change control | Project Director |
| R-002 | Frontend outruns backend/data integrity | High | Medium | Feature Definition of Done and E2E evidence | Engineering |
| R-003 | Tenant isolation defect | Critical | Low/Medium | Server-side policy, negative tests, cross-tenant regression | Engineering/Security |
| R-004 | Demo data mistaken for production capability | High | Medium | Clear DEMO labeling and release evidence | Product/QA |
| R-005 | Migration drift | High | Medium | Alembic-only schema changes and migration checks | Engineering |
| R-006 | Integrations are assumed complete without live handshake | Medium | High | Require credentials, evidence and failure-path tests | Integrations |
| R-007 | Accessibility becomes cosmetic late in delivery | High | Medium | WCAG 2.2 AA target and repeated reviews | UX/QA |
| R-008 | AI introduced before data/permissions are mature | High | Medium | Governed Phase 7 gate; AI disabled by default | Product/Security |
| R-009 | Recovery path is never restored/tested | Critical | Medium | Restore evidence and DR runbook in Phase 8 | Operations |
| R-010 | Local tooling/process locks CI dependencies | Medium | Medium | CI-equivalent clean-run checks and environment matrix | Engineering |

Risk status is evidence-driven; changing treatment requires a controlled change record.