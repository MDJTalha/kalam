import fs from "node:fs/promises";
const tab=await(await fetch("http://127.0.0.1:9333/json/new?http://127.0.0.1:3000/",{method:"PUT"})).json();
const ws=new WebSocket(tab.webSocketDebuggerUrl);await new Promise(r=>ws.addEventListener("open",r,{once:true}));
let id=0;const pending=new Map();
ws.addEventListener("message",e=>{const x=JSON.parse(e.data);if(x.id&&pending.has(x.id)){pending.get(x.id)(x.result);pending.delete(x.id)}});
const send=(method,params={})=>new Promise(r=>{const n=++id;pending.set(n,r);ws.send(JSON.stringify({id:n,method,params}))});
await send("Page.enable");await send("Runtime.enable");
for(const width of [1440,390,320]){
  await send("Emulation.setDeviceMetricsOverride",{width,height:900,deviceScaleFactor:1,mobile:false});
  await send("Page.navigate",{url:"http://127.0.0.1:3000/"});
  await new Promise(r=>setTimeout(r,3500));
  const x=await send("Runtime.evaluate",{expression:"document.documentElement.style.scrollBehavior='auto';window.scrollTo(0,document.documentElement.scrollHeight);JSON.stringify({footers:document.querySelectorAll('footer').length,closing:!!document.querySelector('section[class*=closing]'),overflow:document.documentElement.scrollWidth>innerWidth,links:[...document.querySelectorAll('footer a')].map(x=>({label:x.textContent.trim(),href:x.getAttribute('href'),valid:x.hash ? !!document.querySelector(x.hash) : true}))})",returnByValue:true});
  console.log(width,x.result.value);
  await new Promise(r=>setTimeout(r,250));const shot=await send("Page.captureScreenshot",{format:"png"});
  await fs.writeFile("C:/Projects/CorpLMS/qa/footer-review-"+width+".png",Buffer.from(shot.data,"base64"));
}
ws.close();
