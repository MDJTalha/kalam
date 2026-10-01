"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, CheckCircle2, RefreshCcw } from "lucide-react";

type Intervention = { id:string; intervention_type:string; title:string; objective:string; status:string; assignee_id:string|null; due_at:string|null; completed_at:string|null };
type Progress = { status:string; interactions:number; evidence_count:number; verified_evidence_count:number; progress_signal:string };
type DevelopmentEvidence = { id:string; evidence_type:string; description:string; observed_at:string; verification_status:string; metadata_json:Record<string,unknown> };
type Props = { canVerify:boolean };
const pretty=(v:string)=>v.replaceAll("_"," ");

export function DevelopmentExecution({canVerify}:Props){
  const [items,setItems]=useState<Intervention[]>([]); const [progress,setProgress]=useState<Record<string,Progress>>({}); const [reviewFor,setReviewFor]=useState(""); const [reviewEvidence,setReviewEvidence]=useState<DevelopmentEvidence[]>([]); const [busy,setBusy]=useState(false); const [error,setError]=useState(""); const [message,setMessage]=useState(""); const [evidenceFor,setEvidenceFor]=useState(""); const [evidence,setEvidence]=useState(""); const [level,setLevel]=useState("");
  async function load(){
    setBusy(true); setError("");
    try {
      const r=await fetch("/api/v1/development/interventions",{cache:"no-store"});
      const d=await r.json().catch(()=>[]);
      if(!r.ok) throw new Error(d.detail||"Development interventions could not be loaded.");
      const next=Array.isArray(d)?d as Intervention[]:[];
      const progressRows=await Promise.all(next.map(async item=>{
        const response=await fetch("/api/v1/development/interventions/"+item.id+"/progress",{cache:"no-store"});
        const value=await response.json().catch(()=>null);
        return response.ok&&value&&typeof value==="object" ? [item.id,value as Progress] as const : null;
      }));
      setItems(next);
      setProgress(Object.fromEntries(progressRows.filter((x): x is readonly [string,Progress]=>Boolean(x))));
    }
    catch(e){setError(e instanceof Error?e.message:"Development interventions could not be loaded.");} finally{setBusy(false);}
  }
  useEffect(()=>{const timer=window.setTimeout(()=>{void load();},0); return ()=>window.clearTimeout(timer);},[]);
  async function submitEvidence(id:string){
    if(!evidence.trim()) { setError("Evidence description is required."); return; }
    setBusy(true); setError(""); setMessage("");
    try { const r=await fetch("/api/v1/development/interventions/"+id+"/evidence",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({evidence_type:"practical_demonstration",description:evidence.trim(),observed_at:new Date().toISOString(),demonstrated_level:level?Number(level):null})}); const d=await r.json().catch(()=>({})); if(!r.ok) throw new Error(d.detail||"Evidence could not be submitted."); setEvidence(""); setLevel(""); setEvidenceFor(""); setMessage("Evidence submitted for verification. Once verified, the governed capability gap is recalculated."); await load(); }
    catch(e){setError(e instanceof Error?e.message:"Evidence could not be submitted.");} finally{setBusy(false);}
  }
  async function review(id:string){
    setBusy(true); setError("");
    try {
      const r=await fetch("/api/v1/development/interventions/"+id,{cache:"no-store"});
      const d=await r.json().catch(()=>null);
      if(!r.ok) throw new Error(d?.detail||"Development evidence could not be loaded.");
      setReviewFor(id); setReviewEvidence(Array.isArray(d?.evidence)?d.evidence:[]);
    } catch(e){setError(e instanceof Error?e.message:"Development evidence could not be loaded.");} finally{setBusy(false);}
  }
  async function verify(interventionId:string,evidenceId:string){
    setBusy(true); setError(""); setMessage("");
    try {
      const r=await fetch("/api/v1/development/interventions/"+interventionId+"/evidence/"+evidenceId+"/verify",{method:"POST"});
      const d=await r.json().catch(()=>({}));
      if(!r.ok) throw new Error(d.detail||"Evidence verification failed.");
      setMessage("Development evidence verified. The governed capability gap was recalculated; reassessment can now use the updated evidence.");
      await review(interventionId);
      await load();
    } catch(e){setError(e instanceof Error?e.message:"Evidence verification failed.");} finally{setBusy(false);}
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
      <p>{item.objective}</p><div className="compact-list"><div className="compact-row"><span>Due</span><strong>{item.due_at?new Date(item.due_at).toLocaleDateString():"No due date"}</strong></div><div className="compact-row"><span>Assignee</span><strong>{item.assignee_id?"Assigned":"Self / unassigned"}</strong></div>{progress[item.id]&&<><div className="compact-row"><span>Evidence</span><strong>{progress[item.id].evidence_count} submitted · {progress[item.id].verified_evidence_count} verified</strong></div><div className="compact-row"><span>Signal</span><strong>{pretty(progress[item.id].progress_signal)}</strong></div></>}</div>
      <div className="card-actions">{item.status==="planned"&&<button className="button button-primary" disabled={busy} onClick={()=>void update(item.id,"in_progress")}>Start intervention</button>}{item.status==="in_progress"&&<><button className="button button-secondary" disabled={busy} onClick={()=>setEvidenceFor(evidenceFor===item.id?"":item.id)}>Capture evidence</button><button className="button button-primary" disabled={busy} onClick={()=>void update(item.id,"completed")}>Mark completed</button></>}{item.status==="completed"&&<span className="form-success" role="status"><CheckCircle2 size={15}/>Completed</span>}</div>
      {progress[item.id]?.evidence_count>0&&canVerify&&<div className="card-actions"><button className="button button-secondary" disabled={busy} onClick={()=>void review(item.id)}>Review evidence <ArrowRight size={14}/></button></div>}
      {reviewFor===item.id&&<div className="compact-list" aria-label="Evidence verification"><strong>Evidence review</strong>{reviewEvidence.length?reviewEvidence.map(row=><div className="compact-row" key={row.id}><div><strong>{pretty(row.evidence_type)}</strong><small>{row.description}</small><small>{row.metadata_json.demonstrated_level?String(row.metadata_json.demonstrated_level)+"/5 · ":""}{new Date(row.observed_at).toLocaleString()}</small></div>{row.verification_status==="verified"?<span className="status-badge success">Verified</span>:<button className="button button-primary" disabled={busy} onClick={()=>void verify(item.id,row.id)}>Verify evidence</button>}</div>):<small>No evidence has been submitted.</small>}</div>}
      {progress[item.id]?.verified_evidence_count>0&&<div className="card-actions"><Link className="button button-secondary" href="/dashboard/capability-gaps">Review recalculated gap <ArrowRight size={14}/></Link><Link className="button button-secondary" href="/dashboard/capability-assessments">Open reassessment workspace <ArrowRight size={14}/></Link></div>}
      {evidenceFor===item.id&&<div className="compact-list" aria-label="Evidence capture"><label className="field"><span>What was demonstrated?</span><textarea value={evidence} onChange={e=>setEvidence(e.target.value)} rows={3} maxLength={10000}/></label><label className="field"><span>Demonstrated capability level (1–5, optional)</span><input type="number" min={1} max={5} step={0.1} value={level} onChange={e=>setLevel(e.target.value)}/></label><button className="button button-primary" disabled={busy} onClick={()=>void submitEvidence(item.id)}>Submit evidence</button></div>}
    </article>)}</div>:<div className="empty-state"><p>No active development interventions yet.</p><small>Accept a coaching, mentoring or experiential recommendation to create an executable intervention.</small></div>}
  </section>;
}
