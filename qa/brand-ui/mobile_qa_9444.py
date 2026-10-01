import asyncio, json, requests, websockets, base64, pathlib

PORT=9444
OUT=pathlib.Path(r"C:\Projects\CorpLMS\qa\brand-ui")
targets=[
    ("landing-qa","http://127.0.0.1:3000/"),
    ("login-qa","http://127.0.0.1:3000/login"),
    ("pricing-qa","http://127.0.0.1:3000/pricing"),
]

async def recv_id(ws, req_id):
    while True:
        msg=json.loads(await ws.recv())
        if msg.get("id")==req_id:
            return msg

async def send(ws, req_id, method, params=None):
    await ws.send(json.dumps({"id":req_id,"method":method,"params":params or {}}))
    return await recv_id(ws, req_id)

async def main():
    tabs=requests.get(f"http://127.0.0.1:{PORT}/json",timeout=5).json()
    page=[x for x in tabs if x.get("type")=="page"][0]
    async with websockets.connect(page["webSocketDebuggerUrl"],max_size=2**25) as ws:
        i=1
        await send(ws,i,"Emulation.setDeviceMetricsOverride",{"width":390,"height":844,"deviceScaleFactor":1,"mobile":True,"screenWidth":390,"screenHeight":844}); i+=1
        await send(ws,i,"Page.enable"); i+=1
        for name,url in targets:
            await send(ws,i,"Page.navigate",{"url":url}); i+=1
            await asyncio.sleep(1.5)
            expr="""({
              href:location.href,
              innerWidth:innerWidth, innerHeight:innerHeight, dpr:devicePixelRatio,
              clientWidth:document.documentElement.clientWidth,
              scrollWidth:document.documentElement.scrollWidth,
              bodyWidth:document.body.getBoundingClientRect().width,
              bodyScroll:document.body.scrollWidth,
              header:document.querySelector('header')?.getBoundingClientRect().toJSON(),
              logo:document.querySelector('header img')?.getBoundingClientRect().toJSON(),
              authLogo:document.querySelector('.k-mobile-brand img')?.getBoundingClientRect().toJSON(),
              heroGrid:document.querySelector('[class*=heroGrid]')?.getBoundingClientRect().toJSON(),
              heroVisual:document.querySelector('[class*=heroVisual]')?.getBoundingClientRect().toJSON(),
              auth:document.querySelector('.k-auth')?.getBoundingClientRect().toJSON(),
              card:document.querySelector('.auth-card')?.getBoundingClientRect().toJSON(),
              container:document.querySelector('[class*=container]')?.getBoundingClientRect().toJSON()
            })"""
            res=await send(ws,i,"Runtime.evaluate",{"expression":expr,"returnByValue":True}); i+=1
            print(name, json.dumps(res["result"]["result"].get("value")), flush=True)
            shot=await send(ws,i,"Page.captureScreenshot",{"format":"png","fromSurface":True,"captureBeyondViewport":False}); i+=1
            (OUT/f"{name}.png").write_bytes(base64.b64decode(shot["result"]["data"]))

asyncio.run(main())
