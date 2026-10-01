# Kognivon Task 21 — Search and Productivity UX

Date: 2026-09-29
Status: Complete

## Audit scope

- Global search route and tenant/permission boundaries.
- Search coverage for courses, programs, skills, and people.
- Result-to-record navigation and empty/error states.
- Header search affordance, keyboard shortcut behavior, and quick actions.

## Findings and changes

- Global search is backed by real tenant-scoped records and limits each result group to a bounded set. Published/enrolled course visibility and published-program visibility are enforced for non-course-managers; people results require `users.read`.
- Search results provide direct links to course, program, people, and skills workspaces, with useful no-query, short-query, no-results, and unavailable states.
- The application header displayed `⌘K`/`Ctrl+K` but had no keyboard handler. Added `GlobalSearchShortcut`, which opens `/dashboard/search`, ignores typing contexts, and supports both macOS and Windows/Linux modifiers.

## Verification

- Search/tenant settings API regression — passed.
- Web typecheck — passed.
- Search route Python compilation — passed.
- Search results remain permission- and tenant-scoped at the API layer; UI filtering is not treated as security.
