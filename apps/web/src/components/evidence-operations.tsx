"use client";
import { useMemo, useState } from "react";
import { Check, CircleAlert, FileCheck2, Loader2, Plus, X } from "lucide-react";

type Person={id:string;first_name:string;last_name:string;email:string;job_title?:string|null};
type Competency={id:string;name:string;code:string;status:string};
type Evidence={id:string;user_id:string;target_type:string;target_id:string;evidence_type:string;source_type:string;source_id?:string|null;demonstrated_level:number;confidence:number;status:string;observed_at:string;notes?:string|null;rejection_reason?:string|null};
type Props={people:Person[];competencies:Competency[];initialEvidence:Evidence[];canVerify:boolean};

const levels=[1,2,3,4,5];
const label=(p:Pick<Person,"first_name"|"last_name">)=>[p.first_name,p.last_name].filter(Boolean).join(" ");

export function EvidenceOperations({people,competencies,initialEvidence,canVerify}:Props){
 const [rows,setRows]=useState(initialEvidence); const [selectedUser,setSelectedUser]=useState(""); const [status,setStatus]=useState("all");
 const [busy,setBusy]=useState(false); const [message,setMessage]=useState(""); const [error,setError]=useState("");
 const [form,setForm]=useState({user_id:people[0]?.id||"",competency_id:competencies[0]?.id||"",level:"3",confidence:"80",source_type:"manual_observation",evidence_type:"observation",notes:""});
 const visible=useMemo(()=>rows.filter(x=>(selectedUser?x.user_id===selectedUser:true)&&(status==="all"||x.status===status)),[rows,selectedUser,status]);
 const personMap=useMemo(()=>new Map(people.map(p=>[p.id,p])),[people]); const competencyMap=useMemo(()=>new Map(competencies.map(c=>[c.id,c])),[competencies]);
 const set=(key:keyof typeof form,value:string)=>setForm(v=>({...v,[key]:value}));
 async function create(){setBusy(true);setError("");setMessage("");try{const r=await fetch("/api/v1/evidence",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({user_id:form.user_id,target_type:"competency",target_id:form.competency_id,evidence_type:form.evidence_type,source_type:form.source_type,demonstrated_level:Number(form.level),confidence:Number(form.confidence),notes:form.notes||null})});const data=await r.json().catch(()=>({}));if(!r.ok)throw new Error(data.detail||"Evidence could not be recorded.");setRows(v=>[data,...v]);setMessage("Evidence recorded and queued for verification.");set("notes","");}catch(e){setError(e instanceof Error?e.message:"Evidence action failed.");}finally{setBusy(false)}}
 async function decide(id:string,decision:"verified"|"rejected"){setBusy(true);setError("");try{const reason=decision==="rejected"?window.prompt("Reason for rejecting this evidence:")||"Verification reviewer rejected the evidence.":undefined;const r=await fetch(`/api/v1/evidence/${id}/decision`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({decision,reason})});const data=await r.json().catch(()=>({}));if(!r.ok)throw new Error(data.detail||"Verification action failed.");setRows(v=>v.map(x=>x.id===id?data:x));setMessage(decision==="verified"?"Evidence verified.":"Evidence rejected.");}catch(e){setError(e instanceof Error?e.message:"Verification action failed.");}finally{setBusy(false)}}
 return <div className="two-column">
  <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Capture</span><h2>Record capability evidence</h2><p>Capture observable evidence against a governed competency and keep provenance reviewable.</p></div></div>
   <div className="form-grid">
    <label className="form-field"><span>Person *</span><select value={form.user_id} onChange={e=>set("user_id",e.target.value)}>{people.map(p=><option key={p.id} value={p.id}>{label(p)} · {p.job_title||p.email}</option>)}</select></label>
    <label className="form-field"><span>Competency *</span><select value={form.competency_id} onChange={e=>set("competency_id",e.target.value)}>{competencies.map(c=><option key={c.id} value={c.id}>{c.name} · {c.code}</option>)}</select></label>
    <label className="form-field"><span>Demonstrated level *</span><select value={form.level} onChange={e=>set("level",e.target.value)}>{levels.map(x=><option key={x} value={x}>{x} · {["Foundational","Developing","Proficient","Advanced","Expert"][x-1]}</option>)}</select></label>
    <label className="form-field"><span>Confidence *</span><input type="number" min="0" max="100" value={form.confidence} onChange={e=>set("confidence",e.target.value)}/></label>
    <label className="form-field"><span>Source</span><select value={form.source_type} onChange={e=>set("source_type",e.target.value)}><option value="manual_observation">Manual observation</option><option value="work_product">Work product</option><option value="external">External</option><option value="course_completion">Course completion</option><option value="credential">Credential</option></select></label>
    <label className="form-field"><span>Evidence type</span><select value={form.evidence_type} onChange={e=>set("evidence_type",e.target.value)}><option value="observation">Observation</option><option value="demonstration">Demonstration</option><option value="artifact">Artifact</option><option value="completion">Completion</option><option value="credential">Credential</option></select></label>
    <label className="form-field full"><span>Reviewer notes</span><textarea value={form.notes} placeholder="Describe what was observed, demonstrated or submitted." onChange={e=>set("notes",e.target.value)}/></label>
   </div>
   {error&&<div className="form-error" role="alert"><CircleAlert size={15}/>{error}</div>}{message&&<div className="form-success" role="status"><Check size={15}/>{message}</div>}
   <div className="form-actions"><button className="button button-primary" type="button" disabled={busy||!form.user_id||!form.competency_id} onClick={create}>{busy?<><Loader2 size={15}/> Saving…</>:<><Plus size={15}/> Record evidence</>}</button></div>
  </section>
  <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Review queue</span><h2>Evidence verification</h2></div><span className="section-meta">{visible.length} records</span></div>
   <div className="form-grid"><label className="form-field"><span>Person</span><select value={selectedUser} onChange={e=>setSelectedUser(e.target.value)}><option value="">All people</option>{people.map(p=><option key={p.id} value={p.id}>{label(p)}</option>)}</select></label><label className="form-field"><span>Status</span><select value={status} onChange={e=>setStatus(e.target.value)}><option value="all">All statuses</option><option value="pending">Pending</option><option value="verified">Verified</option><option value="rejected">Rejected</option></select></label></div>
   {visible.length?<div className="table-wrap"><table className="data-table"><thead><tr><th>Person</th><th>Competency</th><th>Level</th><th>Confidence</th><th>Status</th>{canVerify&&<th>Action</th>}</tr></thead><tbody>{visible.map(x=><tr key={x.id}><td><strong>{label(personMap.get(x.user_id)||{first_name:"Unknown",last_name:""})}</strong><small>{new Date(x.observed_at).toLocaleDateString()}</small></td><td>{competencyMap.get(x.target_id)?.name||"Competency"}</td><td>{x.demonstrated_level}/5</td><td>{x.confidence}%</td><td><span className={`status-badge status-${x.status}`}>{x.status}</span>{x.rejection_reason&&<small>{x.rejection_reason}</small>}</td>{canVerify&&<td>{x.status==="pending"?<div className="inline-actions"><button className="button button-secondary" disabled={busy} onClick={()=>void decide(x.id,"verified")} title="Verify evidence"><Check size={14}/></button><button className="button button-secondary" disabled={busy} onClick={()=>void decide(x.id,"rejected")} title="Reject evidence"><X size={14}/></button></div>:<FileCheck2 size={16}/>}</td>}</tr>)}</tbody></table></div>:<div className="empty-state"><FileCheck2 size={24}/><p>No evidence matches the current filters.</p></div>}
  </section>
 </div>;
}
