import asyncio, json, urllib.request
import httpx, websockets

TENANT="demo-corporation"
ADMIN={"email":"admin@demo.corp","password":"DemoOnly!1234"}
COOKIE_NAME="corp_lms_session"

async def call(ws, i, method, params=None):
    i += 1
    await ws.send(json.dumps({"id": i, "method": method, "params": params or {}}))
    while True:
        item=json.loads(await ws.recv())
        if item.get("id")==i:
            return i,item

async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as c:
        r=await c.post("/api/v1/auth/login",json={"tenant_slug":TENANT,**ADMIN})
        r.raise_for_status()
        cookie=c.cookies.get(COOKIE_NAME)
    targets=json.load(urllib.request.urlopen("http://127.0.0.1:9222/json"))
    page=next(x for x in targets if x.get("type")=="page")
    async with websockets.connect(page["webSocketDebuggerUrl"],max_size=20_000_000) as ws:
        i,_=await call(ws,0,"Network.enable")
        i,_=await call(ws,i,"Network.setCookie",{"name":COOKIE_NAME,"value":cookie,"domain":"127.0.0.1","path":"/"})
        for u in ["http://127.0.0.1:3000/dashboard","http://127.0.0.1:3000/dashboard/reports"]:
            i,_=await call(ws,i,"Page.navigate",{"url":u})
            await asyncio.sleep(3)
            i,res=await call(ws,i,"Runtime.evaluate",{"expression":"({url:location.href,login:location.pathname==='/login',title:document.title})","returnByValue":True})
            print(json.dumps(res["result"]["result"].get("value"),ensure_ascii=False))
        i,_=await call(ws,i,"Page.navigate",{"url":"http://127.0.0.1:3000/dashboard"})
        await asyncio.sleep(2)
        expr="""(()=>{const a=[...document.querySelectorAll('a')].find(x=>(x.textContent||'').toLowerCase().includes('analytics')); if(!a)return {found:false,url:location.href}; a.click(); return {found:true,text:a.textContent.trim(),href:a.href};})()"""
        i,res=await call(ws,i,"Runtime.evaluate",{"expression":expr,"returnByValue":True})
        print("CLICK",json.dumps(res["result"]["result"].get("value"),ensure_ascii=False))
        await asyncio.sleep(3)
        i,res=await call(ws,i,"Runtime.evaluate",{"expression":"({url:location.href,path:location.pathname,login:location.pathname==='/login',title:document.title})","returnByValue":True})
        print("AFTER",json.dumps(res["result"]["result"].get("value"),ensure_ascii=False))
asyncio.run(main())
