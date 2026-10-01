import asyncio, json, time, requests, websockets, base64, pathlib

PORT=9333
OUT=pathlib.Path(r"C:\Projects\CorpLMS\qa\brand-ui")
targets=[
    ("landing-cdp","http://127.0.0.1:3000/"),
    ("login-cdp","http://127.0.0.1:3000/login"),
    ("pricing-cdp","http://127.0.0.1:3000/pricing"),
]

async def cmd(ws, i, method, params=None):
    await ws.send(json.dumps({"id":i,"method":method,"params":params or {}}))
    while True:
        msg=json.loads(await ws.recv())
        if msg.get("id")==i:
            return msg

async def main():
    tabs=requests.get(f"http://127.0.0.1:{PORT}/json",timeout=5).json()
    page=[x for x in tabs if x.get("type")=="page"][0]
    async with websockets.connect(page["webSocketDebuggerUrl"],max_size=2**25) as ws:
        i=1
        await cmd(ws,i,"Emulation.setDeviceMetricsOverride",{"width":390,"height":844,"deviceScaleFactor":1,"mobile":True,"screenWidth":390,"screenHeight":844}); i+=1
        await cmd(ws,i,"Emulation.setVisibleSize",{"width":390,"height":844}); i+=1
        for name,url in targets:
            await cmd(ws,i,"Page.navigate",{"url":url}); i+=1
            await asyncio.sleep(2)
            expr="""({
              innerWidth:innerWidth, innerHeight:innerHeight, dpr:devicePixelRatio,
              clientWidth:document.documentElement.clientWidth, scrollWidth:document.documentElement.scrollWidth,
              bodyScroll:document.body.scrollWidth,
              header:document.querySelector('header')?.getBoundingClientRect().toJSON(),
              logo:document.querySelector('header img')?.getBoundingClientRect().toJSON(),
              heroGrid:document.querySelector('[class*=heroGrid]')?.getBoundingClientRect().toJSON(),
              heroVisual:document.querySelector('[class*=heroVisual]')?.getBoundingClientRect().toJSON(),
              auth:document.querySelector('.k-auth')?.getBoundingClientRect().toJSON(),
              card:document.querySelector('.auth-card')?.getBoundingClientRect().toJSON()
            })"""
            res=await cmd(ws,i,"Runtime.evaluate",{"expression":expr,"returnByValue":True}); i+=1
            print(name,json.dumps(res["result"]["result"].get("value")),flush=True)
            shot=await cmd(ws,i,"Page.captureScreenshot",{"format":"png","captureBeyondViewport":False}); i+=1
            (OUT/f"{name}.png").write_bytes(base64.b64decode(shot["result"]["data"]))

asyncio.run(main())
