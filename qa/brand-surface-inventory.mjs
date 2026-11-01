import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const root=process.cwd(), web=path.join(root,"apps","web"), src=path.join(web,"src");
const app=path.join(src,"app"), components=path.join(src,"components"), pub=path.join(web,"public");
const docs=path.join(root,"docs"), qa=path.join(root,"qa"), out=path.join(qa,"generated");
const exists=p=>fs.existsSync(p), rel=p=>path.relative(root,p).split(path.sep).join("/");
const walk=dir=>!exists(dir)?[]:fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>{const p=path.join(dir,e.name);return e.isDirectory()?walk(p):[p]});
const read=p=>{try{return fs.readFileSync(p,"utf8")}catch{return ""}};
const files=[...new Set([...walk(src),...walk(pub),...walk(docs),...walk(path.join(root,"emails")),...walk(path.join(root,"notifications")),...walk(path.join(web,"emails")),...walk(path.join(web,"notifications"))].filter(p=>/\.(?:tsx?|jsx?|css|scss|svg|json|md|mdx|html|txt|ya?ml|webmanifest)$/i.test(p)))].sort();
const routes=files.filter(p=>p.startsWith(app+path.sep)&&/(?:^|[\\/])page\.(?:tsx?|jsx?)$/i.test(p));
const states=files.filter(p=>p.startsWith(app+path.sep)&&/(?:^|[\\/])(?:loading|error|not-found|global-error)\.(?:tsx?|jsx?)$/i.test(p));
const comps=files.filter(p=>p.startsWith(components+path.sep)), css=files.filter(p=>/\.(?:css|scss)$/i.test(p));
const assets=files.filter(p=>p.startsWith(pub+path.sep)), metadata=files.filter(p=>/(?:metadata|manifest|sitemap|robots|opengraph|twitter|schema|structured)/i.test(path.basename(p)));
const comms=files.filter(p=>/(?:email|notification|template|message|marketing|transactional|communication)/i.test(p));
const customerDocs=files.filter(p=>p.startsWith(docs+path.sep)&&/\.(?:md|mdx|html|txt)$/i.test(p));
const routePath=p=>{let s=path.relative(app,path.dirname(p)).split(path.sep).join("/");s=s==="."?"/":"/"+s;return s.replace(/\([^/]+\)\/?/g,"").replace(/\/+/g,"/").replace(/\[([^\]]+)\]/g,":$1")};
const stateMap=new Map();
for(const p of states){const d=path.dirname(p),v=path.basename(p).replace(/\.(?:tsx?|jsx?)$/i,"");stateMap.set(d,[...(stateMap.get(d)||[]),v])}

const inventory=[];
function add(p,type,extra={}){
 const f=rel(p), prior=inventory.find(x=>x.route_or_file===f);
 if(prior){prior.type=[...new Set(prior.type.split("|").concat(type))].sort().join("|");if(extra.route)prior.route=extra.route;if(extra.states)prior.states=extra.states;return}
 const audience=f.includes("/dashboard/")?"authenticated-user":f.startsWith("docs/")?"internal-or-customer-documentation":f.includes("/public/")?"public":"public-or-shared";
 inventory.push({surface_id:f.replace(/[^a-z0-9]+/gi,"-").replace(/^-|-$/g,"").toLowerCase(),route_or_file:f,route:extra.route||"",audience,type,states:extra.states||"not-applicable",brand_status:"NEEDS_MANUAL_REVIEW",terminology_status:"NEEDS_MANUAL_REVIEW",accessibility_status:/^(route|component)/.test(type)?"NEEDS_VERIFICATION":"REVIEW_IF_APPLICABLE",claim_status:"NEEDS_CLAIM_REVIEW",test_status:"NO_SURFACE_SPECIFIC_EVIDENCE_RECORDED",evidence:"Inventory discovery only; automated detection is not certification.",owner:"UNASSIGNED"});
}
for(const p of routes)add(p,"route",{route:routePath(p),states:(stateMap.get(path.dirname(p))||["default"]).join(",")});
for(const p of states)add(p,"route-state",{route:routePath(p),states:path.basename(p).replace(/\.(?:tsx?|jsx?)$/i,"")});
for(const p of comps)add(p,"component");
for(const p of css)add(p,"css-design-token");
for(const p of assets)add(p,"public-brand-or-product-asset");
for(const p of metadata)add(p,"metadata-structured-data");
for(const p of comms)add(p,"customer-communication");
for(const p of customerDocs)add(p,"customer-facing-or-governance-document");
for(const p of files){if(!inventory.some(x=>x.route_or_file===rel(p))){const t=p.startsWith(src+path.sep)?(/layout\.(?:tsx?|jsx?)$/i.test(p)?"layout-shell":"application-source"):p.startsWith(pub+path.sep)?"public-asset":"supporting-communication-or-content";add(p,t)}}

const rules=[
 {name:"legacy-identity",regex:/Kognivon|AIVON Learning OS|Learning Intelligence/gi,scope:p=>p.startsWith(src+path.sep)||p.startsWith(pub+path.sep)||p.startsWith(docs+path.sep),disposition:"CLASSIFY_COMPATIBILITY_HISTORY_FIXTURE_OR_CUSTOMER_FACING"},
 {name:"obsolete-slogan",regex:/Expect\s*<|Expect\s+Build\s+Assess\s+Prove\s+Know\s+Act/gi,scope:p=>p.startsWith(src+path.sep)||p.startsWith(pub+path.sep)||p.startsWith(docs+path.sep),disposition:"REVIEW_AND_RECORD_DISPOSITION"},
 {name:"legacy-color",regex:/#(?:147AC5|63BDE8|092844)\b/gi,scope:p=>p.startsWith(src+path.sep)||p.startsWith(pub+path.sep),disposition:"REVIEW_IF_ACTIVE_CUSTOMER_FACING_STYLE"},
 {name:"placeholder-language",regex:/\b(?:coming soon|lorem ipsum|TODO: replace|placeholder text)\b/gi,scope:p=>p.startsWith(src+path.sep)||p.startsWith(pub+path.sep),disposition:"REVIEW_LIVE_CONTENT_NOT_COMMENTS_OR_FIXTURES"},
 {name:"unsupported-claim-candidate",regex:/\b(?:guaranteed? ROI|100%\s+compliance|fully compliant|certified by|zero risk|unhackable|autonomous competence certification)\b/gi,scope:p=>(p.startsWith(src+path.sep)||p.startsWith(pub+path.sep)||(p.startsWith(docs+path.sep)&&!p.endsWith("KALAM_CLAIM_REGISTRY.md"))),disposition:"VERIFY_EVIDENCE_OR_REMOVE_OR_QUALIFY"},
 {name:"dead-anchor-candidate",regex:/(?:href|to)\s*=\s*["']#["']/gi,scope:p=>p.startsWith(src+path.sep),disposition:"REVIEW_ANCHOR_TARGET_AND_NAVIGATION_INTENT"},
 {name:"empty-href-candidate",regex:/href\s*=\s*["']\s*["']/gi,scope:p=>p.startsWith(src+path.sep),disposition:"REVIEW_EMPTY_LINK_TARGET"},
 {name:"empty-click-handler-candidate",regex:/onClick\s*=\s*\{\s*(?:\(\s*\)\s*=>\s*\{\s*\}|function\s*\(\s*\)\s*\{\s*\})\s*\}/gi,scope:p=>p.startsWith(src+path.sep),disposition:"REVIEW_NOOP_INTERACTION"}
];
const findings=[];
for(const p of files){const text=read(p),lines=text.split(/\r?\n/);for(const rule of rules){if(!rule.scope(p))continue;rule.regex.lastIndex=0;let m;while((m=rule.regex.exec(text))!==null){const line=text.slice(0,m.index).split("\n").length;findings.push({rule:rule.name,file:rel(p),line,match:m[0],disposition:rule.name==="legacy-identity"?(rel(p).startsWith("docs/06-delivery/KOGNIVON_TASK_")||p.endsWith("KOGNIVON_LOCAL_REMAINING_TASKS_CLOSURE_2026-09-29.md")||p.endsWith("PHASE_0_EXIT_EVIDENCE.md")||p.endsWith("ADR-014-KALAM-BRAND-ARCHITECTURE.md")?"APPROVED_HISTORICAL_DELIVERY_OR_DECISION_RECORD":p.endsWith("KALAM_9_9_BRAND_SURFACE_GOVERNANCE.md")?"APPROVED_LEGACY_IDENTITY_POLICY_REFERENCE":"REQUIRES_MANUAL_CLASSIFICATION"):rule.disposition,evidence:(lines[line-1]||"").trim().slice(0,180)});if(m[0].length===0)rule.regex.lastIndex++}}}
const pageMetadata=routes.map(p=>{const own=read(p),layout=path.join(path.dirname(p),"layout.tsx"),rootLayout=path.join(app,"layout.tsx"),pattern=/\bexport\s+(?:const|async\s+function)\s+metadata\b|\bexport\s+const\s+generateMetadata\b/;const inherited=(exists(layout)&&pattern.test(read(layout)))||(exists(rootLayout)&&pattern.test(read(rootLayout)));return{route:routePath(p),file:rel(p),metadata:pattern.test(own)?"PAGE_LEVEL":inherited?"INHERITED_LAYOUT_POSSIBLE":"NOT_DETECTED_STATIC_REVIEW_REQUIRED"}});
const routeStateCoverage=routes.map(p=>{let d=path.dirname(p),found=[];while(d.startsWith(app)){for(const kind of ["loading","error","not-found","global-error"]){const stateFile=path.join(d,kind+".tsx");if(exists(stateFile))found.push(rel(stateFile))}if(d===app)break;d=path.dirname(d)}return{route:routePath(p),file:rel(p),inherited_states:found}});
const routeStateSummary={routes:routeStateCoverage.length,with_loading:routeStateCoverage.filter(x=>x.inherited_states.some(f=>f.endsWith("/loading.tsx"))).length,with_error_boundary:routeStateCoverage.filter(x=>x.inherited_states.some(f=>f.endsWith("/error.tsx"))).length,with_not_found:routeStateCoverage.filter(x=>x.inherited_states.some(f=>f.endsWith("/not-found.tsx"))).length,with_global_error:routeStateCoverage.filter(x=>x.inherited_states.some(f=>f.endsWith("/global-error.tsx"))).length};
let commit="unknown";try{commit=execFileSync("git",["rev-parse","HEAD"],{encoding:"utf8"}).trim()}catch{}
let workingTreeChanges=[];try{workingTreeChanges=execFileSync("git",["status","--porcelain"],{encoding:"utf8"}).split(/\r?\n/).filter(line=>line&&!line.slice(3).startsWith("qa/generated/"))}catch{}
const summary={generated_at:new Date().toISOString(),commit,working_tree:{dirty:workingTreeChanges.length>0,change_count:workingTreeChanges.length},counts:{discovery_files:files.length,routes:routes.length,route_state_files:states.length,components:comps.length,css_design_files:css.length,public_assets:assets.length,metadata_candidates:metadata.length,communication_candidates:comms.length,customer_documentation_files:customerDocs.length,inventory_rows:inventory.length,automated_findings:findings.length},route_state_coverage:routeStateSummary,limitations:["Discovery inventory is not a manual brand disposition.","Regex findings require contextual classification; matches are not automatically defects.","Static metadata detection cannot prove rendered metadata or inheritance correctness.","Dead links/actions, interaction behavior, visual quality, responsive behavior, accessibility and claims require dedicated verification.","No 9.9 score or 100% certification is inferred from this report."],inventory,findings,page_metadata:pageMetadata,route_state_details:routeStateCoverage};
fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,"kalam-brand-surface-inventory.json"),JSON.stringify(summary,null,2)+"\n");
const cols=["surface_id","route_or_file","route","audience","type","states","brand_status","terminology_status","accessibility_status","claim_status","test_status","evidence","owner"],esc=v=>'"'+String(v??"").replace(/"/g,'""')+'"';
fs.writeFileSync(path.join(out,"kalam-brand-surface-inventory.csv"),[cols.join(","),...inventory.map(x=>cols.map(k=>esc(x[k])).join(","))].join("\n")+"\n");
const findingCols=["rule","file","line","match","disposition","evidence"];fs.writeFileSync(path.join(out,"kalam-brand-surface-findings.csv"),[findingCols.join(","),...findings.map(x=>findingCols.map(k=>esc(x[k])).join(","))].join("\n")+"\n");
const report=["# Kalam Brand Surface Inventory","","Generated: "+summary.generated_at,"Commit: "+summary.commit,"Working tree dirty: "+summary.working_tree.dirty,"Working tree change count: "+summary.working_tree.change_count,"","## Discovery counts","",...Object.entries(summary.counts).map(([k,v])=>"- "+k+": "+v),"","## Automated finding dispositions","",...Object.entries(Object.groupBy(findings,x=>x.disposition)).map(([k,v])=>"- "+k+": "+v.length),"","## Route-state coverage","",...Object.entries(routeStateSummary).map(([k,v])=>"- "+k+": "+v),"","## Metadata review","","| Route | Metadata detection | Source |","|---|---|---|",...pageMetadata.map(x=>"| "+x.route+" | "+x.metadata+" | "+x.file+" |"),"","## Limitations","",...summary.limitations.map(x=>"- "+x),"","Full row-level inventory and findings are in the adjacent JSON and CSV files.",""].join("\n");
fs.writeFileSync(path.join(out,"KALAM_BRAND_SURFACE_INVENTORY.md"),report);
console.log("KALAM BRAND SURFACE INVENTORY GENERATED");console.log(JSON.stringify(summary.counts,null,2));console.log("Output: "+path.relative(root,out));
