"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, RefreshCcw } from "lucide-react";

type Intervention = { id:string; intervention_type:string; title:string; objective:string; status:string; assignee_id:string|null; due_at:string|null; completed_at:string|null };
const pretty=(v:string)=>v.replaceAll("_"," ");

export function DevelopmentExecution(){
  const [items,setItems]=useState<Intervention[]>([]); const [busy,setBusy]=useState(false); const [error,setError]=useState(""); const [message,setMessage]=useState(""); const [evidenceFor,setEvidenceFor]=useState(""); const [evidence,setEvidence]=useState(""); const [level,setLevel]=useState("");
  async function load(){
    setBusy(true); setError("");
    try { const r=await fetch("/api/v1/development/interventions",{cache:"no-store"}); const d=await r.json().catch(()=>[]); if(!r.ok) throw new Error(d.detail||"Development interventions could not be loaded."); setItems(Array.isArray(d)?d:[]); }
    catch(e){setError(e instanceof Error?e.message:"Development interventions could not be loaded.");} finally{setBusy(false);}
  }
  useEffect(()=>{void load();},[]);
  async function submitEvidence(id:string){
    if(!evidence.trim()) { setError("Evidence description is required."); return; }
    setBusy(true); setError(""); setMessage("");
    try { const r=await fetch("/api/v1/development/interventions/"+id+"/evidence",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({evidence_type:"practical_demonstration",description:evidence.trim(),observed_at:new Date().toISOString(),demonstrated_level:level?Number(level):null})}); const d=await r.json().catch(()=>({})); if(!r.ok) throw new Error(d.detail||"Evidence could not be submitted."); setEvidence(""); setLevel(""); setEvidenceFor(""); setMessage("Evidence submitted for verification."); }
    catch(e){setError(e instanceof Error?e.message:"Evidence could not be submitted.");} finally{setBusy(false);}
  }
  async function update(id:string,status:string){
    setBusy(true); setError(""); setMessage("");
    try { const r=await fetch("/api/v1/development/interventions/"+id,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({status})}); const d=await r.json().catch(()=>({})); if(!r.ok) throw new Error(d.detail||"Intervention could not be updated."); setItems(v=>v.map(x=>x.id===id?d:x)); setMessage(status==="completed"?"Development intervention completed and recorded.":"Development intervention moved to in progress."); }
    catch(e){setError(e instanceof Error?e.message:"Intervention could not be updated.");} finally{setBusy(false);}
  }
  return <section className="data-panel" aria-labelledby="development-execution-title">
    <div className="section-heading compact"><div><span className="eyebrow">Development execution</span><h2 id="development-execution-title">Active interventions</h2><p>Execute coaching, mentoring and experiential actions, then capture evidence and progress against the original development objective.</p></div><button className="button button-secondary" onClick={()=>void load()} disabled={busy}><RefreshCcw size={14}/>{busy?"Refreshing…":"Refresh"}</button></div>
    {error&&<div className="form-error" role="alert">{error}</div>}{message&&<div className="form-success" role="status"><CheckCircle2 size={15}/>{message}</div>}
    {items.length?<div className="recommendation-grid">{items.slice(0,24).map(item=><article className="data-card" key={item.id}>
      <div className="section-heading compact"><div><span className="eyebrow">{pretty(item.intervention_type)} · {pretty(item.status)}</span><h3>{item.title}</h3></div></div>
      <p>{item.objective}</p><div className="compact-list"><div className="compact-row"><span>Due</span><strong>{item.due_at?new Date(item.due_at).toLocaleDateString():"No due date"}</strong></div><div className="compact-row"><span>Assignee</span><strong>{item.assignee_id?"Assigned":"Self / unassigned"}</strong></div></div>
      <div className="card-actions">{item.status==="planned"&&<button className="button button-primary" disabled={busy} onClick={()=>void update(item.id,"in_progress")}>Start intervention</button>}{item.status==="in_progress"&&<><button className="button button-secondary" disabled={busy} onClick={()=>setEvidenceFor(evidenceFor===item.id?"":item.id)}>Capture evidence</button><button className="button button-primary" disabled={busy} onClick={()=>void update(item.id,"completed")}>Mark completed</button></>}{item.status==="completed"&&<span className="form-success" role="status"><CheckCircle2 size={15}/>Completed</span>}</div>
      {evidenceFor===item.id&&<div className="compact-list" aria-label="Evidence capture"><label className="field"><span>What was demonstrated?</span><textarea value={evidence} onChange={e=>setEvidence(e.target.value)} rows={3} maxLength={10000}/></label><label className="field"><span>Demonstrated capability level (1–5, optional)</span><input type="number" min={1} max={5} step={0.1} value={level} onChange={e=>setLevel(e.target.value)}/></label><button className="button button-primary" disabled={busy} onClick={()=>void submitEvidence(item.id)}>Submit evidence</button></div>}
    </article>)}</div>:<div className="empty-state"><p>No active development interventions yet.</p><small>Accept a coaching, mentoring or experiential recommendation to create an executable intervention.</small></div>}
  </section>;
}
