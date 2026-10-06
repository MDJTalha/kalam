import asyncio,json,urllib.request,websockets
PAGES=['/dashboard/capability-gaps','/dashboard/capability-assessments']
async def evaluate(ws,i,expr):
 await ws.send(json.dumps({'id':i,'method':'Runtime.evaluate','params':{'expression':expr,'returnByValue':True}}))
 while True:
  x=json.loads(await asyncio.wait_for(ws.recv(),timeout=10))
  if x.get('id')==i:return x
async def main():
 t=json.load(urllib.request.urlopen('http://127.0.0.1:9222/json',timeout=5)); page=next(x for x in t if x.get('type')=='page'); print('CDP_READY',flush=True)
 async with websockets.connect(page['webSocketDebuggerUrl'],open_timeout=5,close_timeout=2,max_size=20000000) as ws:
  i=1
  for path in PAGES:
   for width,height,name in [(1440,1000,'desktop'),(390,844,'mobile')]:
    print(f'NAV {path} {name}',flush=True)
    await ws.send(json.dumps({'id':i,'method':'Emulation.setDeviceMetricsOverride','params':{'width':width,'height':height,'deviceScaleFactor':1,'mobile':width<600}})); i+=1
    await asyncio.sleep(.2)
    await ws.send(json.dumps({'id':i,'method':'Page.navigate','params':{'url':'http://127.0.0.1:3000'+path}})); i+=1
    await asyncio.sleep(7)
    expr="""(()=>{const vw=document.documentElement.clientWidth;const els=[...document.querySelectorAll('*')];return {path:location.pathname,ready:document.readyState,title:document.title,overflow:document.documentElement.scrollWidth>vw+1,viewport:innerWidth,unlabeled:[...document.querySelectorAll('input,select,textarea')].filter(x=>!(x.getAttribute('aria-label')||x.getAttribute('aria-labelledby')||x.closest('label')||(x.id&&document.querySelector('label[for="'+CSS.escape(x.id)+'"]')))).length,h1:[...document.querySelectorAll('h1')].map(x=>x.innerText.trim()).filter(Boolean),h2:[...document.querySelectorAll('h2')].map(x=>x.innerText.trim()).filter(Boolean),loading:/loading/i.test(document.body.innerText.slice(0,1000)),actions:[...document.querySelectorAll('.section-actions')].map(x=>({wrap:getComputedStyle(x).flexWrap,width:Math.round(x.getBoundingClientRect().width),display:getComputedStyle(x).display,parentDirection:getComputedStyle(x.parentElement).flexDirection})).slice(0,6),badOverflow:els.filter(x=>x.getBoundingClientRect().right>vw+1).slice(0,8).map(x=>({tag:x.tagName,text:(x.innerText||'').slice(0,50),right:Math.round(x.getBoundingClientRect().right)})),buttons:[...document.querySelectorAll('button')].map(x=>x.innerText.trim()).filter(Boolean).slice(0,20),text:document.body.innerText.slice(0,700)}})()"""
    x=await evaluate(ws,i,expr); i+=1
    print(json.dumps(x.get('result',{}).get('result',{}).get('value'),ensure_ascii=False),flush=True)
asyncio.run(main())
