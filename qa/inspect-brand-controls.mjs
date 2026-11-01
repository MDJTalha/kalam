const base="http://127.0.0.1:3000";
const t=await(await fetch("http://127.0.0.1:9333/json/new?about:blank",{method:"PUT"})).json();
const ws=new WebSocket(t.webSocketDebuggerUrl);await new Promise(r=>ws.addEventListener("open",r,{once:true}));
let id=0;const p=new Map();ws.addEventListener("message",e=>{const m=JSON.parse(e.data);if(m.id&&p.has(m.id)){const q=p.get(m.id);p.delete(m.id);m.error?q.reject(Error(m.error.message)):q.resolve(m.result)}});
const send=(method,params={})=>new Promise((resolve,reject)=>{const n=++id;p.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}))});
const ev=async expression=>(await send("Runtime.evaluate",{expression,returnByValue:true})).result.value;
await send("Page.enable");await send("Runtime.enable");
for(const route of ["/login","/contact-sales"]){
 await send("Page.navigate",{url:base+route});
 let ready=false;for(let n=0;n<100;n++){try{if(await ev("document.readyState")==="complete"){ready=true;break}}catch{}await new Promise(r=>setTimeout(r,100))}
 await new Promise(r=>setTimeout(r,500));
 const result=await ev("JSON.stringify([...document.querySelectorAll('button,input,select,textarea,a[href],[tabindex]:not([tabindex=\"-1\"])')].filter(e=>e.getClientRects().length).map(e=>({tag:e.tagName.toLowerCase(),type:e.getAttribute('type'),name:e.getAttribute('aria-label')||e.getAttribute('title')||e.getAttribute('placeholder')||e.innerText||e.value||'',role:e.getAttribute('role'),html:e.outerHTML.slice(0,450)})))");
 console.log(route,result);
}
await send("Page.close");ws.close();
