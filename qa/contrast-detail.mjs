import fs from "node:fs/promises";
const axe=await fs.readFile("C:/Projects/CorpLMS/node_modules/axe-core/axe.min.js","utf8");
for (const [route,width] of [["/",390],["/pricing",1440]]) {
 const tab=await (await fetch("http://127.0.0.1:9335/json/new?"+encodeURIComponent("http://127.0.0.1:3000"+route),{method:"PUT"})).json();
 const ws=new WebSocket(tab.webSocketDebuggerUrl); await new Promise(r=>ws.addEventListener("open",r,{once:true}));
 let id=0; const pending=new Map(); ws.addEventListener("message",e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(new Error(m.error.message)):p.resolve(m.result)}});
 const send=(method,params={})=>new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}))});
 await send("Runtime.enable"); await send("Page.enable"); await send("Emulation.setDeviceMetricsOverride",{width,height:900,deviceScaleFactor:1,mobile:width<900});
 await send("Runtime.evaluate",{expression:axe});
 await new Promise(r=>setTimeout(r,900));
 const expr="axe.run(document,{runOnly:{type:'rule',values:['color-contrast','aria-hidden-focus']}}).then(x=>JSON.stringify(x.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,html:n.html,summary:n.failureSummary}))}))))";
 const out=await send("Runtime.evaluate",{expression:expr,awaitPromise:true,returnByValue:true}); console.log(route,width,out.result.value); ws.close();
}