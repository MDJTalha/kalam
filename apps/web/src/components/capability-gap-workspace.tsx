"use client";
import { useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, RefreshCcw, Search, ShieldAlert, Target } from "lucide-react";
import { GovernedAIAction } from "@/components/governed-ai-action";
import { PeopleLookupSelect } from "@/components/people-lookup-select";
type Gap={user_id:string;role_id:string;role:string;role_requirement_id:string;target_type:string;target_id:string;target:string|null;required_level:number;demonstrated_level:number|null;gap:number|null;severity:string;criticality:string;weight:number;evidence_confidence:number;evidence_count:number;evidence_observed_at:string|null;evidence_freshness:string;calculation_version:string};
type Summary={scope:string;total_requirements:number;material_gaps:number;counts:Record<string,number>;critical_exposure:number;major_exposure:number;weighted_gap:number;calculation_version:string;freshness_days:number};
type Person={id:string;first_name:string;last_name:string;email:string;job_title?:string|null};
type Props={initialGaps:Gap[];initialSummary:Summary;people:Person[];canManage:boolean;teamScoped:boolean;currentUserId:string};
const label=(s:string)=>s.replaceAll("_"," ");
const severityClass=(s:string)=>s==="critical_gap"?"status-danger":s==="major_gap"?"status-warning":s==="moderate_gap"?"status-neutral":s==="met"?"status-success":"status-neutral";
export function CapabilityGapWorkspace({initialGaps,initialSummary,people,canManage,teamScoped,currentUserId}:Props){
 const [gaps,setGaps]=useState(initialGaps); const [summary,setSummary]=useState(initialSummary); const [personId,setPersonId]=useState(currentUserId);
 const [severity,setSeverity]=useState(""); const [q,setQ]=useState(""); const [busy,setBusy]=useState(false); const [message,setMessage]=useState(""); const [error,setError]=useState("");
 const visible=useMemo(()=>gaps.filter(x=>!severity||x.severity===severity).filter(x=>!q||((x.target||"")+" "+x.role).toLowerCase().includes(q.toLowerCase())),[gaps,severity,q]);
 async function refresh(){
  setBusy(true);setError("");setMessage("");
  try{
   if(canManage){const r=await fetch("/api/v1/capability-gaps/recalculate",{method:"POST"});const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.detail||"Gap recalculation failed.");}
   const query=canManage||teamScoped?"":("?user_id="+encodeURIComponent(personId));
   const summaryQuery=canManage?"scope=enterprise":teamScoped?"scope=direct_reports":"scope=person&scope_id="+encodeURIComponent(personId);
   const [gr,sr]=await Promise.all([fetch("/api/v1/capability-gaps"+query,{cache:"no-store"}),fetch("/api/v1/capability-gaps/summary?"+summaryQuery,{cache:"no-store"})]);
   const gd=await gr.json().catch(()=>[]),sd=await sr.json().catch(()=>({}));
   if(!gr.ok)throw new Error(gd.detail||"Gap data could not be loaded.");if(!sr.ok)throw new Error(sd.detail||"Gap summary could not be loaded.");
   setGaps(Array.isArray(gd)?gd:[]);setSummary(sd);setMessage("Capability gaps refreshed using the governed Phase 4 calculation.");
  }catch(e){setError(e instanceof Error?e.message:"Gap refresh failed.");}finally{setBusy(false)}
 }
 const counts=summary.counts||{};
 return <div className="stack-lg">
  <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Capability exposure</span><h2>Capability Gap Engine</h2><p>Required capability versus demonstrated capability, with evidence confidence and freshness.</p></div><button className="button button-secondary" disabled={busy} onClick={()=>void refresh()}><RefreshCcw size={14}/> {busy?"Refreshing…":canManage?"Recalculate":teamScoped?"Refresh team gaps":"Refresh my gaps"}</button></div>
   {error&&<div className="form-error" role="alert"><AlertTriangle size={15}/>{error}</div>}{message&&<div className="form-success" role="status"><CheckCircle2 size={15}/>{message}</div>}
   {canManage&&<div style={{maxWidth:420}}><PeopleLookupSelect label="Person drill-down" value={personId} onChange={id=>{setPersonId(id);void (async()=>{const r=await fetch("/api/v1/capability-gaps?user_id="+encodeURIComponent(id),{cache:"no-store"});const data=await r.json().catch(()=>[]);if(r.ok)setGaps(Array.isArray(data)?data:[])})()}} initialPeople={people}/></div>}
   <div className="metric-grid"><div className="metric-card"><span>Requirements</span><strong>{summary.total_requirements}</strong><small>role requirements evaluated</small></div><div className="metric-card"><span>Material gaps</span><strong>{summary.material_gaps}</strong><small>minor through critical</small></div><div className="metric-card"><span>Critical exposure</span><strong>{summary.critical_exposure}</strong><small>critical gap records</small></div><div className="metric-card"><span>Major exposure</span><strong>{summary.major_exposure}</strong><small>major gap records</small></div></div>
  </section>
  {personId===currentUserId ? <GovernedAIAction title="Make my gaps actionable" description="Generate a governed explanation of your persisted role-to-skill gaps using authorized learning evidence only." question="Explain my current capability gaps, identify the most important development priorities, and suggest grounded learning actions without making employment decisions." mode="skill_gap" /> : null}
  <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Gap inventory</span><h2>Where capability is below requirement</h2></div></div>
   <div className="filter-bar"><label className="form-field"><span>Search</span><div className="input-with-icon"><Search size={15}/><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Capability, competency, skill or role"/></div></label><label className="form-field"><span>State</span><select value={severity} onChange={e=>setSeverity(e.target.value)}><option value="">All states</option>{["insufficient_evidence","critical_gap","major_gap","moderate_gap","minor_gap","met"].map(x=><option key={x} value={x}>{label(x)}</option>)}</select></label></div>
   <div className="status-summary"><span><ShieldAlert size={14}/> Critical {counts.critical_gap||0}</span><span>Major {counts.major_gap||0}</span><span>Moderate {counts.moderate_gap||0}</span><span>Minor {counts.minor_gap||0}</span><span>Insufficient evidence {counts.insufficient_evidence||0}</span></div>
   {visible.length?<div className="table-wrap"><table className="data-table"><thead><tr><th>Target</th><th>Role</th><th>Required</th><th>Demonstrated</th><th>Gap</th><th>Evidence</th><th>State</th></tr></thead><tbody>{visible.map(x=><tr key={x.role_requirement_id+":"+x.user_id}><td><strong>{x.target||"Unnamed target"}</strong><small>{x.target_type} · {x.criticality} criticality</small></td><td><strong>{x.role}</strong><small>{x.user_id===currentUserId?"My profile":"Team / organization"}</small></td><td>{x.required_level.toFixed(2)}/5</td><td>{x.demonstrated_level===null?"Insufficient":x.demonstrated_level.toFixed(2)+"/5"}</td><td>{x.gap===null?"—":x.gap.toFixed(2)}</td><td><small>{x.evidence_count} verified · {x.evidence_confidence}% confidence</small><small>{x.evidence_observed_at?"Observed "+new Date(x.evidence_observed_at).toLocaleDateString()+" · "+x.evidence_freshness:"No current evidence"}</small></td><td><span className={severityClass(x.severity)}>{label(x.severity)}</span></td></tr>)}</tbody></table></div>:<div className="empty-state"><Target size={24}/><p>No capability gap records match this view.</p><small>Requirements without a requirement mapping are not fabricated as gaps.</small></div>}
  </section>
  <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Governance</span><h2>Calculation transparency</h2><p><strong>Gap = Required Level − Demonstrated Level.</strong> Negative gaps are reported as zero and classified Met. Missing or stale verified evidence produces <strong>Insufficient evidence</strong> for non-met requirements. Evidence older than {summary.freshness_days} days is treated as stale. Calculation version: {summary.calculation_version}.</p></div></div></section>
 </div>
}
