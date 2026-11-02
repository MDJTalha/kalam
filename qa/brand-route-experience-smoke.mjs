import fs from "node:fs";
import path from "node:path";

const root=process.cwd();
const inventory=JSON.parse(fs.readFileSync(path.join(root,"qa/generated/kalam-brand-surface-inventory.json"),"utf8"));
const baseUrl=process.argv[2]||"http://127.0.0.1:3000";
let buildCommit=null;
try{const response=await fetch(new URL("/",baseUrl));buildCommit=response.headers.get("x-kalam-build-commit")}catch{}
const cdpBase=process.env.KALAM_CDP_URL||"http://127.0.0.1:9333";
const routes=[...new Set(inventory.page_metadata.map(x=>x.route))]
  .map(route=>route.replace(/:id/g,"audit-sample").replace(/:tenant/g,"demo").replace(/:code/g,"audit-sample"));
const widths=[320,390,768,1440];

const targetResponse=await fetch(cdpBase+"/json/new?about:blank",{method:"PUT"});
if(!targetResponse.ok)throw new Error("Chrome CDP target creation failed: "+targetResponse.status);
const target=await targetResponse.json();
const ws=new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.addEventListener("open",resolve,{once:true});ws.addEventListener("error",reject,{once:true})});
let id=0;
let loadEvents=0;
const pending=new Map();
ws.addEventListener("message",event=>{
  const m=JSON.parse(event.data);
  if(m.method==="Page.loadEventFired")loadEvents++;
  if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(new Error(m.error.message)):p.resolve(m.result)}
});
function send(method,params={}){return new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}))})}
async function evaluate(expression){
  const r=await send("Runtime.evaluate",{expression,returnByValue:true,awaitPromise:true});
  if(r.exceptionDetails)throw new Error(r.exceptionDetails.text||"Browser evaluation failed");
  return r.result?.value;
}
async function waitForNavigation(previousLoadEvents){
  const started=Date.now();
  while(Date.now()-started<20000){
    try{
      const state=JSON.parse(await evaluate("JSON.stringify({ready:document.readyState,url:location.href})"));
      if(loadEvents>previousLoadEvents&&state.ready==="complete")return state.url;
    }catch{}
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  throw new Error("Navigation load event did not complete");
}
const results=[],errors=[];
try{
  await send("Page.enable");await send("Runtime.enable");
  for(const route of routes){
    const item={route,viewports:[],keyboard:null};
    try{
      const previousLoadEvents=loadEvents;
      const navigation=await send("Page.navigate",{url:new URL(route,baseUrl).href});
      if(navigation.errorText)throw new Error(navigation.errorText);
      item.actual_url=await waitForNavigation(previousLoadEvents);
      await new Promise(resolve=>setTimeout(resolve,350));
      for(const width of widths){
        await send("Emulation.setDeviceMetricsOverride",{width,height:900,deviceScaleFactor:1,mobile:false});
        await new Promise(resolve=>setTimeout(resolve,120));
        const state=JSON.parse(await evaluate("JSON.stringify({url:location.pathname,title:document.title,innerWidth,scrollWidth:document.documentElement.scrollWidth,bodyScrollWidth:document.body?.scrollWidth||0,bodyHeight:document.body?.scrollHeight||0,focusable:[...document.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex=\\\"-1\\\"])')].filter(e=>e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden').length,logo:!!document.querySelector('.kalam-logo')})"));
        const overflow=state.scrollWidth>state.innerWidth+1||state.bodyScrollWidth>state.innerWidth+1;
        item.viewports.push({width,overflow,...state});
        if(overflow)errors.push({route,kind:"HORIZONTAL_OVERFLOW",width,scrollWidth:state.scrollWidth,bodyScrollWidth:state.bodyScrollWidth});
      }
      await send("Emulation.setDeviceMetricsOverride",{width:1440,height:900,deviceScaleFactor:1,mobile:false});
      await send("Page.bringToFront");
      const focusableCount=await evaluate("document.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex=\\\"-1\\\"])').length");
      const tabSteps=[];
      for(let n=0;n<Math.min(12,focusableCount+1);n++){
        await send("Input.dispatchKeyEvent",{type:"rawKeyDown",key:"Tab",code:"Tab",windowsVirtualKeyCode:9,nativeVirtualKeyCode:9});
        await send("Input.dispatchKeyEvent",{type:"keyUp",key:"Tab",code:"Tab",windowsVirtualKeyCode:9,nativeVirtualKeyCode:9});
        const state=JSON.parse(await evaluate("JSON.stringify((()=>{const e=document.activeElement;if(!e||e===document.body)return {tag:'body',name:'',visible:false,focusVisible:false,outlineStyle:'none',outlineWidth:0,boxShadow:'none'};const r=e.getBoundingClientRect(),s=getComputedStyle(e);const labelledBy=(e.getAttribute('aria-labelledby')||'').split(/\\s+/).map(id=>document.getElementById(id)?.innerText||'').join(' ');const label=e.labels?[...e.labels].map(l=>l.innerText).join(' '):(e.closest('label')?.innerText||'');return {tag:e.tagName.toLowerCase(),role:e.getAttribute('role'),name:(e.getAttribute('aria-label')||labelledBy||label||e.getAttribute('title')||e.getAttribute('placeholder')||e.innerText||e.value||'').trim().slice(0,100),href:e.getAttribute('href'),visible:r.width>0&&r.height>0,focusVisible:e.matches(':focus-visible'),outlineStyle:s.outlineStyle,outlineWidth:parseFloat(s.outlineWidth)||0,outlineColor:s.outlineColor,boxShadow:s.boxShadow}})())"));
        tabSteps.push(state);
      }
      const firstStep=tabSteps[0];
      const noFocus=tabSteps.filter(x=>x.tag==="body").length;
      const invisible=tabSteps.filter(x=>x.tag!=="body"&&!x.visible).length;
      const unlabeled=tabSteps.filter(x=>["button","input","select","textarea"].includes(x.tag)&&!x.name).length;
      const noVisibleFocus=tabSteps.filter(x=>{
        if(x.tag==="body")return false;
        const shadowVisible=x.boxShadow!=="none"&&!/rgba\\([^)]*,\\s*0(?:\\.0+)?\\)/.test(x.boxShadow);
        return !x.focusVisible||!(x.outlineStyle!=="none"&&x.outlineWidth>0||shadowVisible);
      }).length;
      item.keyboard={focusableCount,tabSteps,noFocus,invisible,unlabeled,noVisibleFocus,firstStep};
      if(focusableCount>0&&(!firstStep||firstStep.tag==="body"))errors.push({route,kind:"NO_FOCUS_MOVEMENT"});
      if(invisible)errors.push({route,kind:"INVISIBLE_FOCUSED_ELEMENT",count:invisible});
      if(unlabeled)errors.push({route,kind:"UNLABELED_FOCUSED_CONTROL",count:unlabeled});
      if(noVisibleFocus)errors.push({route,kind:"NO_VISIBLE_FOCUS_INDICATOR",count:noVisibleFocus});
    }catch(error){
      item.error=String(error);errors.push({route,kind:"EXPERIENCE_SCAN_ERROR",error:String(error)});
    }
    results.push(item);
    console.log(route+" actual="+(item.actual_url||"ERROR")+" viewport="+item.viewports.filter(x=>!x.error).length+"/4 keyboard="+(item.keyboard?.tabSteps?.length??0)+" issues="+errors.filter(x=>x.route===route).length);
  }
}finally{
  try{await send("Page.close")}catch{}
  ws.close();
}
const report={tested_at:new Date().toISOString(),base_url:baseUrl,inventory_commit:inventory.commit,inventory_working_tree:inventory.working_tree,build_commit:buildCommit,build_commit_matches_inventory:buildCommit===inventory.commit,routes_requested:routes.length,routes_scanned:results.length,viewport_widths:widths,viewport_checks:results.reduce((n,x)=>n+x.viewports.length,0),horizontal_overflow_findings:errors.filter(x=>x.kind==="HORIZONTAL_OVERFLOW").length,keyboard_findings:errors.filter(x=>x.kind!=="HORIZONTAL_OVERFLOW"&&x.kind!=="EXPERIENCE_SCAN_ERROR").length,scan_errors:errors.filter(x=>x.kind==="EXPERIENCE_SCAN_ERROR").length,errors,route_results:results,limitations:["Protected routes may redirect to /login without an authenticated session; this does not test authenticated dashboard screens.","Keyboard testing samples up to the first 12 tab stops per rendered route.","This CDP simulation does not replace physical keyboard, screen-reader or human visual review."]};
fs.writeFileSync(path.join(root,"qa/generated/kalam-brand-route-experience-smoke.json"),JSON.stringify(report,null,2)+"\n");
console.log("KALAM ROUTE EXPERIENCE SMOKE "+(errors.length?"REVIEW":"PASS"));
console.log(JSON.stringify({routes_scanned:report.routes_scanned,viewport_checks:report.viewport_checks,horizontal_overflow_findings:report.horizontal_overflow_findings,keyboard_findings:report.keyboard_findings,scan_errors:report.scan_errors,output:"qa/generated/kalam-brand-route-experience-smoke.json"},null,2));
if(report.scan_errors>0||!report.build_commit_matches_inventory)process.exitCode=1;
