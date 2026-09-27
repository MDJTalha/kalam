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
  i,_=await c(ws,i,"Page.navigate",{"url":"http://127.0.0.1:3000/dashboard/reports"}); await asyncio.sleep(4)
  expr="""(()=>{const vw=window.innerWidth; const els=[...document.querySelectorAll('body *')].map(el=>{const r=el.getBoundingClientRect(),cs=getComputedStyle(el);return{tag:el.tagName,cls:typeof el.className==='string'?el.className:'',left:r.left,right:r.right,width:r.width,minWidth:cs.minWidth,maxWidth:cs.maxWidth,display:cs.display,text:(el.textContent||'').trim().slice(0,60),sidebar:!!el.closest('.sidebar')}}).filter(x=>!x.sidebar&&x.right>vw+1).sort((a,b)=>b.right-a.right).slice(0,20);return{vw,dpr:devicePixelRatio,meta:document.querySelector('meta[name=viewport]')?.getAttribute('content'),scrollWidth:document.documentElement.scrollWidth,innerWidth:vw,app:[...['.app-shell','.sidebar','.sidebar-nav','.workspace','.workspace-header','.phase6-report-stack','.two-column','.data-panel']].map(sel=>{const e=document.querySelector(sel);if(!e)return null;const r=e.getBoundingClientRect(),cs=getComputedStyle(e);return{sel,left:r.left,right:r.right,width:r.width,minWidth:cs.minWidth,grid:cs.gridTemplateColumns,overflowX:cs.overflowX}}),offenders:els}})()"""
  i,r=await c(ws,i,"Runtime.evaluate",{"expression":expr,"returnByValue":True}); print(json.dumps(r["result"]["result"].get("value"),indent=2))
asyncio.run(main())