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
  expr="""(async()=>{let a=await fetch('/api/lms/integrations');let b=await fetch('/api/v1/integrations');return {proxy:{status:a.status,text:(await a.text()).slice(0,1000)},direct:{status:b.status,text:(await b.text()).slice(0,1000)}}})()"""
  i,r=await c(ws,0,"Runtime.evaluate",{"expression":expr,"returnByValue":True,"awaitPromise":True}); print(r["result"]["result"].get("value"))
asyncio.run(main())