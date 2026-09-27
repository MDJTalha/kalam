import asyncio
import json
import urllib.request
import websockets

async def call(ws, ident, method, params=None):
    ident += 1
    payload = {"id": ident, "method": method}
    if params is not None:
        payload["params"] = params
    await ws.send(json.dumps(payload))
    while True:
        item = json.loads(await ws.recv())
        if item.get("id") == ident:
            return ident, item

async def main():
    targets = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json"))
    page = next(x for x in targets if x.get("type") == "page")
    async with websockets.connect(page["webSocketDebuggerUrl"], max_size=20_000_000) as ws:
        ident, _ = await call(ws, 0, "Emulation.setDeviceMetricsOverride", {"width":390,"height":844,"deviceScaleFactor":1,"mobile":True})
        ident, _ = await call(ws, ident, "Page.navigate", {"url":"http://127.0.0.1:3000/dashboard/reports"})
        await asyncio.sleep(1.5)
        expression = """(() => [...document.querySelectorAll('body *')].map(el => {
          const r=el.getBoundingClientRect(); return {tag:el.tagName,cls:typeof el.className==='string'?el.className:'',id:el.id,right:Math.round(r.right),width:Math.round(r.width),left:Math.round(r.left),text:(el.textContent||'').trim().slice(0,80)}
        }).filter(x=>x.right>391).sort((a,b)=>b.right-a.right).slice(0,20))()"""
        ident, result = await call(ws, ident, "Runtime.evaluate", {"expression":expression,"returnByValue":True})
        print(json.dumps(result["result"]["result"].get("value"), indent=2))
        await call(ws, ident, "Emulation.clearDeviceMetricsOverride")

asyncio.run(main())
