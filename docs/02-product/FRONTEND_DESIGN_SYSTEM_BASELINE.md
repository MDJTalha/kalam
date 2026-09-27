# Corporate LMS — Frontend Design System Baseline

Version: 0.1
Status: Phase 0 controlled UX baseline
Date: 2026-09-24

## 1. Design decision

AIVON Learning OS uses a bright blue-first enterprise workspace. Deep navy/blue is the application-shell foundation; blue is the primary product, action and visualization family; gold is a restrained AIVON identity accent. Green is reserved for semantic success states and is not a primary brand/shell color.

This resolves the two design directions in the implementation brief:
- User requirement: bright, blueish corporate visual language.
- Product requirement: premium dark corporate-green navigation with subtle gold accents.

Blue is the primary workspace/data visualization family. Green identifies AIVON brand, active navigation and trusted/approved actions. Gold is reserved for identity emphasis and selected premium states.

## 2. Visual character

The interface must feel:
- enterprise SaaS
- intelligent and data-driven
- bright, precise and information-dense
- calm rather than decorative
- accessible and operational
- suitable for CHRO, CLO, HR/L&D, capability and executive users

Avoid neon, heavy gradients, excessive glassmorphism, stock photography and decorative widgets.

## 3. Core palette

Workspace background: cool blue-white / very light slate.
Primary workspace blue: professional medium-deep blue.
Primary blue dark: navigation/action hover and high-contrast states.
AIVON brand green: deep corporate green.
AIVON green dark: sidebar and high-emphasis brand surfaces.
AIVON gold: restrained identity accent.
Text: dark charcoal/navy.
Muted text: cool slate.
Borders: cool blue-gray.
Surfaces: white and near-white.

Status colors remain semantic and restrained: success, warning, danger and neutral.

## 4. Application shell

The authenticated shell consists of a dark-green AIVON sidebar, bright blue-white workspace, consistent global header and responsive content canvas.

Sidebar requirements:
- grouped navigation
- active state
- role/permission-aware visibility
- collapse behavior
- accessible focus state
- badges only where operationally meaningful

Header requirements:
- breadcrumbs
- page title/context
- organization/workspace selector
- global search
- notifications
- help
- profile and role context

## 5. Information hierarchy

Dashboard and operational screens prioritize:
1. decision-critical KPIs
2. risks and gaps
3. trends
4. actionable work
5. drill-down details
6. supporting evidence

Every visual component must have a defined business purpose.

## 6. Data visualization

Charts must use the blue/green/gold product palette consistently and remain legible without relying on color alone.

Preferred patterns:
- KPI cards
- line/area trends where time matters
- bars for comparison
- rings/donuts for composition when categories are limited
- heatmaps for capability/skill matrices
- progress indicators for completion/readiness

Charts must be data-driven and support accessible labels/tooltips.

## 7. Component system

Reusable components must cover buttons, cards, KPI cards, tables/data grids, forms, filters, tabs, badges, status indicators, progress, charts, modals, drawers, tooltips, breadcrumbs, pagination, empty/loading/error states and confirmations.

Components must share spacing, typography, radius, border, focus and interaction tokens.

## 8. Responsive behavior

Desktop is the primary enterprise workspace. Tablet and mobile layouts must reflow rather than simply scale down.

Tables should support horizontal scrolling or an intentional responsive representation. Navigation should collapse. Dense dashboard grids should reduce columns while preserving priority.

## 9. Accessibility

Target WCAG 2.2 AA. Focus visibility, keyboard navigation, semantic headings, form labels, contrast and non-color status cues are release requirements.

## 10. Phase 0 governance

This document is the visual baseline for Phase 1 frontend implementation. Changes to the primary palette, application shell or information architecture after Phase 0 require controlled change documentation.
