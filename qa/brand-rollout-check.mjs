import fs from "node:fs/promises";
const tab = await (await fetch("http://127.0.0.1:9333/json/new?http://127.0.0.1:3000/", {method:"PUT"})).json();
const ws = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise(resolve => ws.addEventListener("open", resolve, {once:true}));
let id=0; const pending=new Map();
ws.addEventListener("message", event => {
  const m=JSON.parse(event.data);
  if(m.id && pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(m.error.message)):p.resolve(m.result)}
});
function send(method,params={}){return new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}))})}
await send("Page.enable"); await send("Runtime.enable");
for(const [route,width] of [["/",1440],["/",390]]){
  await send("Emulation.setDeviceMetricsOverride",{width,height:900,deviceScaleFactor:1,mobile:false});
  await send("Page.navigate",{url:"http://127.0.0.1:3000"+route});
  await new Promise(resolve=>setTimeout(resolve,1500));
  const state=await send("Runtime.evaluate",{expression:"JSON.stringify({title:document.title,overflow:document.documentElement.scrollWidth>innerWidth,logos:[...document.querySelectorAll('.kognivon-logo-asset img')].map(x=>({src:x.getAttribute('src'),loaded:x.complete&&x.naturalWidth>0,width:Math.round(x.getBoundingClientRect().width)})),icon:document.querySelector('link[rel=icon]')?.href})",returnByValue:true});
  console.log(route,width,state.result.value);
  const shot=await send("Page.captureScreenshot",{format:"png",captureBeyondViewport:false});
  await fs.writeFile("C:/Projects/CorpLMS/qa/brand-"+(route==="/"?"home":route.slice(1))+"-"+width+".png",Buffer.from(shot.data,"base64"));
}
ws.close();
