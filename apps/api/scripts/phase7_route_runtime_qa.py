import asyncio
import json
import urllib.request
import httpx
import websockets

TENANT = "demo-corporation"
ADMIN = {"email": "admin@demo.corp", "password": "DemoOnly!1234"}
COOKIE = "corp_lms_session"
ROUTES = [
    "/dashboard", "/dashboard/ai", "/dashboard/analytics", "/dashboard/team",
    "/dashboard/webhooks", "/dashboard/skills/admin", "/dashboard/assessments/admin",
    "/dashboard/integrations", "/dashboard/reports", "/dashboard/settings",
]

async def call(ws, ident, method, params=None):
    ident += 1
    await ws.send(json.dumps({"id": ident, "method": method, "params": params or {}}))
    while True:
        item = json.loads(await ws.recv())
        if item.get("id") == ident:
            return ident, item

async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        response = await client.post("/api/v1/auth/login", json={"tenant_slug": TENANT, **ADMIN})
        response.raise_for_status()
        session_cookie = client.cookies.get(COOKIE)
    targets = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json"))
    page = next(item for item in targets if item.get("type") == "page")
    async with websockets.connect(page["webSocketDebuggerUrl"], max_size=20_000_000) as ws:
        ident, _ = await call(ws, 0, "Network.enable")
        ident, _ = await call(ws, ident, "Runtime.enable")
        ident, _ = await call(ws, ident, "Network.setCookie", {
            "name": COOKIE, "value": session_cookie, "domain": "127.0.0.1", "path": "/",
        })
        failures = []
        for route in ROUTES:
            ident, _ = await call(ws, ident, "Page.navigate", {"url": "http://127.0.0.1:3000" + route})
            await asyncio.sleep(1.0)
            expression = """(() => ({
              path: location.pathname,
              title: document.title,
              error: document.body.innerText.includes('Functions cannot be passed directly to Client Components'),
              workspaceError: document.body.innerText.includes('WORKSPACE ERROR'),
              body: document.body.innerText.slice(0, 240)
            }))()"""
            ident, result = await call(ws, ident, "Runtime.evaluate", {
                "expression": expression, "returnByValue": True,
            })
            value = result.get("result", {}).get("result", {}).get("value", {})
            print(route, json.dumps(value, ensure_ascii=False))
            if value.get("error") or value.get("workspaceError") or value.get("path") == "/login":
                failures.append(route)
        print("FAILURES", json.dumps(failures))
asyncio.run(main())
