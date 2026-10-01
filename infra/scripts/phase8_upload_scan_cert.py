"""Exercise the authenticated upload path and ClamAV using an existing browser session."""
import asyncio
import json
import os
import urllib.request
from pathlib import Path

import websockets

DEBUG_PORT = os.getenv("BROWSER_DEBUG_PORT", "9222")
WEB_BASE_URL = os.getenv("CERT_WEB_BASE_URL", "http://127.0.0.1:3100").rstrip("/")
OUTPUT = Path(os.getenv("UPLOAD_CERT_OUTPUT", "qa/phase8-upload-scan-cert.json"))


async def call(ws, seq, method, params=None):
    seq += 1
    await ws.send(json.dumps({"id": seq, "method": method, "params": params or {}}))
    while True:
        response = json.loads(await ws.recv())
        if response.get("id") == seq:
            if "error" in response:
                raise RuntimeError(f"CDP {method}: {response['error']}")
            return seq, response.get("result", {})


async def main():
    targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{DEBUG_PORT}/json", timeout=8))
    page = next(item for item in targets if item.get("type") == "page")
    async with websockets.connect(page["webSocketDebuggerUrl"], max_size=20_000_000) as ws:
        seq, _ = await call(ws, 0, "Page.enable")
        seq, _ = await call(ws, seq, "Runtime.enable")
        seq, _ = await call(ws, seq, "Page.navigate", {"url": WEB_BASE_URL + "/dashboard/files"})
        for _ in range(30):
            await asyncio.sleep(0.25)
            seq, state = await call(ws, seq, "Runtime.evaluate", {"expression": "location.pathname", "returnByValue": True})
            if state.get("result", {}).get("value") == "/dashboard/files":
                break
        expression = """(async()=>{const upload=async(name,body)=>{const form=new FormData();
form.append('upload',new File([body],name,{type:'text/plain'}));const r=await fetch('/api/lms/files',{method:'POST',body:form});
return {status:r.status,text:await r.text()};};const clean=await upload('phase8rc-clean.txt','Kognivon Phase 8 clean upload certification file.');
const sig='X5O!P%@AP[4'+String.fromCharCode(92)+'PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*';
const infected=await upload('phase8rc-eicar-standard.txt',sig);const list=await fetch('/api/lms/files');
return {clean,infected,list_status:list.status,files:await list.json()};})()"""
        seq, result = await call(ws, seq, "Runtime.evaluate", {
            "expression": expression, "awaitPromise": True, "returnByValue": True
        })
        if "exceptionDetails" in result:
            raise RuntimeError(f"Upload certification browser exception: {result['exceptionDetails']}")
        value = result.get("result", {}).get("value")
        if not isinstance(value, dict) or "clean" not in value or "infected" not in value:
            raise RuntimeError(f"Upload certification returned unexpected data: {result}")
    files = value.get("files") if isinstance(value.get("files"), list) else []
    clean_ok = value["clean"]["status"] == 201 and any(x.get("name") == "phase8rc-clean.txt" for x in files)
    infected_ok = value["infected"]["status"] == 422 and not any(x.get("name") == "phase8rc-eicar-standard.txt" for x in files)
    report = {**value, "clean_upload_pass": clean_ok, "malware_rejection_pass": infected_ok}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"clean_upload_pass": clean_ok, "malware_rejection_pass": infected_ok, "report": str(OUTPUT)}))
    if not clean_ok or not infected_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
