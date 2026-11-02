import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const inventory = JSON.parse(fs.readFileSync(path.join(root, "qa/generated/kalam-brand-surface-inventory.json"), "utf8"));
const baseUrl = process.argv[2] || "http://127.0.0.1:3000";
const cdpBase = process.env.KALAM_CDP_URL || "http://127.0.0.1:9333";
const routes = [...new Set(inventory.page_metadata.map(item => item.route))]
  .map(route => route.replace(/:id/g, "audit-sample").replace(/:tenant/g, "demo").replace(/:code/g, "audit-sample"));
const viewports = [320, 390, 768, 1440];

const targetResponse = await fetch(cdpBase + "/json/new?about:blank", {method:"PUT"});
if (!targetResponse.ok) throw new Error("Chrome CDP target creation failed: " + targetResponse.status);
const target = await targetResponse.json();
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.addEventListener("open",resolve,{once:true});ws.addEventListener("error",reject,{once:true})});
let id=0;
const pending=new Map();
ws.addEventListener("message",event=>{
  const message=JSON.parse(event.data);
  if(message.id&&pending.has(message.id)){
    const p=pending.get(message.id);pending.delete(message.id);
    message.error?p.reject(new Error(message.error.message)):p.resolve(message.result);
  }
});
function send(method,params={}) {
  return new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}))});
}
async function evaluate(expression) {
  const result=await send("Runtime.evaluate",{expression,returnByValue:true,awaitPromise:true});
  if(result.exceptionDetails)throw new Error(result.exceptionDetails.text||"Browser evaluation failed");
  return result.result?.value;
}
async function waitLoad(){
  const started=Date.now();
  while(Date.now()-started<15000){
    try{if(await evaluate("document.readyState")==="complete")return}catch{}
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  throw new Error("Page load timeout");
}
async function navigate(route,width){
  await send("Emulation.setDeviceMetricsOverride",{width,height:900,deviceScaleFactor:1,mobile:false});
  await send("Page.navigate",{url:new URL(route,baseUrl).href});
  await waitLoad();
  await new Promise(resolve=>setTimeout(resolve,180));
}
const results=[];
const failures=[];
try{
  await send("Page.enable");await send("Runtime.enable");
  for(const route of routes){
    const routeResult={route,viewports:[],keyboard:null};
    for(const width of viewports){
      try{
        await navigate(route,width);
        const state=await evaluate("JSON.stringify({url:location.pathname,title:document.title,innerWidth,scrollWidth:document.documentElement.scrollWidth,bodyScrollWidth:document.body?.scrollWidth||0,bodyHeight:document.body?.scrollHeight||0,focusable:[...document.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex=\"-1\"])')].filter(e=>e.getClientRects().length).length,logo:!!document.querySelector('.kalam-logo'),reducedMotion:matchMedia('(prefers-reduced-motion: reduce)').matches})");
        const parsed=JSON.parse(state);
        const overflow=parsed.scrollWidth>parsed.innerWidth+1||parsed.bodyScrollWidth>parsed.innerWidth+1;
        routeResult.viewports.push({width,overflow,...parsed});
        if(overflow)failures.push({route,width,kind:"HORIZONTAL_OVERFLOW",scrollWidth:parsed.scrollWidth,bodyScrollWidth:parsed.bodyScrollWidth});
      }catch(error){
        routeResult.viewports.push({width,error:String(error)});
        failures.push({route,width,kind:"VIEWPORT_SCAN_ERROR",error:String(error)});
      }
    }
    try{
      await navigate(route,1440);
      const focusableCount=await evaluate("document.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex=\"-1\"])').length");
      const focused=[];
      for(let n=0;n<12;n++){
        await send("Input.dispatchKeyEvent",{type:"keyDown",key:"Tab",code:"Tab",windowsVirtualKeyCode:9,nativeVirtualKeyCode:9});
        await send("Input.dispatchKeyEvent",{type:"keyUp",key:"Tab",code:"Tab",windowsVirtualKeyCode:9,nativeVirtualKeyCode:9});
        const item=await evaluate("(()=>{const e=document.activeElement;if(!e||e===document.body)return {tag:'body',name:'',visible:false,focusVisible:false};const r=e.getBoundingClientRect();const name=(e.getAttribute('aria-label')||e.getAttribute('title')||e.getAttribute('placeholder')||e.innerText||e.value||'').trim().slice(0,100);const s=getComputedStyle(e);return {tag:e.tagName.toLowerCase(),role:e.getAttribute('role'),name,href:e.getAttribute('href'),visible:r.width>0&&r.height>0,focusVisible:e.matches(':focus-visible'),outline:s.outlineStyle+' '+s.outlineWidth+' '+s.outlineColor,boxShadow:s.boxShadow}})()");
        focused.push(JSON.parse(item));
      }
      const noFocus=focused.filter(x=>x.tag==="body").length;
      const invisible=focused.filter(x=>x.tag!=="body"&&!x.visible).length;
      const unlabeled=focused.filter(x=>x.tag==="button"||x.tag==="input"||x.tag==="select"||x.tag==="textarea").filter(x=>!x.name).length;
      routeResult.keyboard={focusableCount,tabSteps:focused,noFocus,invisible,unlabeled};
      if(focusableCount>0&&noFocus===focused.length)failures.push({route,kind:"KEYBOARD_NO_FOCUS_MOVEMENT"});
      if(invisible)failures.push({route,kind:"KEYBOARD_INVISIBLE_FOCUS",count:invisible});
      if(unlabeled)failures.push({route,kind:"UNLABELED_FOCUSED_CONTROLS",count:unlabeled});
    }catch(error){
      routeResult.keyboard={error:String(error)};
      failures.push({route,kind:"KEYBOARD_SCAN_ERROR",error:String(error)});
    }
    results.push(routeResult);
    console.log(route+" viewports="+routeResult.viewports.filter(x=>!x.error).length+"/4 keyboard="+(routeResult.keyboard?.error?"ERROR":routeResult.keyboard?.focusableCount??0)+" failures="+failures.filter(x=>x.route===route).length);
  }
}finally{
  try{await send("Page.close")}catch{}
  ws.close();
}
const report={tested_at:new Date().toISOString(),base_url:baseUrl,routes_requested:routes.length,routes_scanned:results.length,viewports_per_route:viewports,keyboard_tab_steps_per_route:12,viewport_checks:results.reduce((sum,x)=>sum+x.viewports.length,0),horizontal_overflow_findings:failures.filter(x=>x.kind==="HORIZONTAL_OVERFLOW").length,keyboard_findings:failures.filter(x=>x.kind.startsWith("KEYBOARD")||x.kind.startsWith("UNLABELED")).length,scan_errors:failures.filter(x=>x.kind.endsWith("ERROR")).length,failures,route_results:results,limitations:["Protected routes may render unauthenticated states; this is not an authenticated role matrix.","Tab sampling tests the first 12 focus transitions per route, not every control or modal state.","This is a desktop Chrome keyboard simulation; it does not replace real keyboard, screen-reader or manual usability testing."]};
const out=path.join(root,"qa/generated/kalam-brand-experience-smoke.json");
fs.writeFileSync(out,JSON.stringify(report,null,2)+"\n");
console.log("KALAM BRAND EXPERIENCE SMOKE");
console.log(JSON.stringify({routes_scanned:report.routes_scanned,viewport_checks:report.viewport_checks,horizontal_overflow_findings:report.horizontal_overflow_findings,keyboard_findings:report.keyboard_findings,scan_errors:report.scan_errors,output:path.relative(root,out)},null,2));
if(report.scan_errors>0)process.exitCode=1;
