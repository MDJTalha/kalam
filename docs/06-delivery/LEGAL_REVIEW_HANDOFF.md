# Kalam — Legal and Commercial Review Handoff

Status: **OPEN — legal review has not occurred**. This is a technical inventory for qualified counsel and the commercial owner, not approved customer terms or a compliance opinion.

## Product facts to verify before drafting

- Kalam supports separate organizations/tenants, user identities, role-controlled employee and learning records, assessments, credentials, compliance evidence, skills, reports and audit events.
- Customer users may upload files and export reports. The production Compose topology currently uses a local Docker upload volume; any managed object store or regional residency promise needs separately verified deployment evidence.
- Notifications, SMTP, webhooks and integrations depend on configured external services. No specific provider, delivery SLA or subprocessor inventory is approved by this file.
- Governed AI is optional and tenant controlled. Provider, model, data transfer, retention, human review and billing terms depend on the actual enabled configuration.
- Development/UAT demo accounts and sample data are not customer production records. Do not use demo identities in a live customer tenant.
- The web application currently has no dedicated public privacy, terms or cookie-policy routes in the reviewed route tree. Do not publish placeholder legal copy as final policy.

## Counsel and commercial-owner inputs

| Topic | Decision or artifact needed | Owner | State |
|---|---|---|---|
| Contracting parties and service description | Approved order form, service scope and support boundary | Commercial/legal | OPEN |
| Customer and platform data roles | Approved contract and data-processing terms for each launch market | Legal/privacy | OPEN |
| Privacy notice | Actual data categories, purposes, recipients, contact and rights workflow | Legal/privacy | OPEN |
| Retention and deletion | Per-category periods and executable export/deletion procedure | Legal/product | OPEN |
| Hosting and transfers | Selected region, infrastructure, backup locations and transfer review | Legal/operations | OPEN |
| Subprocessors | Verified list for hosting, email, monitoring, integration and enabled AI | Legal/operations | OPEN |
| Security commitments | Scope and evidence for controls, incident notice, recovery and audit requests | Security/legal | OPEN |
| AI use | Approved provider disclosures, permitted data, model/output limitations and human review | Legal/product | OPEN |
| Accessibility statements | Independently reviewed scope and remediation process | Accessibility/legal | OPEN |
| Cookie/session notice | Actual session, analytics and optional tracking inventory | Legal/web | OPEN |
| Public terms and policies | Approved, versioned text and publication/acceptance workflow | Legal/product | OPEN |
| Branding and claims | Approval for enterprise, certification, uptime and comparative market claims | Commercial/legal | OPEN |

## Technical evidence to give reviewers

- `docs/04-security-compliance/SECURITY_COMPLIANCE_BASELINE.md` — targets, data categories and explicit limits on certification claims.
- `docs/06-delivery/ENVIRONMENT_MATRIX.md` and `infra/docker/docker-compose.app.yml` — planned and local topology; verify against the actual target deployment.
- `docs/06-delivery/PHASE_8_RELEASE_ACCEPTANCE.md` — open release gates and evidence packet.
- `docs/06-delivery/PHASE_8_RELEASE_RUNBOOK.md` and `PHASE_8_ROLLBACK_RUNBOOK.md` — operational procedure drafts.
- Current provider contracts, deployment diagrams, data-retention/export implementation, incident contacts and vulnerability assessment must be supplied separately.

## Exit record

Record the reviewing counsel, jurisdictions, approved document versions, publication location, acceptance method, unresolved issues and approval date. Phase 8 legal review stays OPEN until that record and the approved customer-facing documents exist.
