# Kalam — Frontend Design System Baseline

Version: 1.0
Status: Active canonical frontend baseline
Authority: `KALAM_9_9_BRAND_SURFACE_GOVERNANCE.md` and `apps/web/src/app/design-system.css`

## 1. Design decision

Kalam is an **Enterprise Workforce Capability Platform**. The frontend uses Kalam Navy and Kalam Blue as its identity foundation, with Tech, Ice and restrained Gold accents. Green is reserved for semantic success states; it is not a competing brand or navigation identity.

The canonical narrative is **Expectation → Capability → Evidence → Action → Readiness**. The interface should make capability visible, governable and provable.

## 2. Visual character

The interface must feel enterprise SaaS, intelligent, data-driven, precise, calm, information-dense, accessible and operational. It must support executives, HR/L&D, capability and workforce leaders, managers, instructors, compliance owners and learners.

Avoid neon, excessive gradients, glassmorphism, stock photography and decorative widgets.

## 3. Canonical tokens

Consume the shared variables from `apps/web/src/app/design-system.css`. Do not introduce a parallel palette.

| Token | Canonical value | Primary use |
|---|---|---|
| Kalam Navy | #08243D | Identity, hierarchy, shell |
| Kalam Blue | #0878C9 | Primary actions, links, product emphasis |
| Kalam Tech | #3EA9DD | Secondary emphasis and data visualization |
| Kalam Ice | #EAF5FC | Subtle surfaces and selected states |
| Kalam Gold | #C99732 | Restrained premium emphasis |
| Kalam Blue Hover | #0669AE | AA-safe primary text/action on Ice |
| Kalam Ice Ink | #52657A | AA-safe muted text on Ice |

Workspace surfaces, text, borders, semantic statuses, typography, spacing, radii, shadows, focus and motion must use the shared design-system variables wherever available. Normal-size text requires at least 4.5:1 contrast. Kalam Tech and Kalam Gold are accent colors, not normal-size text on white or Ice. Use Kalam Blue Hover or Kalam Ice Ink for text on Ice.

## 4. Application shell

The authenticated shell uses the canonical navy/blue Kalam identity, a responsive content canvas, role- and permission-aware navigation, accessible active/focus states and a consistent global header.

Header context includes breadcrumbs, page title, organization/workspace selector, global search, notifications, help, profile and role context as applicable.

## 5. Information hierarchy

Prioritize decision-critical signals, risks and gaps, trends, actionable work, drill-down details and supporting evidence. Every visual component must have a defined business purpose.

Decision surfaces follow **Context → Evidence → Decision → Action → Accountability**.

## 6. Data visualization

Use the Kalam blue family as the primary visualization family, navy for reference/baseline and gold for restrained emphasis. Semantic status colors remain distinct. Charts must remain understandable without color alone and provide accessible labels, units, provenance and summaries.

## 7. Component system

Reusable components cover buttons, cards, KPI cards, tables/data grids, forms, filters, tabs, badges, status indicators, progress, charts, modals, drawers, tooltips, breadcrumbs, pagination, empty/loading/error states and confirmations.

Components share spacing, typography, radius, border, focus and interaction tokens. Applicable keyboard, screen-reader, responsive and reduced-motion states must be documented and verified.

## 8. Responsive behavior

Desktop, tablet and mobile layouts reflow around task priority rather than merely scaling down. Tables use horizontal scrolling or an intentional responsive representation. Navigation collapses accessibly. Dense dashboard grids reduce columns while preserving decision-critical information.

## 9. Accessibility

Target WCAG 2.2 AA. Focus visibility, keyboard navigation, semantic headings, form labels, contrast, non-color status cues and reduced-motion support are release requirements.

## 10. Governance

This is the active Kalam frontend baseline. The canonical brand governance document and implemented design-system tokens take precedence in any conflict. Historical predecessor-brand design exploration is not an active source of truth.
