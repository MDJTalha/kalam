import asyncio, json, urllib.request
import httpx, websockets

TENANT = "demo-corporation"
ADMIN = {"email": "admin@demo.corp", "password": "DemoOnly!1234"}
COOKIE = "corp_lms_session"

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
        cookie = client.cookies.get(COOKIE)
    targets = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json"))
    page = next(item for item in targets if item.get("type") == "page")
    async with websockets.connect(page["webSocketDebuggerUrl"], max_size=20_000_000) as ws:
        ident, _ = await call(ws, 0, "Network.enable")
        ident, _ = await call(ws, ident, "Network.setCookie", {"name": COOKIE, "value": cookie, "domain": "127.0.0.1", "path": "/"})
        for width, height, label in [(1440, 1000, "desktop"), (390, 844, "mobile")]:
            ident, _ = await call(ws, ident, "Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": width < 600})
            ident, _ = await call(ws, ident, "Page.navigate", {"url": "http://127.0.0.1:3000/dashboard/ai"})
            await asyncio.sleep(1.5)
            expr = """(() => ({
              path: location.pathname,
              horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
              unlabeledFields: [...document.querySelectorAll('input,select,textarea')].filter(x=>{
                const explicit = x.id && [...document.querySelectorAll('label')].some(l=>l.htmlFor===x.id);
                return !(x.getAttribute('aria-label')||x.getAttribute('aria-labelledby')||x.closest('label')||explicit);
              }).length,
              buttonsWithoutName: [...document.querySelectorAll('button')].filter(x=>!(x.innerText.trim()||x.getAttribute('aria-label')||x.getAttribute('title'))).length,
              h1: document.querySelector('h1')?.textContent?.trim() || null
            }))()"""
            ident, result = await call(ws, ident, "Runtime.evaluate", {"expression": expr, "returnByValue": True})
            print(label, json.dumps(result.get("result", {}).get("result", {}).get("value", {}), ensure_ascii=False))
        ident, _ = await call(ws, ident, "Emulation.clearDeviceMetricsOverride")
asyncio.run(main())
