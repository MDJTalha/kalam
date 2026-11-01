import fs from "node:fs";
import path from "node:path";

const root=process.cwd();
const inventory=JSON.parse(fs.readFileSync(path.join(root,"qa/generated/kalam-brand-surface-inventory.json"),"utf8"));
const baseUrl=process.argv[2]||"http://127.0.0.1:3000";
const cdpBase=process.env.KALAM_CDP_URL||"http://127.0.0.1:9333";
const routes=[...new Set(inventory.page_metadata.map(x=>x.route))]
  .map(route=>route.replace(/:id/g,"audit-sample").replace(/:tenant/g,"demo").replace(/:code/g,"audit-sample"));
const targetResponse=await fetch(cdpBase+"/json/new?about:blank",{method:"PUT"});
if(!targetResponse.ok)throw new Error("Chrome CDP target creation failed: "+targetResponse.status);
const target=await targetResponse.json();
const ws=new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.addEventListener("open",resolve,{once:true});ws.addEventListener("error",reject,{once:true})});
let id=0;
const pending=new Map();
ws.addEventListener("message",event=>{
  const m=JSON.parse(event.data);
  if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(new Error(m.error.message)):p.resolve(m.result)}
});
function send(method,params={}){return new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}))})}
async function evaluate(expression){
  const r=await send("Runtime.evaluate",{expression,returnByValue:true,awaitPromise:true});
  if(r.exceptionDetails)throw new Error(r.exceptionDetails.text||"Runtime evaluation failed");
  return r.result?.value;
}
async function waitLoad(){
  const started=Date.now();
  while(Date.now()-started<15000){try{if(await evaluate("document.readyState")==="complete")return}catch{}await new Promise(resolve=>setTimeout(resolve,100))}
  throw new Error("Timed out waiting for page load");
}
const results=[],errors=[];
try{
  await send("Page.enable");await send("Runtime.enable");
  for(const route of routes){
    const item={route};
    try{
      await send("Page.navigate",{url:new URL(route,baseUrl).href});
      await waitLoad();
      await new Promise(resolve=>setTimeout(resolve,150));
      await send("Page.bringToFront");
      const start=await evaluate("JSON.stringify({url:location.pathname,title:document.title,focusable:[...document.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex=\"-1\"])')].filter(e=>e.getClientRects().length).length})");
      item.page=JSON.parse(start);
      const focused=[];
      for(let n=0;n<Math.min(12,item.page.focusable);n++){
        await send("Input.dispatchKeyEvent",{type:"rawKeyDown",key:"Tab",code:"Tab",windowsVirtualKeyCode:9,nativeVirtualKeyCode:9});
        await send("Input.dispatchKeyEvent",{type:"keyUp",key:"Tab",code:"Tab",windowsVirtualKeyCode:9,nativeVirtualKeyCode:9});
        const result=await evaluate("JSON.stringify((()=>{const e=document.activeElement;if(!e||e===document.body)return {tag:'body',name:'',visible:false,focusVisible:false,outline:'none',boxShadow:'none'};const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {tag:e.tagName.toLowerCase(),role:e.getAttribute('role'),name:(e.getAttribute('aria-label')||(e.getAttribute('aria-labelledby')||'').split(/\\s+/).map(id=>document.getElementById(id)?.innerText||'').join(' ')||(e.labels?[...e.labels].map(l=>l.innerText).join(' '):e.closest('label')?.innerText)||e.getAttribute('title')||e.getAttribute('placeholder')||e.innerText||e.value||'').trim().slice(0,100),href:e.getAttribute('href'),visible:r.width>0&&r.height>0,focusVisible:e.matches(':focus-visible'),outline:s.outlineStyle+' '+s.outlineWidth+' '+s.outlineColor,boxShadow:s.boxShadow}})())");
        focused.push(JSON.parse(result));
      }
      const noFocus=focused.filter(x=>x.tag==="body").length;
      const invisible=focused.filter(x=>x.tag!=="body"&&!x.visible).length;
      const unlabeled=focused.filter(x=>["button","input","select","textarea"].includes(x.tag)&&!x.name).length;
      const noVisibleFocus=focused.filter(x=>x.tag!=="body"&&(!x.focusVisible||(x.outline.startsWith("none")&&x.boxShadow==="none"))).length;
      item.keyboard={tabSteps:focused,noFocus,invisible,unlabeled,noVisibleFocus};
      if(item.page.focusable>0&&noFocus===focused.length)errors.push({route,kind:"NO_FOCUS_MOVEMENT"});
      if(invisible)errors.push({route,kind:"INVISIBLE_FOCUSED_ELEMENT",count:invisible});
      if(unlabeled)errors.push({route,kind:"UNLABELED_FOCUSED_CONTROL",count:unlabeled});
      console.log(route+" focusable="+item.page.focusable+" tabs="+focused.filter(x=>x.tag!=="body").length+"/12 noVisibleFocus="+noVisibleFocus+" unlabeled="+unlabeled);
    }catch(error){
      item.error=String(error);errors.push({route,kind:"KEYBOARD_SCAN_ERROR",error:String(error)});
      console.log(route+" KEYBOARD_SCAN_ERROR "+String(error));
    }
    results.push(item);
  }
}finally{
  try{await send("Page.close")}catch{}
  ws.close();
}
const report={tested_at:new Date().toISOString(),base_url:baseUrl,routes_requested:routes.length,routes_scanned:results.length,tab_steps_per_route:12,errors,route_results:results,limitations:["Protected routes may render unauthenticated states; authenticated role matrix remains separate.","First 12 tab transitions are sampled; dialogs, menus and every component state still require focused scenario tests.","CDP keyboard simulation is not a substitute for physical keyboard and screen-reader testing."]};
fs.writeFileSync(path.join(root,"qa/generated/kalam-brand-keyboard-smoke.json"),JSON.stringify(report,null,2)+"\n");
console.log("KALAM BRAND KEYBOARD SMOKE "+(errors.length?"REVIEW":"PASS"));
console.log(JSON.stringify({routes_scanned:results.length,errors:errors.length,scan_errors:errors.filter(x=>x.kind==="KEYBOARD_SCAN_ERROR").length,output:"qa/generated/kalam-brand-keyboard-smoke.json"},null,2));
if(errors.some(x=>x.kind==="KEYBOARD_SCAN_ERROR"))process.exitCode=1;
