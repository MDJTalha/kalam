# Kalam API Error Contract — Source Closure

Date: 2026-10-31

## Result

The legacy server-side `apiJson()` helper has been removed from `apps/web/src/lib/server-api.ts`.

The canonical server-side JSON access contract is now `apiJsonResult()`, which preserves:

- `ok`
- HTTP `status`
- parsed `data`
- API `error` detail

This prevents server-rendered business screens from collapsing 401/403/404/409/422/429/5xx responses into an indistinguishable null result.

## Verification performed

The current `main` source was inspected after the removal commit. The remaining repository search hit for the string `apiJson(` is historical QA documentation, not an application caller.

Representative current screens already using `apiJsonResult()` include:

- Compliance
- People administration
- L&D operations
- Admin
- Audit
- Files
- Skills
- Organization
- Reports
- Analytics
- Assessments
- Development
- Sessions
- Webhooks
- SaaS tasks
- AI
- Manager/team workspace

## Boundary

This is **source-level closure**, not runtime certification. CI, browser authentication, live tenant-isolation tests, accessibility, performance, backup restore, DR, AWS production and rollback evidence remain independent release gates.
