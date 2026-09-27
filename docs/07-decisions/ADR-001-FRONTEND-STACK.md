# ADR-001 — Frontend Stack

Status: Accepted
Date: 2026-09-24

## Decision
Use Next.js with TypeScript for the web application.

## Why
- Supports server/client rendering deliberately.
- Strong TypeScript ecosystem and routing model.
- Suitable for authenticated enterprise dashboards and public pages.
- Enables an accessible responsive interface without introducing a separate SPA shell by default.

## Alternatives
A standalone React SPA was considered but adds routing/rendering responsibility without a required benefit at this stage.

## Consequences
The web app owns presentation and browser interaction; authorization remains server-side in the API. Build/typecheck/lint are CI gates.