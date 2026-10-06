"""Focused local axe audit in a disposable Chrome DevTools tab."""
import asyncio
import json
import os
import urllib.request
from pathlib import Path

import httpx
import websockets

ROOT = Path(__file__).resolve().parents[3]
AXE = (ROOT / "node_modules" / "axe-core" / "axe.min.js").read_text(encoding="utf-8")
ROUTES = os.getenv("AXE_ROUTES", "/dashboard,/dashboard/compliance,/dashboard/compliance/admin,/dashboard/catalog,/dashboard/people,/dashboard/settings").split(",")
PORT = os.getenv("BROWSER_DEBUG_PORT", "9222")
WEB_BASE_URL = os.getenv("AXE_WEB_BASE_URL", "http://127.0.0.1:3000").rstrip("/")
AUTH_URL = os.getenv("AXE_AUTH_URL", "http://127.0.0.1:8000/api/v1/auth/login")
COOKIE = "corp_lms_session"
ROUTE_READY_ATTEMPTS = int(os.getenv("AXE_ROUTE_READY_ATTEMPTS", "120"))
ALIASES = {
    "/dashboard/instructor": {"/dashboard/instructor", "/dashboard/sessions"},
    "/dashboard/instructors": {"/dashboard/instructors", "/dashboard/sessions"},
    "/dashboard/manager": {"/dashboard/manager", "/dashboard/team"},
}


async def call(ws, seq, method, params=None):
    seq += 1
    await ws.send(json.dumps({"id": seq, "method": method, "params": params or {}}))
    while True:
        response = json.loads(await ws.recv())
        if response.get("id") == seq:
            if "error" in response:
                raise RuntimeError(f"CDP {method}: {response['error']}")
            return seq, response.get("result", {})


async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        auth = await client.post(AUTH_URL, json={"tenant_slug": "demo-corporation", "email": "admin@demo.corp", "password": "DemoOnly!1234"})
        auth.raise_for_status()
        session = client.cookies.get(COOKIE)
        if not session:
            raise RuntimeError("Demo login did not issue a session cookie")
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?about:blank", method="PUT")
    target = json.load(urllib.request.urlopen(req, timeout=8))
    results = []
    try:
        async with websockets.connect(target["webSocketDebuggerUrl"], max_size=30_000_000) as ws:
            seq, _ = await call(ws, 0, "Page.enable")
            seq, _ = await call(ws, seq, "Runtime.enable")
            seq, _ = await call(ws, seq, "Network.enable")
            seq, _ = await call(ws, seq, "Network.setCookie", {"name": COOKIE, "value": session, "url": WEB_BASE_URL})
            seq, _ = await call(ws, seq, "Page.addScriptToEvaluateOnNewDocument", {"source": AXE})
            for width, height, label in [(1440, 1000, "desktop"), (390, 844, "mobile")]:
                seq, _ = await call(ws, seq, "Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": width < 600})
                for route in ROUTES:
                    expected_paths = ALIASES.get(route, {route})
                    seq, _ = await call(ws, seq, "Page.navigate", {"url": WEB_BASE_URL + route})
                    for _ in range(ROUTE_READY_ATTEMPTS):
                        await asyncio.sleep(0.5)
                        seq, state = await call(ws, seq, "Runtime.evaluate", {"expression": "({path:location.pathname,loading:document.body.innerText.includes('Loading learning workspace'),h1:!!document.querySelector('h1')})", "returnByValue": True})
                        value = state.get("result", {}).get("value", {})
                        if value.get("path") in expected_paths and value.get("h1") and not value.get("loading"):
                            break
                    if value.get("path") not in expected_paths or not value.get("h1") or value.get("loading"):
                        raise RuntimeError(f"Route not ready: {route} {value}")
                    expression = "axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','best-practice']}}).then(r=>({violations:r.violations.map(v=>({id:v.id,impact:v.impact,description:v.description,node_count:v.nodes.length,nodes:v.nodes.slice(0,30).map(n=>({target:n.target,summary:n.failureSummary}))})),incomplete:r.incomplete.map(v=>({id:v.id,impact:v.impact,description:v.description,node_count:v.nodes.length,nodes:v.nodes.slice(0,30).map(n=>({target:n.target,summary:n.failureSummary}))})),passes:r.passes.length}))"
                    seq, audit = await call(ws, seq, "Runtime.evaluate", {"expression": expression, "awaitPromise": True, "returnByValue": True})
                    if "exceptionDetails" in audit:
                        raise RuntimeError(f"axe failed for {route}: {audit['exceptionDetails']}")
                    report = audit.get("result", {}).get("value")
                    if not report:
                        raise RuntimeError(f"axe returned no data for {route}")
                    results.append({"viewport": label, "route": route, **report})
                    print(label, route, "violations", len(report["violations"]))
    finally:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/close/{target['id']}", timeout=8).close()
        except Exception:
            pass
    output = Path(os.getenv("AXE_OUTPUT", str(ROOT / "qa" / "phase8-axe-run.json")))
    output.write_text(json.dumps({"checks": len(results), "results": results}, indent=2), encoding="utf-8")
    violations = sum(len(entry["violations"]) for entry in results)
    manual_review = sum(len(entry["incomplete"]) for entry in results)
    print(json.dumps({"checks": len(results), "violations": violations, "manual_review": manual_review, "report": str(output)}))
    if violations:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
