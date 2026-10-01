# Kognivon landing page quality review
Date: 27 September 2026
Scope: public route `/` in `apps/web`.

## Implemented
- Rebuilt the public page around the learning-to-capability-to-evidence product story.
- Established **Enterprise Workforce Capability Platform** as Kognivon's primary category position; SaaS is used as the delivery model rather than the product category.
- Added mobile navigation paths to evaluation questions and the demo form when enabled.
- Corrected the brand contrast and broken character encoding.
- Added a responsive navigation path, six expandable capability cards, role-specific context, workflow, enterprise context and evaluation questions.
- Kept the illustrative product preview explicitly labelled; no fabricated customers, results or certifications.
- Distinguished existing-user sign-in from public exploration.
- Added a real inquiry form and a private, audited review queue with tenant and permission checks. The form is feature gated until the operations tenant and reviewers are configured.
- Matched focus, target, contrast and reduced-motion patterns to the product design system.
- Upgraded the public experience with a sticky translucent enterprise header, stronger hero hierarchy, category narrative, and a four-part enterprise principles band covering governance, role-aware experiences, distributed organizations and connected evidence.
- Updated the hero to: “Build workforce capability. Prove readiness. Move the enterprise forward.”

## Verification
- TypeScript: pass on the revised SaaS page.
- Targeted ESLint: pass on the revised SaaS page.
- Next.js production build: pass after the final positioning and UI changes (Next.js 16.3.6; exit code 0), including the public intake route and private review page.
- Inquiry validation, review-tenant isolation and missing-reviewer-tenant guard: 3 focused API tests pass.
- Disabled public intake returns HTTP 503; an enabled preview rejects a foreign Origin with HTTP 403. With a missing configured review tenant, the API also rejects intake with HTTP 503.
- Enabled preview at 390 and 1440 CSS pixels: form present, no horizontal overflow or broken anchors; axe WCAG 2.2 AA returned zero detected violations.
- The local marketing inquiry migration is applied at Alembic head `u6v7w8x9y0z1`. The earlier full API suite run was blocked when PostgreSQL was unavailable; it has not been rerun in full.
- Final rendered-page browser reflow at 320, 390, 768 and 1440 CSS pixels: no document overflow or broken anchors; six capability disclosures and five evaluation questions are present at every tested width.
- All in-page links resolve to existing targets.
- Capability disclosure opens by pointer and keyboard Space.
- Final automated axe WCAG 2.2 AA checks: zero detected violations at 320, 390, 768 and 1440 CSS pixels.
- Final capability interaction check: pointer disclosure opens correctly and keyboard Space opens the focused disclosure while retaining focus on the summary control.
- Final visual evidence refreshed at `qa/landing-final-390.png` and `qa/landing-final-1440.png`.
- Visual evidence: `qa/landing-saas-cdp-320.png`, `qa/landing-saas-cdp-390.png`, `qa/landing-saas-cdp-768.png`, `qa/landing-saas-cdp-1440.png`, plus the earlier gated inquiry previews.

## Release gates for a defensible 9.9/10
- Provision a dedicated active Kognivon operations tenant with authorized reviewers; set `MARKETING_REVIEW_TENANT_SLUG` and `MARKETING_INBOX_ENABLED=true` on both API and web, then verify an end-to-end inquiry and review status update. The local migration is applied. The CTA stays on product exploration while the feature is disabled.
- Define ownership, response process, retention/deletion policy and a published privacy notice before collecting live inquiries.
- Replace or supplement illustrative preview with approved current product imagery and verified customer evidence when available.
- Perform manual screen-reader, keyboard journey, zoom and real-device review.
- Measure production LCP, INP and CLS under deployment conditions.
- Validate all enterprise claims against completed security, availability and implementation evidence.

The implemented page is an improved product presentation with a gated conversion path. It does not claim a final 9.9 certification or Fortune 500 deployment readiness.
