# Kognivon Website — Executive Creative, Marketing, UI/UX & Technology Audit
Date: 2026-09-28

## Executive summary
Kognivon now presents a credible enterprise SaaS identity: disciplined blue/navy brand language, evidence-led trust messaging, structured enterprise sales intake, guided evaluation, pricing, implementation and integration journeys, and a premium organization-scoped login experience.

The largest remaining website issue is not visual quality; it is consolidation. The landing page and CSS have accumulated overlapping messages and repeated style layers during rapid iteration. The next refinement should shorten the buyer journey, unify public header/footer/button primitives, and consolidate style tokens rather than adding more visual components.

## Implemented before this audit
- Replaced the old landing-page workspace preview with a richer responsive Kognivon Capability Command Center visual.
- Added global scroll-to-top control with keyboard focus and reduced-motion handling.
- Added intl-tel-input with searchable country flags, international dialing codes, formatting and validation-oriented behavior to commercial forms.
- Preserved searchable country selector with flag + country name.
- Added business phone to the compact landing inquiry form.
- Consolidated auth/login CSS and removed duplicate/malformed mobile override blocks.
- Kept structured enterprise inquiry fields flowing into CRM: country, organization size, phone, objective, timeline and campaign attribution.
- Existing security, sitemap, SEO, implementation, integrations, guided-evaluation and trust work remains in place.

## 1. Header & navigation
### Current strengths
- Sticky white/blurred enterprise header.
- Kognivon logo is clear and appropriately weighted.
- Primary commercial action is Contact Sales.
- Guided Evaluation and Sign In have lower visual weight.
- Desktop IA covers Platform, Solutions, Enterprise, Security & Trust and Pricing.

### Gaps
- Landing page and CommercialShell implement separate header systems.
- At smaller desktop widths the two-row navigation adds density.
- Public IA is approaching the point where direct links will become crowded.

### Recommendation
- Build one shared PublicHeader used across every public page.
- Keep desktop top-level navigation to 5–6 destinations.
- When more public pages exist, introduce a real Enterprise/Product menu instead of extending the horizontal link list.
- Add current-route/active state on secondary pages.
- Maintain >=44px touch targets and >=12.5px desktop nav type.

## 2. Footer
### Current strengths
- Buyer-oriented groups: Platform, Evaluate, Trust & Access.
- Implementation and Integrations are discoverable.
- Footer maintains the same brand tone as the landing page.

### Gaps
- Landing and CommercialShell footers are duplicated implementations.
- Privacy, Terms, DPA, Subprocessors, Accessibility and privacy-choice links do not yet exist.

### Recommendation
- Create one PublicFooter component.
- Add legal/privacy destinations only after approved legal content exists.
- Add a low-emphasis compliance/legal strip below the main footer once those documents are available.

## 3. Visual identity, colors & theme
### Current strengths
- Navy + enterprise blue + white is internationally credible and appropriate for HR/learning/workforce technology.
- Dark navy is used for high-emphasis areas instead of excessive decoration.
- Brand blue clearly identifies actions and key statements.
- The new command-center hero visual is product-adjacent rather than generic stock imagery.

### Gaps
- globals.css still contains historical green-theme rules followed by later blue override layers.
- Several public styles use literal hex values instead of semantic tokens.

### Recommendation
Consolidate into semantic tokens:
- --color-brand-primary
- --color-brand-hover
- --color-text-primary
- --color-text-secondary
- --color-surface
- --color-surface-muted
- --color-border
- --color-success / warning / danger

Use only three principal public background families:
1. White / neutral
2. Very light blue
3. Deep navy

## 4. Typography
### Current strengths
- Geist is an excellent enterprise SaaS choice.
- Large display headings have strong hierarchy and contemporary spacing.
- Body copy has adequate line-height and restrained weight.

### Gaps
- Some real UI helper text/nav/footer labels fall into the 9–11px range.
- Repeated uppercase eyebrow labels can become visually noisy on a long page.

### Recommendation
Real interface type floors:
- Body: 15–17px
- Navigation: 12.5–14px
- Form labels: 12–13px
- Helper text: 11–12px
- Eyebrows: 10.5–11.5px
Avoid interactive copy below 11px.
Reserve very small text for the illustrative hero visual only.

## 5. Buttons
### Current strengths
- Primary blue CTA is clear.
- Secondary outlined actions are restrained.
- Focus states exist.
- Hero CTA alignment has been improved.

### Gaps
There are multiple button systems:
- landing primaryButton / secondaryButton
- commercial primary / secondary
- global button / button-primary
- auth submit-button

### Recommendation
Create one Button primitive with:
- primary
- secondary
- tertiary/text
- destructive
- sm / md / lg
Only one primary action per content block.

## 6. Landing-page hero
### Current strengths
- “Build Capability. Drive Performance.” is concise and outcome oriented.
- Supporting copy explains the fragmentation problem.
- Primary CTA is sales-oriented.
- New Capability Command Center visual better communicates executive workforce intelligence than the previous static-looking preview.

### Recommendation
Keep the hero focused on:
- category
- problem
- result
- CTA
- one visual
Do not add more badges or proof claims above the fold until real customer evidence exists.

## 7. Landing-page duplication & repetition
### Observed overlap
- Product Experience and How It Works both explain expectation → learning → evidence.
- Use Cases and Business Case both explain value/outcomes.
- Enterprise Signals, Enterprise section and Trust section repeat role/governance/evidence language.
- Enterprise Architecture repeats the dedicated Integrations page.
- Rollout repeats the dedicated Implementation page.
- Intro band repeats part of the hero/category proposition.
- FAQ repeats Integration and Implementation explanations.

### Content frequency in current landing source
- capability: ~40 occurrences
- enterprise: ~36
- learning: ~36
- role: ~29
- evidence: ~28
- workforce: ~19
- action: ~18
- readiness: ~16

### Recommended landing structure
1. Hero
2. Enterprise proof/signal strip
3. Platform capabilities
4. How Kognivon works — merge Product Experience + How It Works
5. Business outcomes/use cases — merge Use Cases + Business Case
6. Role-based value
7. Enterprise readiness teaser linking to Trust / Integrations / Implementation
8. FAQ
9. Enterprise conversation form
10. Closing CTA + footer

This would shorten the page while improving narrative clarity.

## 8. Forms
### Current strengths
- Official work email validation.
- Searchable country field with flags.
- intl-tel-input for phone country flag, country code and international formatting.
- Organization size, job title, objective and evaluation timeline.
- Consent, honeypot and rate limiting.
- Structured CRM attribution and qualification.
- Clear success state.

### Improvements
- Add field-level inline validation instead of relying mainly on the bottom form status.
- Add inputId/htmlFor wiring for React Select for stronger accessibility.
- Validate optional phone server-side to E.164 when a phone is supplied.
- Link consent to the real Privacy Notice once approved.
- Consider email-domain typo guidance.
- Keep landing form shorter than Contact Sales; do not duplicate every enterprise field on both surfaces.
- Add useful post-submit next actions such as Security & Trust or Guided Evaluation.

## 9. Login
### Current strengths
- Premium split-screen brand experience.
- Organization-scoped sign-in.
- Company-specific /login/{organization} route.
- Password visibility, reset flow, lockout controls and secure session handling.
- Search-engine indexing disabled.

### Next identity work
The project has OIDC/SAML integration configuration/testing infrastructure, but the login route is still password based. Do not advertise SSO until actual authentication flow is implemented.

Recommended sequence:
1. Tenant/auth discovery
2. OIDC Authorization Code + PKCE
3. SAML SP flow where required
4. Tenant/domain mapping
5. IdP configuration wizard
6. JIT provisioning / SCIM decision
7. MFA/session policy
8. SSO audit events
9. Conditional “Continue with SSO” in login

## 10. Pricing
### Strengths
- No fabricated pricing.
- CRM-backed public catalogue.
- Enterprise scope is explained.

### Recommendations
- If no standard public plan exists, keep the page short: pricing drivers + enterprise proposal CTA.
- When plans are public, compare meaningful procurement dimensions: modules, users, integrations, implementation, support, security, analytics and service levels.
- Treat public “offers” carefully; enterprise buyers often respond better to negotiated commercial terms than promotional discount language.

## 11. Security & Trust
### Strengths
- Evidence-led posture.
- No fabricated certifications.
- Clear distinction between controls, contractual commitments and certifications.

### Recommended future evidence sections
Only when verified:
- encryption
- tenant isolation
- backup/DR
- incident response
- retention/deletion
- subprocessors
- vulnerability management
- availability/BCP
- penetration testing
- data residency
- SSO/MFA
- DPA/privacy

## 12. Implementation & Integrations
### Strengths
- Dedicated routes now exist.
- No unsupported logo wall.
- Scope-first wording is credible.

### Recommendation
- Landing page should tease these areas rather than repeat their full content.
- Add a validated integration registry later with explicit status: Supported / Validated / Configuration-based / Planned / Not supported.
- Add customer/Kognivon responsibility matrix to Implementation once services policy is finalized.

## 13. Accessibility
### Strengths
- Skip links
- visible focus
- reduced-motion support
- semantic details/summary
- status messaging

### Recommendations
- Run WCAG 2.2 AA automated + keyboard audit.
- Test React Select and intl-tel-input end-to-end by keyboard.
- Add scroll-margin-top to anchor targets if sticky-header overlap is found.
- Test 320, 375, 768, 1024, 1440 and 1920 widths.
- Keep real interface text >=11px.
- Ensure scroll-to-top does not conflict with future chat/support widgets.

## 14. CSS / technical duplication
A selector scan of landing.module.css found heavy accumulated override debt:
- heroGrid appears in ~12 rule blocks
- signin ~11
- nav ~9
- brandLogo ~9
- navCta ~9
- many section selectors 7–9 times

Some repeats are media-query variants, but the file clearly contains iterative override layers.

### Recommendation
After the visual system is locked:
- refactor landing.module.css into one canonical header section
- one hero section
- one section/card system
- one forms section
- one responsive breakpoint layer
- remove obsolete preview styles after the new command-center visual is accepted

## 15. SEO & performance
### Current strengths
- canonical metadata
- Open Graph
- sitemap
- robots
- structured Organization + SoftwareApplication data
- local fonts
- private routes noindex

### Recommendations
- add per-page OG metadata
- consider visible FAQ schema only if FAQ is retained
- configure final production NEXT_PUBLIC_SITE_URL
- monitor bundle impact of intl-tel-input and keep it form-scoped
- continue avoiding heavy autoplay/video hero assets

## Priority order
P0 — completed in this tranche:
- scroll-to-top
- intl-tel-input
- country flags
- improved hero visual
- auth CSS cleanup
- form internationalization

P1:
- merge duplicated landing sections
- unify PublicHeader/PublicFooter
- unify button primitives
- consolidate public design tokens
- remove obsolete landing CSS overrides

P2:
- real SSO/OIDC/SAML auth flow
- field-level form validation
- verified security-center evidence
- legal/privacy pages
- validated integration registry

P3:
- real customer evidence and case studies
- quantified ROI/business-case material
- content/resource center
