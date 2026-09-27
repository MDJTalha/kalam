# Kognivon — Phase 8 Release Acceptance Register

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
