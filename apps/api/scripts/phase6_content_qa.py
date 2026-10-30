import asyncio
import json
import urllib.request
import websockets
async def c(ws,i,m,p=None):
 i+=1; await ws.send(json.dumps({"id":i,"method":m,"params":p or {}}))
 while True:
  x=json.loads(await ws.recv())
  if x.get("id")==i:return i,x
async def main():
 t=json.load(urllib.request.urlopen("http://127.0.0.1:9222/json")); page=next(x for x in t if x.get("type")=="page")
 async with websockets.connect(page["webSocketDebuggerUrl"]) as ws:
  for url in ["http://127.0.0.1:3000/dashboard/reports","http://127.0.0.1:3000/dashboard/integrations"]:
   i,_=await c(ws,0,"Page.navigate",{"url":url}); await asyncio.sleep(2)
   expr="""(()=>({url:location.href,title:document.title,body:(document.body.innerText||'').slice(0,1800),workspaceError:(document.body.innerText||'').includes('WORKSPACE ERROR'),headings:[...document.querySelectorAll('h1,h2,h3')].map(x=>x.textContent?.trim()).filter(Boolean)}))()"""
   i,r=await c(ws,i,"Runtime.evaluate",{"expression":expr,"returnByValue":True}); print(json.dumps(r["result"]["result"].get("value"),indent=2))
asyncio.run(main())