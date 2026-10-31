#!/usr/bin/env python3
"""Deterministic, dependency-free release-hygiene audit for Kalam.

This audit intentionally checks only repository facts that can be proven from the
candidate source tree. It does not claim runtime, browser, AWS, DR, or production
certification.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "apps/api",
    "apps/web",
    "apps/api/requirements.txt",
    "apps/web/package.json",
    "package.json",
    "package-lock.json",
    ".github/workflows/ci.yml",
    "infra/docker/docker-compose.app.yml",
    "infra/reverse-proxy/nginx.conf",
    "docs/06-delivery/PHASE_8_RELEASE_RUNBOOK.md",
]

DASHBOARD_ROOTS = [
    ROOT / "apps/web/src/app/dashboard",
    ROOT / "apps/web/src/app/(dashboard)",
]

MARKER_RE = re.compile(
    r"(?i)\b(TODO|FIXME|PLACEHOLDER|SAMPLE DATA|MOCK DATA|COMING SOON|LOREM IPSUM)\b"
)

def files_under(paths: list[Path]):
    seen: set[Path] = set()
    for root in paths:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.is_file() and p.suffix in {".ts", ".tsx", ".js", ".jsx", ".md"} and p not in seen:
                seen.add(p)
                yield p

def main() -> int:
    checks: list[dict[str, object]] = []

    for rel in REQUIRED:
        ok = (ROOT / rel).exists()
        checks.append({"check": f"required:{rel}", "status": "PASS" if ok else "FAIL"})

    dashboard_files = list(files_under(DASHBOARD_ROOTS))
    marker_hits: list[dict[str, object]] = []
    for path in dashboard_files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if MARKER_RE.search(line):
                marker_hits.append({
                    "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "line": line_no,
                    "text": line.strip()[:240],
                })

    checks.append({
        "check": "dashboard:placeholder-markers",
        "status": "PASS" if not marker_hits else "FAIL",
        "details": marker_hits,
    })

    brand = ROOT / "apps/web/src/components/kalam-brand.tsx"
    checks.append({
        "check": "brand:canonical-kalam-component",
        "status": "PASS" if brand.exists() else "FAIL",
        "details": str(brand.relative_to(ROOT)) if brand.exists() else None,
    })

    manifest = ROOT / "apps/web/src/app/manifest.ts"
    static_manifest = ROOT / "apps/web/public/manifest.json"
    checks.append({
        "check": "web:manifest-source-present",
        "status": "PASS" if manifest.exists() or static_manifest.exists() else "WARN",
        "details": [str(p.relative_to(ROOT)) for p in (manifest, static_manifest) if p.exists()],
    })

    result = {
        "audit": "kalam-final-release-hygiene",
        "version": 1,
        "repository_root": str(ROOT),
        "dashboard_files_scanned": len(dashboard_files),
        "checks": checks,
        "summary": {
            "pass": sum(c["status"] == "PASS" for c in checks),
            "fail": sum(c["status"] == "FAIL" for c in checks),
            "warn": sum(c["status"] == "WARN" for c in checks),
        },
    }

    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["summary"]["fail"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
