import asyncio,json,urllib.request,websockets
async def c(ws,i,m,p=None):
 i+=1; await ws.send(json.dumps({"id":i,"method":m,"params":p or {}}))
 while True:
  x=json.loads(await ws.recv())
  if x.get("id")==i:return i,x
async def main():
 t=json.load(urllib.request.urlopen("http://127.0.0.1:9222/json")); page=next(x for x in t if x.get("type")=="page")
 async with websockets.connect(page["webSocketDebuggerUrl"]) as ws:
  i,_=await c(ws,0,"Emulation.clearDeviceMetricsOverride")
  i,_=await c(ws,i,"Page.navigate",{"url":"http://127.0.0.1:3000/dashboard/reports"}); await asyncio.sleep(3)
  i,_=await c(ws,i,"Emulation.setDeviceMetricsOverride",{"width":390,"height":844,"deviceScaleFactor":1,"mobile":True})
  await asyncio.sleep(2)
  expr="""(()=>({innerWidth:window.innerWidth,clientWidth:document.documentElement.clientWidth,media760:matchMedia('(max-width:760px)').matches,scrollWidth:document.documentElement.scrollWidth,grid:getComputedStyle(document.querySelector('.app-shell')).gridTemplateColumns,workspace:getComputedStyle(document.querySelector('.workspace')).width}))()"""
  i,r=await c(ws,i,"Runtime.evaluate",{"expression":expr,"returnByValue":True}); print(r["result"]["result"].get("value"))
asyncio.run(main())