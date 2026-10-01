import fs from "node:fs/promises";
const base="http://127.0.0.1:3000";
const routes=["/","/pricing","/contact-sales","/guided-evaluation","/implementation","/integrations","/trust","/clients"];
const widths=[390,768,1440];
const tab=await (await fetch("http://127.0.0.1:9337/json/new?"+encodeURIComponent(base+"/"),{method:"PUT"})).json();
const ws=new WebSocket(tab.webSocketDebuggerUrl);
await new Promise(r=>ws.addEventListener("open",r,{once:true}));
let id=0;const pending=new Map();
ws.addEventListener("message",e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(new Error(m.error.message)):p.resolve(m.result)}});
const send=(method,params={})=>new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}))});
await send("Page.enable");await send("Runtime.enable");
const axe=await fs.readFile("C:/Projects/CorpLMS/node_modules/axe-core/axe.min.js","utf8");
await send("Page.addScriptToEvaluateOnNewDocument",{source:axe});
let failed=false;const report=[];
for(const route of routes){for(const width of widths){
 await send("Emulation.setDeviceMetricsOverride",{width,height:900,deviceScaleFactor:1,mobile:width<900});
 await send("Page.navigate",{url:base+route});
 await new Promise(r=>setTimeout(r,850));
 const state=JSON.parse((await send("Runtime.evaluate",{expression:`JSON.stringify({h1:document.querySelectorAll('h1').length,overflow:document.documentElement.scrollWidth>innerWidth,broken:[...document.querySelectorAll('a[href^="#"]')].filter(a=>a.hash&&!document.getElementById(a.hash.slice(1))).map(a=>a.getAttribute('href')),header:!!document.querySelector('header')})`,returnByValue:true})).result.value);
 const violations=JSON.parse((await send("Runtime.evaluate",{expression:"axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}}).then(x=>JSON.stringify(x.violations.map(v=>({id:v.id,impact:v.impact,targets:v.nodes.map(n=>n.target)}))))",awaitPromise:true,returnByValue:true})).result.value);
 const bad=state.h1!==1||state.overflow||state.broken.length||violations.length;
 failed||=bad;report.push({route,width,...state,violations});
 console.log((bad?"FAIL ":"PASS ")+route+" "+width+" "+JSON.stringify({h1:state.h1,overflow:state.overflow,broken:state.broken,violations:violations.map(v=>v.id)}));
}}
await fs.writeFile("C:/Projects/CorpLMS/qa/PUBLIC_RELEASE_AUDIT_2026-09-28.json",JSON.stringify(report,null,2));
ws.close();if(failed)process.exitCode=2;