import asyncio, json, time, requests, websockets

time.sleep(1)
tabs = requests.get("http://127.0.0.1:9222/json", timeout=5).json()
pages = [x for x in tabs if x.get("type") == "page"]
print("pages", [(p.get("title"), p.get("url")) for p in pages], flush=True)
ws_url = pages[0]["webSocketDebuggerUrl"]

async def main():
    async with websockets.connect(ws_url, max_size=2**22) as ws:
        expr = """({
          innerWidth: window.innerWidth,
          innerHeight: window.innerHeight,
          dpr: window.devicePixelRatio,
          clientWidth: document.documentElement.clientWidth,
          scrollWidth: document.documentElement.scrollWidth,
          bodyWidth: document.body.getBoundingClientRect().width,
          bodyScroll: document.body.scrollWidth,
          heroGrid: document.querySelector('[class*=heroGrid]')?.getBoundingClientRect().toJSON(),
          heroVisual: document.querySelector('[class*=heroVisual]')?.getBoundingClientRect().toJSON(),
          brand: document.querySelector('header img')?.getBoundingClientRect().toJSON()
        })"""
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": expr, "returnByValue": True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("id") == 1:
                print(json.dumps(msg, indent=2), flush=True)
                break

asyncio.run(main())
