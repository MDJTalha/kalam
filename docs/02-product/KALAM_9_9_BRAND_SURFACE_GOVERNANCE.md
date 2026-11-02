# Kalam 9.9 Brand Surface Governance & Certification Standard

**Status:** Active
**Target:** 9.9/10
**Scope:** 100% customer-visible and customer-influencing surfaces

## Purpose

This document converts the Kalam brand system into an enforceable implementation standard. Brand quality is measured at the smallest meaningful unit: route, screen, component, element, interaction state, content string, asset, metadata, communication and documented claim.

## Canonical identity

- **Brand:** Kalam
- **Category:** Enterprise Workforce Capability Platform
- **Primary expression:** Build Capability. Drive Performance.
- **Outcome:** Prove Readiness.
- **Narrative:** From expectation to capability, evidence, action and readiness.
- **Brand idea:** Capability should be visible, governable and provable.
- **Voice:** Expertise without hype.

## 100% surface inventory

Every discovered surface must be inventoried and assigned one status:

- **KEEP** — meets the canonical standard.
- **REFINE** — minor alignment required.
- **REBUILD** — material inconsistency.
- **EXCEPTION** — intentional deviation with documented rationale.

Inventory categories:

1. routes and pages
2. screens and layouts
3. reusable components
4. component variants and states
5. interactive elements
6. content strings
7. assets and icons
8. navigation and information architecture
9. forms and validation
10. tables, charts and reporting
11. dashboards and widgets
12. empty/loading/error/permission states
13. authentication and onboarding
14. trust/security/privacy surfaces
15. AI surfaces
16. emails and notifications
17. help and documentation
18. metadata and SEO
19. responsive behavior
20. accessibility behavior
21. localization/globalization
22. analytics and event naming
23. technical/customer-facing identifiers

Sampling is permitted for regression testing only. It is not evidence of complete inventory coverage.

## Traceability

Every audited surface must be traceable as:

**Surface → Requirement → Current State → Decision → Implementation → Verification → Evidence → Final Status**

No 9.9 certification is valid without traceability for all P0/P1 findings and a disposition for every discovered surface.

## Component standard

Reusable components must have documented behavior for applicable:

- default
- hover
- focus
- active
- selected
- disabled
- loading
- success
- warning
- error
- destructive
- empty
- permission denied
- keyboard
- screen reader
- responsive
- reduced motion
- long content/localization

## Content standard

Every user-visible string must be reviewed for:

- positioning
- terminology
- voice
- clarity
- evidence
- claim safety
- accessibility
- localization readiness

Prohibited: unsupported customer, certification, security, regulatory, performance, AI or ROI claims.

## Experience standard

Every important screen must answer:

1. What is happening?
2. What evidence supports it?
3. What should happen next?

Decision surfaces should follow:

**Context → Evidence → Decision → Action → Accountability**

The canonical capability model is:

**Expectation → Capability → Evidence → Action → Readiness**

## Visual standard

Canonical tokens are defined in `apps/web/src/app/design-system.css` and the global Kalam brand documentation. New customer-facing UI must consume these tokens and shared brand primitives rather than creating parallel brand values.

Canonical brand colors:

- Navy #08243D
- Blue #0878C9
- Tech #3EA9DD
- Ice #EAF5FC
- Gold #C99732

Semantic success/warning/danger colors remain status colors and must not become competing brand colors.

## Legacy identity policy

Kalam is the only customer-facing master brand. Historical Kognivon/CorpLMS identifiers may remain only where required for technical continuity, migrations, database/API compatibility or historical evidence. They must not appear as active customer-facing branding.

## Accessibility and motion

Accessibility is part of brand quality. Keyboard access, focus visibility, semantic structure, labels, contrast, screen-reader behavior, responsive layout and reduced-motion preferences must be preserved across every applicable component.

## Certification gates

A release cannot receive 9.9 certification if:

- a P0/P1 brand-critical defect remains;
- a customer-facing legacy brand conflict remains unexplained;
- a material unsupported claim remains;
- a critical accessibility regression exists;
- a core workflow is functionally broken;
- the inventory is incomplete;
- evidence is missing for material claims of completion.

## Scoring

| Dimension | Weight |
|---|---:|
| Strategy | 10% |
| Positioning | 10% |
| Messaging | 10% |
| Visual identity | 10% |
| UX/UI | 10% |
| Product consistency | 10% |
| Enterprise credibility | 10% |
| Content/SEO | 10% |
| Governance | 10% |
| Accessibility/global readiness | 10% |

Target: **≥ 9.9/10**, with no unresolved critical gate failure.

## Ownership

Product owns product meaning and workflows.
Design owns visual and interaction standards.
Engineering owns implementation integrity and automated enforcement.
Marketing owns public messaging and content.
Security/Legal own trust and claim boundaries.
Leadership owns strategic exceptions and final certification.

## Operating rule

Preserve existing implementation when it is demonstrably stronger than the written guideline; update the guideline to match. Where the canonical standard is stronger and the implementation is outdated, update implementation. Where both conflict, establish one canonical decision and remove the competing standard.

