import asyncio
import json
import os
import urllib.request
import httpx
import websockets

TENANT="demo-corporation"
ADMIN={"email":"admin@demo.corp","password":"DemoOnly!1234"}
COOKIE="corp_lms_session"
DEBUG_PORT=os.getenv("BROWSER_DEBUG_PORT", "9222")
ALIASES = {
    "/dashboard/instructor": {"/dashboard/instructor", "/dashboard/sessions"},
    "/dashboard/instructors": {"/dashboard/instructors", "/dashboard/sessions"},
    "/dashboard/manager": {"/dashboard/manager", "/dashboard/team"},
}

ROUTES=[
"/dashboard","/dashboard/admin","/dashboard/ai","/dashboard/analytics",
"/dashboard/assessments","/dashboard/assessments/admin","/dashboard/audit",
"/dashboard/catalog","/dashboard/catalog/categories","/dashboard/catalog/new",
"/dashboard/certificates","/dashboard/certificates/admin","/dashboard/compliance",
"/dashboard/compliance/admin","/dashboard/course-studio","/dashboard/development",
"/dashboard/files","/dashboard/instructor","/dashboard/instructors",
"/dashboard/integrations","/dashboard/ld-operations","/dashboard/ld-operations/equivalencies",
"/dashboard/learning-paths","/dashboard/learning-paths/new","/dashboard/manager",
"/dashboard/notifications","/dashboard/organization","/dashboard/people",
"/dashboard/people/admin","/dashboard/programs","/dashboard/reports",
"/dashboard/search","/dashboard/sessions","/dashboard/settings",
"/dashboard/settings/sessions","/dashboard/skills","/dashboard/skills/admin",
"/dashboard/team","/dashboard/webhooks"
]
if os.getenv("CERT_ROUTES"):
    ROUTES = [route for route in ROUTES if route in os.environ["CERT_ROUTES"].split(",")]

async def call(ws, ident, method, params=None):
    ident += 1
    await ws.send(json.dumps({"id":ident,"method":method,"params":params or {}}))
    while True:
        item=json.loads(await ws.recv())
        if item.get("id")==ident:
            return ident,item
async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as c:
        r=await c.post("/api/v1/auth/login",json={"tenant_slug":TENANT,**ADMIN})
        r.raise_for_status()
        cookie=c.cookies.get(COOKIE)
    targets=json.load(urllib.request.urlopen(f"http://127.0.0.1:{DEBUG_PORT}/json"))
    page=next(x for x in targets if x.get("type")=="page")
    async with websockets.connect(page["webSocketDebuggerUrl"],max_size=20_000_000) as ws:
        ident,_=await call(ws,0,"Network.enable")
        ident,_=await call(ws,ident,"Runtime.enable")
        ident,_=await call(ws,ident,"Network.setCookie",{"name":COOKIE,"value":cookie,"domain":"127.0.0.1","path":"/"})
        failures=[]
        results=[]
        for width,height,label in [(1440,1000,"desktop"),(390,844,"mobile")]:
            ident,_=await call(ws,ident,"Emulation.setDeviceMetricsOverride",{"width":width,"height":height,"deviceScaleFactor":1,"mobile":width<600})
            for route in ROUTES:
                ident,_=await call(ws,ident,"Page.navigate",{"url":"http://127.0.0.1:3000"+route})
                await asyncio.sleep(0.9)
                expr="""(() => {
                  const fields=[...document.querySelectorAll('input,select,textarea')];
                  const unlabeled=fields.filter(x=>{
                    const explicit=x.id && [...document.querySelectorAll('label')].some(l=>l.htmlFor===x.id);
                    return !(x.getAttribute('aria-label')||x.getAttribute('aria-labelledby')||x.closest('label')||explicit);
                  }).length;
                  return {
                    path:location.pathname,
                    overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1,
                    widths:{document:document.documentElement.scrollWidth,viewport:document.documentElement.clientWidth,body:document.body.scrollWidth,sidebar:document.querySelector('.sidebar')?.getBoundingClientRect().width,nav:document.querySelector('.sidebar-nav')?.getBoundingClientRect().width},
                    overflowSources:[...document.querySelectorAll('body *')].filter(x=>x.getBoundingClientRect().right>document.documentElement.clientWidth+1 && x.getBoundingClientRect().width>0 && !x.closest('.sidebar-nav')).slice(0,20).map(x=>({tag:x.tagName,cls:String(x.className).slice(0,100),right:Math.round(x.getBoundingClientRect().right)})),
                    unlabeled,
                    unnamedButtons:[...document.querySelectorAll('button')].filter(x=>!(x.innerText.trim()||x.getAttribute('aria-label')||x.getAttribute('title'))).length,
                    serializationError:document.body.innerText.includes('Functions cannot be passed directly to Client Components'),
                    hasErrorBoundary:/Application error|Internal Server Error/.test(document.body.innerText),
                    loading:/Loading learning workspace/.test(document.body.innerText),
                    h1:document.querySelector('h1')?.textContent?.trim()||null
                  };
                })()"""
                ident,res=await call(ws,ident,"Runtime.evaluate",{"expression":expr,"returnByValue":True})
                value=res.get("result",{}).get("result",{}).get("value",{})
                expected_paths=ALIASES.get(route,{route})
                for _ in range(16):
                    if isinstance(value, dict) and value.get("path") in expected_paths and not value.get("loading"):
                        break
                    await asyncio.sleep(0.5)
                    ident,res=await call(ws,ident,"Runtime.evaluate",{"expression":expr,"returnByValue":True})
                    value=res.get("result",{}).get("result",{}).get("value",{})
                bad=(
                    not isinstance(value,dict)
                    or not value.get("path")
                    or value.get("path")=="/login"
                    or value.get("path") not in expected_paths
                    or value.get("overflow")
                    or value.get("unlabeled",0)>0
                    or value.get("unnamedButtons",0)>0
                    or value.get("serializationError")
                    or value.get("hasErrorBoundary")
                    or value.get("loading")
                )
                results.append({"viewport":label,"route":route,**value})
                if bad:
                    failures.append({"viewport":label,"route":route,**value})
                print(label,route,json.dumps(value,ensure_ascii=False))
        ident,_=await call(ws,ident,"Emulation.clearDeviceMetricsOverride")
        print("FAILURES",json.dumps(failures,ensure_ascii=False))
        print("SUMMARY",json.dumps({"checks":len(results),"failures":len(failures)}))
        if failures:
            raise SystemExit(f"Browser release certification failed: {len(failures)} route checks")
asyncio.run(main())
