import fs from "node:fs";
import path from "node:path";
const root=process.cwd(),generated=path.join(root,"qa/generated");
const source=JSON.parse(fs.readFileSync(path.join(generated,"kalam-brand-experience-smoke.json"),"utf8"));
const expectedWidths=[320,390,768,1440];
const errors=[];
if(source.routes_scanned!==92)errors.push("Expected 92 routes, found "+source.routes_scanned);
for(const item of source.route_results){
  if(item.viewports?.length!==4)errors.push(item.route+" does not have four viewport records");
  for(const width of expectedWidths){
    const viewport=item.viewports?.find(v=>v.width===width);
    if(!viewport)errors.push(item.route+" missing "+width+"px viewport");
    else if(viewport.error)errors.push(item.route+" "+width+"px scan error: "+viewport.error);
    else if(viewport.overflow)errors.push(item.route+" horizontal overflow at "+width+"px");
    else if(viewport.scrollWidth>viewport.innerWidth+1||viewport.bodyScrollWidth>viewport.innerWidth+1)errors.push(item.route+" width mismatch at "+width+"px");
  }
}
const report={tested_at:source.tested_at,base_url:source.base_url,routes_requested:source.routes_requested,routes_scanned:source.routes_scanned,viewport_widths:expectedWidths,viewport_checks:source.route_results.reduce((sum,x)=>sum+(x.viewports||[]).length,0),horizontal_overflow_findings:errors.length,errors,route_results:source.route_results.map(x=>({route:x.route,viewports:x.viewports})),limitations:["This evidence is a verified extraction of the 368 viewport records from the full-route browser run.","Responsive widths and document overflow are checked; visual layout quality still requires human screenshot review.","Protected routes may render unauthenticated states; authenticated responsive states remain untested."]};
fs.writeFileSync(path.join(generated,"kalam-brand-responsive-smoke.json"),JSON.stringify(report,null,2)+"\n");
console.log("KALAM RESPONSIVE EVIDENCE "+(errors.length?"REVIEW":"PASS"));
console.log(JSON.stringify({routes:report.routes_scanned,viewport_checks:report.viewport_checks,overflow_findings:errors.length,output:"qa/generated/kalam-brand-responsive-smoke.json"},null,2));
if(errors.length)process.exitCode=1;
