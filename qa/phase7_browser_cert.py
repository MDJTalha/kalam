import asyncio
import json
import urllib.request

import httpx
import websockets

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
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=30.0) as client:
        response = await client.post("/api/v1/auth/login", json={"tenant_slug": TENANT, **ADMIN})
        response.raise_for_status()
        cookie = client.cookies.get(COOKIE)
    targets = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json"))
    page = next(item for item in targets if item.get("type") == "page")
    async with websockets.connect(page["webSocketDebuggerUrl"], max_size=20_000_000) as ws:
        ident, _ = await call(ws, 0, "Network.enable")
        ident, _ = await call(ws, ident, "Network.setCookie", {
            "name": COOKIE, "value": cookie, "domain": "127.0.0.1", "path": "/",
        })
        for width, height, name in [(1440, 1000, "desktop"), (390, 844, "mobile")]:
            ident, _ = await call(ws, ident, "Emulation.setDeviceMetricsOverride", {
                "width": width, "height": height, "deviceScaleFactor": 1, "mobile": width < 600,
            })
            ident, _ = await call(ws, ident, "Page.navigate", {
                "url": "http://127.0.0.1:3000/dashboard/capability-gaps",
            })
            await asyncio.sleep(25.0)
            expression = """(() => ({
              path: location.pathname,
              overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
              unlabeled: [...document.querySelectorAll('input,select,textarea')].filter(x => !(x.getAttribute('aria-label') || x.getAttribute('aria-labelledby') || x.closest('label') || (x.id && document.querySelector('label[for="' + CSS.escape(x.id) + '"]')))).length,
              h1: [...document.querySelectorAll('h1')].map(x => x.textContent?.trim()).filter(Boolean),
              h2: [...document.querySelectorAll('h2')].map(x => x.textContent?.trim()).filter(Boolean),
              body: document.body.innerText.slice(0, 240),
              media760: matchMedia("(max-width:760px)").matches,
              sectionActions: [...document.querySelectorAll(".section-actions")].slice(0,3).map(x => ({display:getComputedStyle(x).display, flexWrap:getComputedStyle(x).flexWrap, width:Math.round(x.getBoundingClientRect().width), parent:getComputedStyle(x.parentElement).flexDirection, parentClass:x.parentElement?.className?.toString()})),
              overflowElements: [...document.querySelectorAll('*')].filter(x => x.getBoundingClientRect().right > document.documentElement.clientWidth + 1).slice(0, 12).map(x => ({tag: x.tagName, text: x.innerText?.slice(0, 60), cls: x.className?.toString().slice(0, 100), right: Math.round(x.getBoundingClientRect().right), width: Math.round(x.getBoundingClientRect().width), parent: x.parentElement?.className?.toString().slice(0, 100)})),
              reviewButtons: [...document.querySelectorAll('button')].filter(x => ['Approve','Reject'].includes((x.textContent||'').trim())).length
            }))()"""
            ident, result = await call(ws, ident, "Runtime.evaluate", {
                "expression": expression, "returnByValue": True,
            })
            print(name, json.dumps(result["result"]["result"].get("value"), ensure_ascii=False))
asyncio.run(main())


