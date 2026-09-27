# Phase 8 — Production Release Runbook

## Preconditions
1. Main branch green in CI.
2. Release candidate commit/tag identified and immutable.
3. Production environment variables injected from the deployment secret store.
4. Database backup and upload-volume/object-storage backup completed; both restore verifications are current, and their backup identifiers and checksums are recorded.
5. SMTP, webhook, integration and AI-provider credentials validated for the target environment where enabled.
6. TLS certificate/managed ingress is healthy.
7. On-call owner and rollback decision owner are named.

## Preflight
Run `infra/scripts/phase8-preflight.ps1` from the repository root. Do not deploy if any gate fails.

## Deployment sequence
1. Pull/build API, web and dedicated worker images for the exact release commit; verify the worker image packages the course-reminder, compliance, email, webhook and report-scheduler jobs.
2. Run the one-shot migration service and require successful completion.
3. Start API and require `/api/v1/health/live` and `/api/v1/health/ready` to pass.
4. Start the dedicated worker image and verify its container stays running, then check a controlled worker-cycle result and job failure/retry signals. Do not use a demo seed or real outbound recipients for a production smoke.
5. Start web, then gateway.
6. Run `infra/scripts/phase8-gateway-smoke.ps1` with the target gateway URL, API/worker/migration container names, and expected API/web/worker image IDs. Require gateway/web status, security headers, API readiness, running worker, migration exit and exact images to pass. Store the JSON output as release evidence.
7. Run authenticated smoke covering login, dashboard, catalog, learner journey, manager/team, reports, settings and governed AI when enabled.
8. Run `python infra/scripts/phase8_security_smoke.py --gateway <public-gateway-url> --api <reachable-internal-api-url> --web-origin <public-web-origin> --output <evidence-path>` from an approved environment. Require every check to pass; inspect security headers again at the actual TLS ingress. The script exercises anonymous access, origin/host denial, and CORS; it does not certify tenant isolation or the TLS configuration.
9. Verify upload + malware scan with a clean test file.
10. Verify notification/email, webhook and configured integration handshakes.
11. Observe logs/alerts for the agreed stabilization window before declaring release complete.

## Release evidence
Capture: commit/tag, migration head, API/web/worker image digests, deployment timestamps, health/readiness and worker-job results, smoke results, backup identifier, restore-verification timestamp, external dependency checks, and approver.

## No-go conditions
- Migration failure or drift.
- Readiness failure.
- Any Critical/High unresolved defect.
- Failed backup/restore verification.
- Authentication/session regression.
- Cross-tenant isolation failure.
- Malware scanning unavailable when uploads are enabled.
- External dependency required for the release is not certified.
