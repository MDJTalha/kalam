import fs from "node:fs/promises";
const axe=await fs.readFile("C:/Projects/CorpLMS/node_modules/axe-core/axe.min.js","utf8");
for (const route of ["/clients","/trust","/guided-evaluation","/"]) {
 const tab=await (await fetch("http://127.0.0.1:9335/json/new?"+encodeURIComponent("http://127.0.0.1:3000"+route),{method:"PUT"})).json();
 const ws=new WebSocket(tab.webSocketDebuggerUrl); await new Promise(r=>ws.addEventListener("open",r,{once:true}));
 let id=0;const p=new Map();ws.addEventListener("message",e=>{const m=JSON.parse(e.data);if(m.id&&p.has(m.id)){const q=p.get(m.id);p.delete(m.id);m.error?q.reject(new Error(m.error.message)):q.resolve(m.result)}});
 const send=(method,params={})=>new Promise((resolve,reject)=>{const n=++id;p.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}))});
 await send("Runtime.enable"); await send("Page.enable"); await new Promise(r=>setTimeout(r,700)); await send("Runtime.evaluate",{expression:axe});
 const expr="axe.run(document,{runOnly:{type:'rule',values:['color-contrast']}}).then(x=>JSON.stringify(x.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,html:n.html,summary:n.failureSummary}))}))))";
 const out=await send("Runtime.evaluate",{expression:expr,awaitPromise:true,returnByValue:true});
 console.log(route,out.result?.value||JSON.stringify(out)); ws.close();
}