import asyncio
import base64
import json
import sys
import urllib.request
from pathlib import Path

import httpx
import websockets

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.config import settings
from tests.test_foundation_api import ADMIN, TENANT

SCREEN_DIR = Path("C:/Projects/CorpLMS/qa")
SCREEN_DIR.mkdir(parents=True, exist_ok=True)

async def cdp(ws, ident, method, params=None):
    ident += 1
    message = {"id": ident, "method": method}
    if params is not None:
        message["params"] = params
    await ws.send(json.dumps(message))
    while True:
        data = json.loads(await ws.recv())
        if data.get("id") == ident:
            return ident, data

async def run():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        response = await client.post("/api/v1/auth/login", json={"tenant_slug": TENANT, **ADMIN})
        response.raise_for_status()
        session_cookie = client.cookies.get(settings.session_cookie_name)
    targets = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json"))
    page = next(item for item in targets if item.get("type") == "page")
    async with websockets.connect(page["webSocketDebuggerUrl"], max_size=20_000_000) as ws:
        ident = 0
        ident, _ = await cdp(ws, ident, "Network.enable")
        ident, _ = await cdp(ws, ident, "Network.setCookie", {"name": settings.session_cookie_name, "value": session_cookie, "domain": "127.0.0.1", "path": "/"})
        for width, height, name in [(1440, 1000, "reports-desktop"), (390, 844, "reports-mobile")]:
            ident, _ = await cdp(ws, ident, "Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": width < 600})
            ident, _ = await cdp(ws, ident, "Page.navigate", {"url": "http://127.0.0.1:3000/dashboard/reports"})
            await asyncio.sleep(1.5)
            ident, result = await cdp(ws, ident, "Runtime.evaluate", {"expression": """(() => ({
              title: document.title,
              url: location.href,
              scrollWidth: document.documentElement.scrollWidth,
              clientWidth: document.documentElement.clientWidth,
              horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
              unlabeledFields: [...document.querySelectorAll('input,select,textarea')].filter(x=>!(x.getAttribute('aria-label')||x.getAttribute('aria-labelledby')||x.closest('label'))).length,
              headings: [...document.querySelectorAll('h1,h2,h3')].map(x=>x.textContent?.trim()).filter(Boolean)
            }))()""", "returnByValue": True})
            print(name, result.get("result", {}).get("result", {}).get("value"))
            ident, shot = await cdp(ws, ident, "Page.captureScreenshot", {"format": "png"})
            (SCREEN_DIR / f"{name}.png").write_bytes(base64.b64decode(shot["result"]["data"]))
        ident, _ = await cdp(ws, ident, "Emulation.clearDeviceMetricsOverride")
        ident, _ = await cdp(ws, ident, "Page.navigate", {"url": "http://127.0.0.1:3000/dashboard/integrations"})
        await asyncio.sleep(1.5)
        ident, result = await cdp(ws, ident, "Runtime.evaluate", {"expression": """(() => ({
          title: document.title,
          url: location.href,
          testButtons: [...document.querySelectorAll('button')].filter(x=>(x.textContent||'').includes('Test connection')).length,
          unlabeledFields: [...document.querySelectorAll('input,select,textarea')].filter(x=>!(x.getAttribute('aria-label')||x.getAttribute('aria-labelledby')||x.closest('label'))).length
        }))()""", "returnByValue": True})
        print("integrations", result.get("result", {}).get("result", {}).get("value"))

asyncio.run(run())
