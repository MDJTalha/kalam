# ADR-007 — File/Object Storage

Status: Accepted
Date: 2026-09-24

## Decision
Abstract binary storage behind a storage service. Local filesystem storage is allowed for development; S3-compatible object storage is the production target.

## Why
The application needs private, scalable storage without coupling business logic to a specific vendor.

## Consequences
PostgreSQL stores ownership and metadata. Uploads pass MIME/size/name validation and a malware-scanning boundary. Downloads require authorization. Production URLs must not expose private objects accidentally.

## Implementation contract
- `STORAGE_BACKEND=local` remains the development default. Production configuration must select `s3`.
- S3-compatible uploads are staged on the configured local quarantine filesystem, scanned before `PutObject`, and removed from staging after successful transfer.
- Downloads remain application-authorized and stream through the API; the API does not issue public object URLs.
- Configure `S3_BUCKET`, `S3_REGION`, and optionally `S3_ENDPOINT_URL`. Static credentials are optional for workload identity, but if used both access key and secret are required. Never commit credentials.
- Bucket privacy, encryption, versioning, lifecycle/retention, replication, and backup policy are infrastructure responsibilities and must be verified for the chosen provider before production activation.
