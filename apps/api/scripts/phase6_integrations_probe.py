import asyncio,json,urllib.request,websockets
async def c(ws,i,m,p=None):
 i+=1; await ws.send(json.dumps({"id":i,"method":m,"params":p or {}}))
 while True:
  x=json.loads(await ws.recv())
  if x.get("id")==i:return i,x
async def main():
 t=json.load(urllib.request.urlopen("http://127.0.0.1:9222/json")); page=next(x for x in t if x.get("type")=="page")
 async with websockets.connect(page["webSocketDebuggerUrl"]) as ws:
  i,_=await c(ws,0,"Page.navigate",{"url":"http://127.0.0.1:3000/dashboard/integrations"}); await asyncio.sleep(1.5)
  expr="""(()=>({url:location.href,forms:document.forms.length,buttons:[...document.querySelectorAll('button')].map(x=>x.textContent.trim()).filter(Boolean),headings:[...document.querySelectorAll('h1,h2,h3')].map(x=>x.textContent.trim()),body:(document.body.innerText||'').slice(0,2500)}))()"""
  i,r=await c(ws,i,"Runtime.evaluate",{"expression":expr,"returnByValue":True}); print(r["result"]["result"].get("value"))
asyncio.run(main())