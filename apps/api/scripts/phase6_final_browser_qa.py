import asyncio
import base64
import json
import urllib.request
from pathlib import Path

import httpx
import sys
import websockets

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.test_foundation_api import ADMIN, TENANT

OUT = Path("C:/Projects/CorpLMS/qa")
OUT.mkdir(parents=True, exist_ok=True)

async def call(ws, ident, method, params=None):
    ident += 1
    await ws.send(json.dumps({"id": ident, "method": method, "params": params or {}}))
    while True:
        item = json.loads(await ws.recv())
        if item.get("id") == ident:
            return ident, item

async def inspect(ws, ident, width, height, url, name):
    ident, _ = await call(ws, ident, "Emulation.setDeviceMetricsOverride", {
        "width": width, "height": height, "deviceScaleFactor": 1, "mobile": width < 600,
    })
    ident, _ = await call(ws, ident, "Page.navigate", {"url": url})
    await asyncio.sleep(6)
    expression = """(() => {
      const text = document.body.innerText || "";
      const root = document.documentElement;
      return {
        url: location.href,
        width: root.clientWidth,
        scrollWidth: root.scrollWidth,
        overflow: root.scrollWidth > root.clientWidth + 1,
        workspaceError: text.includes("WORKSPACE ERROR"),
        workspaceLoading: text.includes("Loading learning workspace"),
        courseLoadError: text.includes("Course performance could not be loaded"),
        headings: [...document.querySelectorAll("h1,h2,h3")].map(x => x.textContent?.trim()).filter(Boolean),
        unlabeledFields: [...document.querySelectorAll("input,select,textarea")].filter(
          x => !(x.getAttribute("aria-label") || x.getAttribute("aria-labelledby") || x.closest("label"))
        ).length
      };
    })()"""
    ident, result = await call(ws, ident, "Runtime.evaluate", {
        "expression": expression, "returnByValue": True
    })
    screenshot = await call(ws, ident, "Page.captureScreenshot", {"format": "png"})
    ident, shot = screenshot
    (OUT / f"{name}.png").write_bytes(base64.b64decode(shot["result"]["data"]))
    print(name, json.dumps(result["result"]["result"].get("value"), ensure_ascii=False))
    return ident

async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        response = await client.post("/api/v1/auth/login", json={"tenant_slug": TENANT, **ADMIN})
        response.raise_for_status()
        cookie_name = "corp_lms_session"
        cookie = client.cookies.get(cookie_name)

    targets = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json"))
    page = next(x for x in targets if x.get("type") == "page")
    async with websockets.connect(page["webSocketDebuggerUrl"], max_size=20_000_000) as ws:
        ident = 0
        ident, _ = await call(ws, ident, "Network.enable")
        ident, _ = await call(ws, ident, "Network.setCookie", {
            "name": cookie_name, "value": cookie, "domain": "127.0.0.1", "path": "/"
        })
        ident = await inspect(ws, ident, 1440, 1000, "http://127.0.0.1:3000/dashboard/reports", "phase6-reports-desktop")
        ident = await inspect(ws, ident, 390, 844, "http://127.0.0.1:3000/dashboard/reports", "phase6-reports-mobile")
        ident = await inspect(ws, ident, 390, 844, "http://127.0.0.1:3000/dashboard/integrations", "phase6-integrations-mobile")
        await call(ws, ident, "Emulation.clearDeviceMetricsOverride")

asyncio.run(main())
