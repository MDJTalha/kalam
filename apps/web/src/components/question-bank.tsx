"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowDown, ArrowUp, Pencil, Save, Trash2, X } from "lucide-react";

type Question = { id:string; question_type:string; prompt:string; options:string[]; answer_key:{correct:string|string[]}; points:number; position:number };
type Props = { assessmentId:string; initialQuestions:Question[]; locked:boolean };

export function QuestionBank({ assessmentId, initialQuestions, locked }: Props) {
  const [questions,setQuestions] = useState(initialQuestions);
  const [editing,setEditing] = useState<string|null>(null);
  const [draft,setDraft] = useState({prompt:"",options:"",correct:"",points:"1",question_type:"single_choice"});
  const [busy,setBusy] = useState(false);
  const [message,setMessage] = useState("");
  const [error,setError] = useState("");

  function startEdit(q:Question) {
    setEditing(q.id); setDraft({prompt:q.prompt,options:q.options.join("\n"),correct:Array.isArray(q.answer_key.correct)?q.answer_key.correct.join(" | "):q.answer_key.correct,points:String(q.points),question_type:q.question_type});
    setMessage(""); setError("");
  }

  async function saveEdit() {
    if (!editing || draft.prompt.trim().length < 3) return;
    setBusy(true); setError(""); setMessage("");
    try {
      const response = await fetch("/api/lms/assessments/questions/"+editing,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({question_type:draft.question_type,prompt:draft.prompt.trim(),options:draft.options.split(/\r?\n/).map(s=>s.trim()).filter(Boolean),answer_key:{correct:draft.question_type==="multiple_choice"?draft.correct.split("|").map(s=>s.trim()).filter(Boolean):draft.correct.trim()},points:Number(draft.points)})});
      const data=await response.json().catch(()=>({}));
      if(!response.ok) throw new Error(data.detail||"Question could not be updated.");
      setQuestions(current=>current.map(q=>q.id===editing?{...q,question_type:draft.question_type,prompt:draft.prompt.trim(),options:draft.options.split(/\r?\n/).map(s=>s.trim()).filter(Boolean),answer_key:{correct:draft.question_type==="multiple_choice"?draft.correct.split("|").map(s=>s.trim()).filter(Boolean):draft.correct.trim()},points:Number(draft.points)}:q));
      setEditing(null); setMessage("Question updated.");
    } catch(e) { setError(e instanceof Error?e.message:"Update failed."); }
    finally { setBusy(false); }
  }

  async function remove(id:string) {
    if(!window.confirm("Delete this question? This action is audited and cannot be undone.")) return;
    setBusy(true); setError("");
    try { const response=await fetch("/api/lms/assessments/questions/"+id,{method:"DELETE"}); if(!response.ok){const data=await response.json().catch(()=>({}));throw new Error(data.detail||"Question could not be deleted.");} setQuestions(current=>current.filter(q=>q.id!==id)); setMessage("Question deleted."); }
    catch(e){setError(e instanceof Error?e.message:"Delete failed.");} finally{setBusy(false);}
  }

  async function move(index:number,direction:-1|1) {
    const target=index+direction; if(target<0||target>=questions.length) return;
    const next=[...questions]; [next[index],next[target]]=[next[target],next[index]];
    setBusy(true); setError("");
    try { const response=await fetch("/api/lms/assessments/"+assessmentId+"/questions/reorder",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question_ids:next.map(q=>q.id)})}); const data=await response.json().catch(()=>({})); if(!response.ok)throw new Error(data.detail||"Questions could not be reordered."); setQuestions(next.map((q,i)=>({...q,position:i+1}))); setMessage("Question order saved."); }
    catch(e){setError(e instanceof Error?e.message:"Reorder failed.");} finally{setBusy(false);}
  }

  return <div className="compact-list">    {error&&<div className="form-error" role="alert">{error}</div>}{message&&<div className="form-success" role="status">{message}</div>}
    {questions.length?questions.map((q,index)=><div className="compact-row" key={q.id}>
      <div style={{minWidth:0,flex:1}}><strong>{index+1}. {q.prompt}</strong><small>{q.question_type.replaceAll("_"," ")} · {q.points} point(s) · {q.options.length} options</small>
      {editing===q.id&&!locked&&<div className="form-grid" style={{marginTop:12}}><label className="form-field"><span>Question type</span><select value={draft.question_type} onChange={e=>setDraft({...draft,question_type:e.target.value})}><option value="single_choice">Single choice</option><option value="multiple_choice">Multiple choice</option></select></label><label className="form-field full"><span>Question prompt</span><textarea value={draft.prompt} onChange={e=>setDraft({...draft,prompt:e.target.value})}/></label><label className="form-field full"><span>Options — one per line</span><textarea value={draft.options} onChange={e=>setDraft({...draft,options:e.target.value})}/></label><label className="form-field full"><span>Correct answer{draft.question_type==="multiple_choice"?"s — separate with |":""}</span><input value={draft.correct} onChange={e=>setDraft({...draft,correct:e.target.value})} required/></label><label className="form-field"><span>Points</span><input type="number" min="1" value={draft.points} onChange={e=>setDraft({...draft,points:e.target.value})}/></label><div className="form-actions"><button className="button button-primary" type="button" disabled={busy} onClick={saveEdit}><Save size={14}/> Save</button><button className="button button-secondary" type="button" disabled={busy} onClick={()=>setEditing(null)}><X size={14}/> Cancel</button></div></div>}
      </div>
      {!locked&&<div className="page-heading-actions"><button className="button button-secondary" type="button" title="Move up" disabled={busy||index===0} onClick={()=>move(index,-1)}><ArrowUp size={14}/></button><button className="button button-secondary" type="button" title="Move down" disabled={busy||index===questions.length-1} onClick={()=>move(index,1)}><ArrowDown size={14}/></button><button className="button button-secondary" type="button" disabled={busy} onClick={()=>startEdit(q)}><Pencil size={14}/> Edit</button><button className="button button-secondary" type="button" disabled={busy} onClick={()=>remove(q.id)}><Trash2 size={14}/> Delete</button></div>}
    </div>):<div className="empty-state">No questions yet. Add the first question using the builder.</div>}
  </div>;
}

export function CloneAssessment({assessmentId}:{assessmentId:string}){
  const router=useRouter();const [busy,setBusy]=useState(false);const [error,setError]=useState("");
  async function clone(){setBusy(true);setError("");try{const response=await fetch(`/api/lms/assessments/${assessmentId}/clone`,{method:"POST"});const data=await response.json();if(!response.ok)throw new Error(data.detail||"Unable to clone assessment");router.push(`/dashboard/assessments/admin/${data.id}`)}catch(reason){setError(reason instanceof Error?reason.message:"Unable to clone assessment")}finally{setBusy(false)}}
  return <span>{error&&<span className="form-error" role="alert">{error}</span>}<button className="button button-secondary" type="button" onClick={clone} disabled={busy}>{busy?"Copying…":"Clone for revision"}</button></span>;
}
