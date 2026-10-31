# SaaS Super Admin bootstrap

## Purpose

Kalam keeps the SaaS Super Admin identity separate from tenant administrators, SaaS Administrators, and Platform Developers. The role is provisioned in the internal SaaS operations tenant and is not a customer-tenant role.

## Required configuration

Set the following values in the deployment secret store or an untracked local environment file:

- `SAAS_OPS_TENANT_SLUG`: the internal operations tenant slug (normally `kalam`).
- `SAAS_SUPER_ADMIN_EMAIL`: the named operator's email address.
- `SAAS_SUPER_ADMIN_PASSWORD`: a unique initial password of at least 16 characters.

Never commit populated credentials, put passwords in shell history, or paste them into issue/PR comments. Generate the initial password with a password manager and rotate it through the normal account recovery process after first sign-in. Configure MFA/SSO where supported by the deployment's identity policy.

## Provisioning sequence

1. Apply the reviewed Alembic migration chain to the intended database.
2. Configure the operations tenant slug and Super Admin email/password using the deployment secret store.
3. Run `python scripts/bootstrap_saas_ops.py` from `apps/api` using the same application environment and database connection as the deployment.
4. Confirm the command reports the Super Admin account as created/assigned, then verify the account is active and has the `SaaS Super Admin` platform role in the operations tenant.
5. Sign in through the browser and verify tenant lifecycle, platform-role governance, customer-user access, finance, audit and session-revocation permissions. Confirm customer-tenant accounts cannot access SaaS operations.
6. Remove the one-time bootstrap secret from the execution environment after provisioning.

The bootstrap script requires both email and password to create a new Super Admin account. It rejects initial passwords shorter than 16 characters. It does not create a default account or print the password. If the email already exists, it assigns the platform role to that existing account; it does not reset an existing password.

## Release safety

Do not create the first Super Admin using a shared demo credential. Do not enable platform operations on a production database until the migration chain, backups, access policy, TLS and audit logging have been verified. The bootstrap process creates an identity and role assignment; it does not itself prove that the account has passed authenticated browser acceptance.
