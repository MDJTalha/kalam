import asyncio,json,requests,websockets
PORT=9333
tabs=requests.get(f"http://127.0.0.1:{PORT}/json",timeout=5).json()
print([(t.get("url"),t.get("type")) for t in tabs],flush=True)
page=[t for t in tabs if t.get("type")=="page"][0]
async def main():
 async with websockets.connect(page["webSocketDebuggerUrl"],max_size=2**22) as ws:
  await ws.send(json.dumps({"id":99,"method":"Runtime.evaluate","params":{"expression":"({iw:innerWidth,cw:document.documentElement.clientWidth,sw:document.documentElement.scrollWidth,bs:document.body.scrollWidth,logo:document.querySelector('header img')?.getBoundingClientRect().toJSON()})","returnByValue":True}}))
  while True:
   m=json.loads(await ws.recv())
   if m.get("id")==99:
    print(m["result"]["result"].get("value"),flush=True);break
asyncio.run(main())
