# ADR-007 — File/Object Storage

Status: Accepted
Date: 2026-09-24

## Decision
Abstract binary storage behind a storage service. Local filesystem storage is allowed for development; S3-compatible object storage is the production target.

## Why
The application needs private, scalable storage without coupling business logic to a specific vendor.

## Consequences
PostgreSQL stores ownership and metadata. Uploads pass MIME/size/name validation and a malware-scanning boundary. Downloads require authorization. Production URLs must not expose private objects accidentally.