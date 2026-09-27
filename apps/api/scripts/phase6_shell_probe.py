import asyncio,json,urllib.request,websockets
async def c(ws,i,m,p=None):
 i+=1; await ws.send(json.dumps({"id":i,"method":m,"params":p or {}}))
 while True:
  x=json.loads(await ws.recv())
  if x.get("id")==i:return i,x
async def main():
 t=json.load(urllib.request.urlopen("http://127.0.0.1:9222/json")); page=next(x for x in t if x.get("type")=="page")
 async with websockets.connect(page["webSocketDebuggerUrl"]) as ws:
  i,_=await c(ws,0,"Emulation.setDeviceMetricsOverride",{"width":390,"height":844,"deviceScaleFactor":1,"mobile":True})
  i,_=await c(ws,i,"Page.navigate",{"url":"http://127.0.0.1:3000/dashboard/reports"}); await asyncio.sleep(1)
  expr="""(()=>{let s=document.querySelector('.sidebar'),n=document.querySelector('.sidebar-nav'),w=document.querySelector('.workspace'),a=document.querySelector('.app-shell');return [a,s,n,w].map(x=>{let r=x.getBoundingClientRect(),cs=getComputedStyle(x);return {cls:x.className,width:r.width,right:r.right,minWidth:cs.minWidth,overflowX:cs.overflowX,grid:cs.gridTemplateColumns}})})()"""
  i,r=await c(ws,i,"Runtime.evaluate",{"expression":expr,"returnByValue":True}); print(r["result"]["result"]["value"])
asyncio.run(main())