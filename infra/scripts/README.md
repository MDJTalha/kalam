# Infrastructure scripts

- `backup-postgres.ps1`: creates a PostgreSQL custom-format backup from the Compose database.
- `backup-uploads.ps1`: archives a named upload volume read-only and writes a size/count/SHA-256 manifest. Pass the exact volume name; the script does not infer or modify application data.
- `verify-uploads-backup.ps1`: validates the manifest and archive, rejects unsafe paths and non-file entries, and extracts into a disposable local directory to check file count.
- `verify-postgres-restore.ps1`: refuses to overwrite an existing database, restores into a unique verification database, checks Alembic revision and tenant/user/course row counts, and removes only its own temporary database.
- `phase8-preflight.ps1`: runs local release-readiness checks across Compose, migration heads, API static analysis/tests and web quality gates. Restores caller environment/location afterward and builds in `.next-phase8-preflight` so a live Next development server retains its own output.
- `phase8-gateway-smoke.ps1`: checks gateway/web status, security headers, internal API readiness, migration exit, and running image IDs. Supply `-ExpectedApiImage` and `-ExpectedWebImage` to fail on stale deployed images.
- `phase8-monitor-probe.ps1`: emits JSON gateway/API health with persistent failure counts, warning/critical exit codes, and recovery reset. Run once per minute with a persistent state path; connect its output to a target-environment alert transport.
- `phase8-image-runtime-smoke.ps1`: boots the built API and web images in isolated disposable containers, checks production API guards and key web routes, and removes both containers. CI runs it after the image build; it does not certify integrated deployment.

Backup/restore verification should be executed before a production release and periodically as part of disaster-recovery evidence.
