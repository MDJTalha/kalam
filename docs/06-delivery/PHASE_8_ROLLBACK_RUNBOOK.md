# Phase 8 — Rollback and Recovery Runbook

## Rollback triggers
Rollback is initiated for data-integrity risk, authentication outage, cross-tenant exposure, sustained readiness failure, severe performance regression, migration incompatibility, or another Critical/High release defect.

## Application rollback
1. Stop new deployment traffic at the ingress/load balancer.
2. Preserve logs and current container state for incident evidence.
3. Re-deploy the previous known-good application images.
4. Do not downgrade the database automatically.
5. Validate API liveness/readiness and authenticated smoke before restoring traffic.

## Database rollback/recovery
Schema downgrades are not assumed safe. If the release migration is destructive or incompatible:
1. Stop application writes.
2. Restore the pre-release verified backup into an isolated recovery database first.
3. Validate `alembic_version`, row counts for critical tenant/auth/course tables, and application smoke against recovery data.
4. Promote recovery only through the target environment's controlled database-recovery procedure.
5. Record data-loss window and incident timeline.

## Queue/cache recovery
Valkey is treated as operational state, not the source of truth. Restart/rebuild it only after PostgreSQL health is established. Confirm worker retry behavior and dedupe protections before resuming processing.

## File-content recovery
The production upload volume/object store must be backed up independently of containers. For a Docker volume, use `backup-uploads.ps1` and `verify-uploads-backup.ps1` before release; store the archive and SHA-256 manifest outside the host's failure domain. The verification script only tests isolated extraction and does not promote files to a live volume. After controlled recovery, validate metadata-to-object consistency and malware scan status for representative files.

## Post-rollback
Open an incident record, preserve evidence, identify root cause, update tests/runbooks, and require a fresh full release gate before redeployment.
