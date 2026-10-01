# CorpLMS Phase 0 QA Baseline

Date: 2026-09-25

Dashboard route modules: 49
Recovery/placeholder route matches: 36
Button/Link occurrences scanned: 98

## Recovery routes
- apps\web\src\app\dashboard\audit\page.tsx:1 — import { RecoveredWorkspace } from "@/components/recovered-workspace";
- apps\web\src\app\dashboard\audit\page.tsx:4 — return <RecoveredWorkspace />;
- apps\web\src\app\dashboard\catalog\categories\page.tsx:1 — import { RecoveredWorkspace } from "@/components/recovered-workspace";
- apps\web\src\app\dashboard\catalog\categories\page.tsx:4 — return <RecoveredWorkspace />;
- apps\web\src\app\dashboard\certificates\admin\page.tsx:1 — import { RecoveredWorkspace } from "@/components/recovered-workspace";
- apps\web\src\app\dashboard\certificates\admin\page.tsx:4 — return <RecoveredWorkspace />;
- apps\web\src\app\dashboard\compliance\admin\page.tsx:1 — import { RecoveredWorkspace } from "@/components/recovered-workspace";
- apps\web\src\app\dashboard\compliance\admin\page.tsx:4 — return <RecoveredWorkspace />;
- apps\web\src\app\dashboard\course-studio\page.tsx:1 — import { RecoveredWorkspace } from "@/components/recovered-workspace";
- apps\web\src\app\dashboard\course-studio\page.tsx:4 — return <RecoveredWorkspace />;
- apps\web\src\app\dashboard\files\page.tsx:1 — import { RecoveredWorkspace } from "@/components/recovered-workspace";
- apps\web\src\app\dashboard\files\page.tsx:4 — return <RecoveredWorkspace />;
- apps\web\src\app\dashboard\instructor\page.tsx:1 — import { RecoveredWorkspace } from "@/components/recovered-workspace";
- apps\web\src\app\dashboard\instructor\page.tsx:4 — return <RecoveredWorkspace />;
- apps\web\src\app\dashboard\instructors\page.tsx:1 — import { RecoveredWorkspace } from "@/components/recovered-workspace";
- apps\web\src\app\dashboard\instructors\page.tsx:4 — return <RecoveredWorkspace />;
- apps\web\src\app\dashboard\integrations\page.tsx:1 — import { RecoveredWorkspace } from "@/components/recovered-workspace";
- apps\web\src\app\dashboard\integrations\page.tsx:4 — return <RecoveredWorkspace />;
- apps\web\src\app\dashboard\ld-operations\page.tsx:1 — import { RecoveredWorkspace } from "@/components/recovered-workspace";
- apps\web\src\app\dashboard\ld-operations\page.tsx:4 — return <RecoveredWorkspace />;
- apps\web\src\app\dashboard\ld-operations\equivalencies\page.tsx:1 — import { RecoveredWorkspace } from "@/components/recovered-workspace";
- apps\web\src\app\dashboard\ld-operations\equivalencies\page.tsx:4 — return <RecoveredWorkspace />;
- apps\web\src\app\dashboard\learning-paths\page.tsx:1 — import { RecoveredWorkspace } from "@/components/recovered-workspace";
- apps\web\src\app\dashboard\learning-paths\page.tsx:4 — return <RecoveredWorkspace />;
- apps\web\src\app\dashboard\learning-paths\new\page.tsx:1 — import { RecoveredWorkspace } from "@/components/recovered-workspace";
- apps\web\src\app\dashboard\learning-paths\new\page.tsx:4 — return <RecoveredWorkspace />;
- apps\web\src\app\dashboard\manager\page.tsx:1 — import { RecoveredWorkspace } from "@/components/recovered-workspace";
- apps\web\src\app\dashboard\manager\page.tsx:4 — return <RecoveredWorkspace />;
- apps\web\src\app\dashboard\notifications\page.tsx:1 — import { RecoveredWorkspace } from "@/components/recovered-workspace";
- apps\web\src\app\dashboard\notifications\page.tsx:4 — return <RecoveredWorkspace />;
- apps\web\src\app\dashboard\organization\page.tsx:1 — import { RecoveredWorkspace } from "@/components/recovered-workspace";
- apps\web\src\app\dashboard\organization\page.tsx:4 — return <RecoveredWorkspace />;
- apps\web\src\app\dashboard\people\admin\page.tsx:1 — import { RecoveredWorkspace } from "@/components/recovered-workspace";
- apps\web\src\app\dashboard\people\admin\page.tsx:4 — return <RecoveredWorkspace />;
- apps\web\src\app\dashboard\sessions\page.tsx:1 — import { RecoveredWorkspace } from "@/components/recovered-workspace";
- apps\web\src\app\dashboard\sessions\page.tsx:4 — return <RecoveredWorkspace />;

## Duplicate Settings navigation
Settings references in workspace navigation: 2
- line 55: ["/dashboard/settings", "Platform Settings", Settings2],
- line 99: <Link className={`nav-item ${isActive("/dashboard/settings") ? "active" : ""}`} href="/dashboard/settings" aria-label="Settings" title="Settings">

## QA status at the time of this scan
PHASE 0 BASELINE: OPEN — defects identified; remediation required before phase exit.

This is a historical 2026-09-25 snapshot, superseded for the local foundation gate by `docs/06-delivery/PHASE_0_REBASELINE_2026-09-25.md`. It is not a current route inventory or a formal hosted-CI closure record. Current Phase 0 verification is tracked in `docs/06-delivery/PHASE_0_EXIT_EVIDENCE.md`.

Acceptance rule: route compilation is not functional acceptance; each route must render its intended screen and each interactive workflow must be verified through API and persistence.
