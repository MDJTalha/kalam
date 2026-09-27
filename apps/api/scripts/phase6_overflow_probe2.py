import asyncio
import json
import urllib.request
import websockets

async def call(ws, ident, method, params=None):
    ident += 1
    await ws.send(json.dumps({"id": ident, "method": method, "params": params or {}}))
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
        await asyncio.sleep(1.2)
        expr="""(() => {
          const vw=document.documentElement.clientWidth;
          return {
            viewport:vw,
            scrollWidth:document.documentElement.scrollWidth,
            offenders:[...document.querySelectorAll('body *')].map(el=>{
              const r=el.getBoundingClientRect(); return {el, r, sidebar:!!el.closest('.sidebar')}
            }).filter(x=>!x.sidebar && x.r.right>vw+1).sort((a,b)=>b.r.right-a.r.right).slice(0,15).map(x=>({
              tag:x.el.tagName, cls:typeof x.el.className==='string'?x.el.className:'', right:Math.round(x.r.right), left:Math.round(x.r.left), width:Math.round(x.r.width), text:(x.el.textContent||'').trim().slice(0,100)
            }))
          }
        })()"""
        ident, result = await call(ws, ident, "Runtime.evaluate", {"expression":expr,"returnByValue":True})
        print(json.dumps(result["result"]["result"].get("value"), indent=2))
        await call(ws, ident, "Emulation.clearDeviceMetricsOverride")

asyncio.run(main())
