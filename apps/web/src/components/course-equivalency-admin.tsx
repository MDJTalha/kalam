"use client";

import { useMemo, useState } from "react";
import { Loader2, Plus, Trash2 } from "lucide-react";

type Course={id:string;title:string};
type Equivalency={id:string;course_id:string;course_title:string;equivalent_course_id:string;equivalent_course_title:string;equivalency_type:string;notes?:string|null;active:boolean};

export function CourseEquivalencyAdmin({ courses, initial }: { courses: Course[]; initial: Equivalency[] }) {
  const [rows,setRows]=useState(initial);
  const [courseId,setCourseId]=useState("");
  const [equivalentId,setEquivalentId]=useState("");
  const [type,setType]=useState("full");
  const [notes,setNotes]=useState("");
  const [busy,setBusy]=useState(false);
  const [query,setQuery]=useState("");
  const [message,setMessage]=useState("");
  const [error,setError]=useState("");
  const available=useMemo(()=>courses.filter(c=>c.id!==courseId),[courses,courseId]);

  async function create() {
    if(!courseId||!equivalentId){setError("Select both courses.");return}
    setBusy(true);setError("");
    try {
      const res=await fetch("/api/lms/courses/equivalencies",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({course_id:courseId,equivalent_course_id:equivalentId,equivalency_type:type,notes:notes||null})});
      const data=await res.json().catch(()=>({}));
      if(!res.ok) throw new Error(data.detail||"Could not create equivalency.");
      setRows(current=>[data,...current]);setCourseId("");setEquivalentId("");setType("full");setNotes("");setMessage("Equivalency recorded.");
    } catch(e){setError(e instanceof Error?e.message:"The action failed.")} finally{setBusy(false)}
  }

  async function toggle(row:Equivalency) {
    setBusy(true);setError("");setMessage("");
    try {
      const res=await fetch("/api/lms/courses/equivalencies/"+row.id,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({active:!row.active})});
      const data=await res.json().catch(()=>({}));
      if(!res.ok)throw new Error(typeof data.detail==="string"?data.detail:"Could not update equivalency.");
      setRows(current=>current.map(item=>item.id===row.id?data:item));setMessage(data.active?"Equivalency activated.":"Equivalency deactivated.");
    } catch(e){setError(e instanceof Error?e.message:"The action failed.")} finally{setBusy(false)}
  }

  async function remove(id:string) {
    if(!window.confirm("Remove this course equivalency?")) return;
    setBusy(true);setError("");
    try {
      const res=await fetch("/api/lms/courses/equivalencies/"+id,{method:"DELETE"});
      if(!res.ok){const data=await res.json().catch(()=>({}));throw new Error(data.detail||"Could not remove equivalency.")}
      setRows(current=>current.filter(row=>row.id!==id));setMessage("Equivalency removed.");
    } catch(e){setError(e instanceof Error?e.message:"The action failed.")} finally{setBusy(false)}
  }

  return <div className="stack">
    <div className="data-panel">
      <div className="section-heading compact"><div><span className="eyebrow">Course governance</span><h2>Define equivalent learning</h2><p>Record reviewed course relationships for planning. An equivalency does not automatically grant completion or compliance credit.</p></div></div>
      <div className="form-grid">
        <label className="form-field"><span>Course</span><select value={courseId} onChange={e=>{setCourseId(e.target.value);setEquivalentId("")}}><option value="">Select course…</option>{courses.map(c=><option key={c.id} value={c.id}>{c.title}</option>)}</select></label>
        <label className="form-field"><span>Equivalent course</span><select value={equivalentId} onChange={e=>setEquivalentId(e.target.value)}><option value="">Select equivalent…</option>{available.map(c=><option key={c.id} value={c.id}>{c.title}</option>)}</select></label>
        <label className="form-field"><span>Relationship</span><select value={type} onChange={e=>setType(e.target.value)}><option value="full">Full equivalency</option><option value="partial">Partial equivalency</option><option value="credit_transfer">Credit transfer</option></select></label>
        <label className="form-field full"><span>Governance note</span><textarea value={notes} onChange={e=>setNotes(e.target.value)} placeholder="Document the business rule or accreditation basis."/></label>
      </div>
      {error&&<div className="form-error" role="alert">{error}</div>}{message&&<div className="form-success" role="status">{message}</div>}
      <div className="form-actions"><button className="button button-primary" onClick={create} disabled={busy}>{busy?<Loader2 size={15} className="spin"/>:<Plus size={15}/>} Add equivalency</button></div>
    </div>
    <div className="data-panel">
      <div className="section-heading compact"><div><span className="eyebrow">Governance register</span><h2>Current equivalencies</h2></div></div>
      <label className="form-field"><span>Search register</span><input type="search" value={query} onChange={event=>setQuery(event.target.value)} placeholder="Course or governance note" /></label>
      {rows.length?<div className="table-wrap"><table className="data-table"><thead><tr><th scope="col">Course</th><th scope="col">Equivalent</th><th scope="col">Type</th><th scope="col">Status</th><th scope="col">Actions</th></tr></thead><tbody>{rows.filter(row=>!query.trim() || `${row.course_title} ${row.equivalent_course_title} ${row.notes??""}`.toLowerCase().includes(query.trim().toLowerCase())).map(row=><tr key={row.id}><td><strong>{row.course_title}</strong></td><td>{row.equivalent_course_title}</td><td>{row.equivalency_type.replace("_"," ")}{row.notes&&<small>{row.notes}</small>}</td><td><span className={row.active?"status-badge success":"status-badge muted"}>{row.active?"Active":"Inactive"}</span></td><td><div className="inline-actions"><button className="button button-secondary" onClick={()=>void toggle(row)} disabled={busy}>{row.active?"Deactivate":"Activate"}</button><button className="button button-secondary" onClick={()=>void remove(row.id)} disabled={busy}><Trash2 size={14}/> Remove</button></div></td></tr>)}</tbody></table></div>:<p className="muted">No course equivalencies have been configured.</p>}
    </div>
  </div>;
}
