# Kalam — AI Governance Certification Decision

Date: 2026-10-31
Candidate branch: `work/final-production-readiness-2026-10-31`
Decision: **AI NOT ENABLED FOR PRODUCTION**

## Scope

This decision covers the current release candidate. It does not certify any future real-provider activation.

## Evidence

- Deployment configuration defaults `AI_ENABLED=false` and `AI_PROVIDER=disabled`.
- The deployment configuration explicitly states that AI remains disabled until an administrator registers a provider/model and enables a tenant governance policy.
- The database governance policy defaults `enabled=false`.
- CI fixtures create tenant AI governance policies with AI disabled, grounding required, employment decisioning prohibited, raw prompt/response storage prohibited, and an empty allowed-provider list.
- The application returns governance state with policy enablement and storage controls, and activation is fail-closed until deployment and tenant governance conditions are satisfied.
- Existing focused provider/governance tests cover disabled-provider behavior, grounding, provider rejection, secret-reference fail-closed behavior and readiness-gated activation.

## Certification boundary

C17 is certified **only as a fail-closed disabled-by-default control** for this candidate.

Before enabling any real provider in staging or production, a new certification event is mandatory covering:
1. provider/model registration;
2. secret handling;
3. tenant isolation;
4. grounding and source authorization;
5. prompt/response data handling;
6. human override and employment-decision restrictions;
7. audit evidence;
8. rate/cost limits;
9. abuse/safety testing;
10. rollback/disablement.

No real-provider production activation is authorized by this record.
