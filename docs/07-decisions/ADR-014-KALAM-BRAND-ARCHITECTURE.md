# ADR-014 — Kalam Brand Architecture

**Date:** 2026-09-29  
**Status:** Accepted  
**Supersedes:** Kognivon-facing brand governance decisions for customer-facing product identity

## Decision

The current customer-facing product brand is **Kalam**.

The canonical descriptor is:

**Kalam — Enterprise Workforce Capability Platform**

The brand architecture is deliberately product-led rather than module-led. Learning, skills, assessments, credentials, compliance, development, analytics and governed AI are capabilities within Kalam; they should not become disconnected product brands.

## Brand hierarchy

1. **Kalam** — master customer-facing product brand
2. **Enterprise Workforce Capability Platform** — category descriptor
3. **Build Capability. Drive Performance.** — primary brand expression
4. **Prove Readiness.** — supporting outcome expression
5. Capability names — Learning, Skills, Compliance, Assessments, Credentials, Workforce Intelligence, etc.

## Naming rules

Use Kalam in:
- page titles
- public navigation
- authentication
- dashboard chrome
- public metadata
- support and trust content
- social preview assets
- customer-facing documentation

Use CorpLMS only as a repository/technical continuity identifier.

The historical kognivon-brand.tsx file remains only as a compatibility re-export. New code must import the canonical kalam-brand.tsx component.

## Positioning rule

Do not position Kalam primarily as an LMS.

Lead with workforce capability, evidence, governance and readiness. Learning is an important capability within that broader operating model.

## Legal gate

The word Kalam is used by multiple current businesses and products, including education, language learning and customer-experience organizations. An initial public-web screen therefore identified a genuine global name-clearance consideration. Formal trademark, company-name, domain and market-specific clearance must be completed before claiming worldwide exclusivity or making irreversible expansion commitments.

The product may continue to use the Kalam identity in the current controlled environment, but legal clearance is a release gate for international brand scaling.

## Design-system rule

All customer-facing surfaces inherit the shared Kalam design system:
- Kalam Navy
- Kalam Blue
- Kalam Tech
- Kalam Ice
- restrained Kalam Gold accent
- Geist Sans
- shared radius/elevation/motion tokens
- canonical K + alam lockup

A screen-specific visual treatment must not create an alternative brand system.

## Rationale

Global enterprise brands build recognition by repeating a small set of distinctive assets and ideas across many touchpoints. Kalam therefore uses one identity, one message spine and one design language across public marketing, authentication, product, trust, documentation and enterprise sales experiences.

## Consequences

Positive:
- stronger brand recognition across the product
- clearer enterprise category ownership
- less module-level brand fragmentation
- easier global localization and asset governance
- more consistent product and marketing design

Required follow-through:
- replace remaining legacy Kognivon customer-facing references
- maintain one shared brand component
- align website, CRM, trust, product and sales narratives
- complete formal global name clearance
- maintain evidence-backed claims only