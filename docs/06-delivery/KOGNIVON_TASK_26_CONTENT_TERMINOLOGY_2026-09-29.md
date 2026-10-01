# Kognivon Task 26 — Content and Terminology Governance

Date: 2026-09-29  
Status: Complete for the current application copy pass.

## Audit scope

Reviewed navigation labels, page headings, empty states, CTAs, KPI labels, administrative descriptions, and public-facing capability language for consistency with Kognivon's positioning around workforce capability, readiness, development, evidence, credentials, and organizational decisions.

## Changes made

- Renamed navigation `User Administration` to `People Administration` to align with the People workspace and workforce terminology.
- Renamed the learner-facing `Certificates` navigation label to `Credentials` while preserving the existing route and data model.
- Renamed the assessment page heading `Examinations` to `Assessments` for consistency across navigation, operations, and reporting.
- Renamed the reports KPI label `Certificates` to `Credentials`.
- Updated manager detail language from `Manager learner view` / `Learner data unavailable` to `Manager development view` / `Team member data unavailable`.
- Updated capability framework guidance to reference People Administration rather than the superseded label.

## Governance decisions

- Use `learner` for the person receiving learning, assignments, or assessment activity.
- Use `team member` in manager-facing context where the relationship matters more than the learning transaction.
- Use `credential` for issued, verifiable achievement records; retain `certificate` only where it describes the underlying record or certificate-specific administrative workflow.
- Use `capability`, `readiness`, `evidence`, and `development` for product value language; retain technical terms such as API, webhook, and enrollment where operational precision requires them.

## Verification

- `pnpm --filter web typecheck` passed.
- `git diff --check` passed; only existing line-ending normalization warnings were reported.

## Follow-up

Future copy changes should use these terms as the review baseline, with translation/content review before adding additional public or workflow vocabulary.
