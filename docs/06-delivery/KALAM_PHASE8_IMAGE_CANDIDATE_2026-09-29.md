# Kalam Phase 8 — Current-Source Image Candidate

Date: 2026-09-29
Commit: 6fea20a92337f18b0b74eedab9493675981da08e
Branch: release/phase8-rc1-20260927

## Candidate image digests

- API: sha256:774ec41d418dcab1ddd520cf3594706a334c74e5e0bc83abd581a9fef8af9cb1
- Web: sha256:4c0453f2c88e87179f3b1c5ba9a217a1813738718f02600d142902f4a99573ad
- Worker: sha256:d6cba0ca664daa478ee631bfbb438e8881e94c1398b8bd2cf4278b19717a7d7c

## Candidate tags

- kalam-phase8-api:6fea20a92337f18b0b74eedab9493675981da08e
- kalam-phase8-web:6fea20a92337f18b0b74eedab9493675981da08e
- kalam-phase8-worker:6fea20a92337f18b0b74eedab9493675981da08e

## Certification status

Local candidate identity captured. This does not constitute production certification.

### Integrated candidate smoke

The current candidate image trio was deployed together in the Phase 8 RC stack and passed gateway smoke with the exact candidate digests:

- Gateway health: 200
- Web: 200
- Security headers: pass
- API readiness: ready
- Database: ready
- Valkey: ready
- Migration container: exit 0
- Worker: running
- API/Web/Worker digests: exact candidate match

### Defects corrected during authenticated-readiness work

- Removed a literal escaped newline token at the end of apps/api/app/api/routes/intelligence.py that caused API test collection to fail with SyntaxError.
- Corrected seed_reference_enterprise.py role-name mismatches so every seeded access role resolves to an actual role.
- Added the missing enterprise reference roles used by the seed (HR/L&D Admin, HR Business Partner, Quality & Compliance, Auditor, Regional Executive, Global Executive) and corrected the default learner role name.
- Restored the local demo/operations QA baseline from the Phase 8 database snapshot, applied current Alembic migrations, and enabled the explicitly configured local demo CRM exception.
- Authenticated AI governance/security tests now pass: 10 passed.
- SaaS commercial tests now pass: 5 passed.

Browser/CDP authenticated certification is still not closed because the local CDP endpoint used by the existing browser harness is currently unavailable; therefore no browser PASS is being claimed from that harness.
