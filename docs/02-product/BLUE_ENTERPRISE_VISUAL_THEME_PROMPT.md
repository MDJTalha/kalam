# Kalam — Enterprise Visual Theme Baseline

Version: 1.0
Status: Active canonical visual direction
Supersedes: The September 2026 predecessor-brand visual exploration in this file's prior revision.
Authority: `KALAM_9_9_BRAND_SURFACE_GOVERNANCE.md` and `apps/web/src/app/design-system.css`

## Canonical identity

- Brand: **Kalam**
- Category: **Enterprise Workforce Capability Platform**
- Primary expression: **Build Capability. Drive Performance.**
- Outcome: **Prove Readiness.**
- Brand idea: Capability should be visible, governable and provable.
- Voice: Expertise without hype.

## Visual character

The interface must feel enterprise-grade, intelligent, data-driven, calm, precise, information-dense, readable and operational. It must serve executives, HR/L&D, capability leaders, managers, instructors, compliance owners and learners.

Avoid neon, excessive gradients, glassmorphism, decorative widgets, stock photography and visual noise. Every visual element must support comprehension, a task or a business decision.

## Canonical palette

Use the shared design tokens in `apps/web/src/app/design-system.css`; do not create parallel brand palettes.

- Kalam Navy: **#08243D**
- Kalam Blue: **#0878C9**
- Kalam Tech: **#3EA9DD**
- Kalam Ice: **#EAF5FC**
- Kalam Gold: **#C99732**
- White and cool blue-white surfaces for workspace clarity.
- Semantic success, warning, danger and neutral colors are status colors, not competing brand identities.

Gold is a restrained accent. Navy establishes trust and hierarchy. Blue communicates action and product intelligence. Tech and Ice support secondary emphasis and surfaces.

### Contrast guardrails (WCAG 2.2 AA)

For normal-size text, use foreground/background pairs with at least 4.5:1 contrast. Verified ratios: Kalam Navy on white 15.79:1; Kalam Blue on white 4.63:1; Kalam Blue Hover (#0669AE) on Ice 5.21:1; Muted Slate (#63738A) on white 4.83:1; Kalam Ice Ink (#52657A) on Ice 5.42:1. Kalam Tech and Kalam Gold are accents, not normal-size text colors on white or Ice. Use navy or an approved AA-safe text token for labels placed over those surfaces.

## Application shell

The authenticated workspace uses the canonical navy/blue Kalam identity, clear navigation grouping, accessible active/focus states, a consistent global header and a responsive content canvas.

The shell should preserve:
- role- and permission-aware navigation;
- breadcrumbs and page context;
- organization/workspace context;
- global search, notifications, help and profile access;
- responsive navigation and usable touch targets;
- visible keyboard focus and skip navigation.

## Information hierarchy

Prioritize:
1. decision-critical capability and readiness signals;
2. evidence, risks and gaps;
3. trends and context;
4. actionable work;
5. drill-down details and accountability.

Decision surfaces should follow **Context → Evidence → Decision → Action → Accountability**.

The canonical capability model is **Expectation → Capability → Evidence → Action → Readiness**.

## Data visualization

Charts must be data-driven, accessible and legible without relying on color alone. Use blue as the primary visualization family, navy for reference/baseline, gold for restrained emphasis and semantic colors only for status.

Preferred patterns include KPI cards, time-series trends, comparison bars, limited-category composition charts, capability/skill matrices and progress/readiness indicators. Labels, units, provenance, empty states and accessible summaries are required.

## Component system

Reusable components must share typography, spacing, radius, border, focus, motion and interaction tokens. Applicable states include default, hover, focus, active, selected, disabled, loading, success, warning, error, empty, permission denied, keyboard, screen-reader, responsive and reduced-motion behavior.

## Responsive and accessibility requirements

Target WCAG 2.2 AA. Desktop, tablet and mobile must preserve task priority and hierarchy. Dense grids reflow; tables use intentional responsive representations; controls remain keyboard and touch accessible. Respect reduced-motion preferences.

## Governance

This file is subordinate to the canonical Kalam brand governance document and the implemented design tokens. If a conflict exists, the governance document and design-system tokens take precedence. Historical brand names in archived task records are evidence only and must not re-enter customer-facing surfaces.
