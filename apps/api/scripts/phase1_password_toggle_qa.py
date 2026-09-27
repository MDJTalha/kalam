import asyncio,json,urllib.request,websockets
async def call(ws,i,m,p=None):
 i+=1; await ws.send(json.dumps({"id":i,"method":m,"params":p or {}}))
 while True:
  x=json.loads(await ws.recv())
  if x.get("id")==i:return i,x
async def main():
 t=json.load(urllib.request.urlopen("http://127.0.0.1:9222/json")); page=next(x for x in t if x.get("type")=="page")
 async with websockets.connect(page["webSocketDebuggerUrl"],max_size=20000000) as ws:
  i,_=await call(ws,0,"Page.navigate",{"url":"http://127.0.0.1:3000/login"}); await asyncio.sleep(2)
  expr="""(()=>{const input=document.querySelector('input[type=password]');const buttons=[...document.querySelectorAll('button')];const toggle=buttons.find(b=>/show password|hide password/i.test((b.getAttribute('aria-label')||'')+' '+(b.textContent||'')));return{url:location.href,input:!!input,type:input?.type,toggle:!!toggle,aria:toggle?.getAttribute('aria-label')}})()"""
  i,r=await call(ws,i,"Runtime.evaluate",{"expression":expr,"returnByValue":True}); print("BEFORE",json.dumps(r["result"]["result"].get("value")))
  expr2="""(()=>{const b=[...document.querySelectorAll('button')].find(b=>/show password/i.test(b.getAttribute('aria-label')||'')); if(!b)return false;b.click();return true})()"""
  i,r=await call(ws,i,"Runtime.evaluate",{"expression":expr2,"returnByValue":True}); await asyncio.sleep(.5)
  i,r=await call(ws,i,"Runtime.evaluate",{"expression":"({type:document.querySelector('input')?.type,labels:[...document.querySelectorAll('button')].map(b=>b.getAttribute('aria-label')).filter(Boolean)})","returnByValue":True}); print("AFTER",json.dumps(r["result"]["result"].get("value")))
asyncio.run(main())
