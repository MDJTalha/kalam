# Kalam S3-Compatible Storage Setup

Status: implementation ready; provider account and live integration are not yet configured.

## Recommended no-card starting option

Backblaze B2 is the current recommendation for a no-credit/debit-card signup requirement. Backblaze advertises account signup without a credit card, and B2 supports an S3-compatible API. This is not a promise of unlimited free storage: review current usage limits, prices, and billing terms in the provider console before putting customer data there.

## Provider setup

1. Create/sign in to a Backblaze account and enable B2 Cloud Storage.
2. Create a **private** bucket in the region suitable for the expected users and data residency requirements. Copy the exact S3 endpoint and region shown by the provider.
3. Create a dedicated application key restricted to this bucket and only the object operations Kalam needs (upload, read/head, delete). Do not use an account master key.
4. Store these deployment values in the host's secret store or an ignored local environment file; never commit them or paste secret keys into chat:

   ```dotenv
   STORAGE_BACKEND=s3
   S3_BUCKET=<private-bucket-name>
   S3_REGION=<provider-region>
   S3_ENDPOINT_URL=https://s3.<provider-region>.backblazeb2.com
   S3_ACCESS_KEY_ID=<bucket-restricted-key-id>
   S3_SECRET_ACCESS_KEY=<bucket-restricted-application-key>
   ```

   Use the exact endpoint shown for the bucket rather than assuming the example hostname. For AWS workload identity, leave the two static credential values unset.

5. Configure a separate backup destination or at least a separate restricted backup key/prefix and retention policy. Prefer a separately administered backup bucket/account so an application-key compromise cannot erase both live data and its recovery copy. Do not enable immutable retention/Object Lock until the retention and deletion policy is approved; these settings can prevent deletion during their lock period.
6. Deploy the exact reviewed commit and verify the Compose-rendered config without printing secret values. Start a controlled test with a non-sensitive fixture: upload, confirm it is clean-scanned, download and compare SHA-256, verify cross-tenant denial, delete it, and confirm it is absent. Check that no public URL or anonymous bucket access is enabled.
7. Exercise database and upload backup to the off-host destination, restore both into an isolated target, record checksums and restore time, then configure monitored scheduling and retention.

## Go-live gate

Do not mark storage or disaster recovery production-ready until the private-bucket policy, restricted key, upload/download/tenant-isolation tests, malware-scan path, off-host backup, restore drill, retention, and alerting have evidence. The existing local upload-volume drill contained zero files, so it is not evidence of customer-file recovery.
