"use client";

import { useMemo, useState } from "react";
import { CheckCircle2, ClipboardCheck, Plus, RefreshCcw, Save, Target } from "lucide-react";
import { PeopleLookupSelect } from "@/components/people-lookup-select";

type Assessment={id:string;title:string;assessment_type:string;measurement_method:string;validity_days:number|null;reassessment_interval_days:number|null};
type Person={id:string;first_name:string;last_name:string;email:string;job_title?:string|null};
type Candidate={id:string;type:string;name:string;code?:string};
type Target={id:string;assessment_id:string;target_type:string;target_id:string;target_name:string|null;target_level:number;weight:number};
type Cycle={id:string;assessment_id:string;assessment_title:string;assessment_type:string;user_id:string;target_type:string;target_id:string;required_level:number;baseline_level:number|null;current_level:number|null;gap:number|null;improvement:number|null;status:string;next_reassessment_due_at:string|null;development_plan_id:string|null};
type Attempt={id:string;cycle_id:string;stage:string;assessment_id:string};
type Props={assessments:Assessment[];initialAssessmentId:string;people:Person[];candidates:Candidate[];initialTargets:Target[];initialCycles:Cycle[];canManage:boolean;currentUserId:string};

const levelName=(n:number)=>({1:"Foundational",2:"Developing",3:"Proficient",4:"Advanced",5:"Expert"} as Record<number,string>)[n]||"Level";
const personName=(p?:Person)=>p ? ((p.first_name+" "+p.last_name).trim()||p.email) : "Unknown person";

export function CapabilityAssessmentWorkspace({assessments,initialAssessmentId,people,candidates,initialTargets,initialCycles,canManage,currentUserId}:Props){
  const initialAssessment=assessments.find(item=>item.id===initialAssessmentId)||assessments[0];
  const [assessmentId,setAssessmentId]=useState(initialAssessment?.id||"");
  const [candidateKey,setCandidateKey]=useState("");
  const [targetLevel,setTargetLevel]=useState("3");
  const [targetWeight,setTargetWeight]=useState("1");
  const [assessmentType,setAssessmentType]=useState(initialAssessment?.assessment_type||"knowledge_test");
  const [measurementMethod,setMeasurementMethod]=useState(initialAssessment?.measurement_method||"score_based");
  const [validityDays,setValidityDays]=useState(String(initialAssessment?.validity_days||30));
  const [reassessmentDays,setReassessmentDays]=useState(String(initialAssessment?.reassessment_interval_days||90));
  const [personId,setPersonId]=useState(people[0]?.id||currentUserId);
  const [cycleTargetId,setCycleTargetId]=useState(initialTargets[0]?.id||"");
  const [targets,setTargets]=useState(initialTargets);
  const [cycles,setCycles]=useState(initialCycles);
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState("");
  const [error,setError]=useState("");
  const [attempt,setAttempt]=useState<Attempt|null>(null);
  const [attemptTargets,setAttemptTargets]=useState<Target[]>([]);
  const [outcomes,setOutcomes]=useState<Record<string,{level:string;confidence:string}>>({});

  const mappedTargets=useMemo(()=>targets.filter(x=>x.assessment_id===assessmentId),[targets,assessmentId]);
  const personMap=useMemo(()=>new Map(people.map(p=>[p.id,p])),[people]);

  function selectAssessment(id:string){
    const next=assessments.find(x=>x.id===id);
    if(!next)return;
    setAssessmentId(id);
    setAssessmentType(next.assessment_type||"knowledge_test");
    setMeasurementMethod(next.measurement_method||"score_based");
    setValidityDays(String(next.validity_days||30));
    setReassessmentDays(String(next.reassessment_interval_days||90));
    setCandidateKey("");
    void refreshTargets(id);
  }

  async function refreshTargets(id=assessmentId){
    const r=await fetch("/api/v1/capability-assessments/assessments/"+id+"/targets",{cache:"no-store"});
    const d=await r.json().catch(()=>[]);
    if(r.ok){
      const next=Array.isArray(d)?d:[];
      setTargets(next);
      setCycleTargetId(next[0]?.id||"");
    }
  }

  async function refreshCycles(id=personId){
    const r=await fetch("/api/v1/capability-assessments/cycles?user_id="+encodeURIComponent(id),{cache:"no-store"});
    const d=await r.json().catch(()=>[]);
    if(r.ok)setCycles(Array.isArray(d)?d:[]);
  }

  async function saveInstrumentSettings(){
    if(!assessmentId)return;
    setBusy(true);setError("");setMessage("");
    try{
      const r=await fetch("/api/v1/assessments/"+assessmentId,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({
        assessment_type:assessmentType,measurement_method:measurementMethod,
        validity_days:Number(validityDays),reassessment_interval_days:Number(reassessmentDays),
      })});
      const d=await r.json().catch(()=>({}));
      if(!r.ok)throw new Error(d.detail||"Assessment settings could not be saved.");
      setMessage("Assessment measurement settings saved and audited.");
    }catch(e){setError(e instanceof Error?e.message:"Instrument update failed.");}finally{setBusy(false)}
  }

  async function saveTarget(){
    const parts=candidateKey.split(":");
    const candidate=candidates.find(x=>x.type===parts[0]&&x.id===parts.slice(1).join(":"));
    if(!candidate||!assessmentId)return;
    setBusy(true);setError("");setMessage("");
    try{
      const r=await fetch("/api/v1/capability-assessments/assessments/"+assessmentId+"/targets",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({target_type:candidate.type,target_id:candidate.id,target_level:Number(targetLevel),weight:Number(targetWeight)})});
      const d=await r.json().catch(()=>({}));
      if(!r.ok)throw new Error(d.detail||"Assessment target could not be saved.");
      setMessage("Assessment measurement target saved.");
      await refreshTargets();
    }catch(e){setError(e instanceof Error?e.message:"Target mapping failed.");}finally{setBusy(false)}
  }

  async function createCycle(){
    const target=mappedTargets.find(x=>x.id===cycleTargetId)||mappedTargets[0];
    if(!assessmentId||!target||!personId){setError("Select an assessment, mapped target and person.");return}
    setBusy(true);setError("");setMessage("");
    try{
      const r=await fetch("/api/v1/capability-assessments/assessments/"+assessmentId+"/cycles",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({user_id:personId,target_type:target.target_type,target_id:target.target_id,required_level:Number(targetLevel)})});
      const d=await r.json().catch(()=>({}));
      if(!r.ok)throw new Error(d.detail||"Assessment cycle could not be created.");
      setMessage("Baseline assessment cycle created.");
      await refreshCycles(personId);
    }catch(e){setError(e instanceof Error?e.message:"Cycle creation failed.");}finally{setBusy(false)}
  }

  async function startAttempt(cycleId:string,stage:"baseline"|"reassessment"){
    setBusy(true);setError("");setMessage("");
    try{
      const r=await fetch("/api/v1/capability-assessments/cycles/"+cycleId+"/attempts?stage="+stage,{method:"POST"});
      const d=await r.json().catch(()=>({}));
      if(!r.ok)throw new Error(d.detail||"Assessment could not be started.");
      setAttempt(d);setOutcomes({});
      const cycle=cycles.find(x=>x.id===cycleId);
      if(cycle){
        const tr=await fetch("/api/v1/capability-assessments/assessments/"+cycle.assessment_id+"/targets",{cache:"no-store"});
        const td=await tr.json().catch(()=>[]);
        if(tr.ok)setAttemptTargets(Array.isArray(td)?td:[]);
      }
      setMessage((stage==="baseline"?"Baseline":"Reassessment")+" started. Record every mapped outcome.");
    }catch(e){setError(e instanceof Error?e.message:"Assessment start failed.");}finally{setBusy(false)}
  }

  async function saveOutcome(targetId:string){
    if(!attempt)return;
    const row=outcomes[targetId]||{level:"",confidence:"100"};
    if(!row.level){setError("Select a demonstrated level before saving.");return}
    setBusy(true);setError("");
    try{
      const r=await fetch("/api/v1/capability-assessments/attempts/"+attempt.id+"/outcomes",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({target_type:attemptTargets.find(x=>x.target_id===targetId)?.target_type,target_id:targetId,demonstrated_level:Number(row.level),confidence:Number(row.confidence||100)})});
      const d=await r.json().catch(()=>({}));
      if(!r.ok)throw new Error(d.detail||"Outcome could not be saved.");
      setMessage("Outcome saved at "+Number(d.demonstrated_level).toFixed(2)+"/5.");
    }catch(e){setError(e instanceof Error?e.message:"Outcome save failed.");}finally{setBusy(false)}
  }

  async function completeAttempt(){
    if(!attempt)return;
    setBusy(true);setError("");
    try{
      const r=await fetch("/api/v1/capability-assessments/attempts/"+attempt.id+"/complete",{method:"POST"});
      const d=await r.json().catch(()=>({}));
      if(!r.ok)throw new Error(d.detail||"Assessment could not be completed.");
      setMessage("Assessment completed at "+Number(d.demonstrated_level).toFixed(2)+"/5 with "+d.confidence+"% confidence.");
      setAttempt(null);setAttemptTargets([]);await refreshCycles(personId);
    }catch(e){setError(e instanceof Error?e.message:"Assessment completion failed.");}finally{setBusy(false)}
  }

  async function markDue(cycleId:string){
    setBusy(true);setError("");
    try{
      const r=await fetch("/api/v1/capability-assessments/cycles/"+cycleId+"/mark-reassessment-due",{method:"POST"});
      const d=await r.json().catch(()=>({}));
      if(!r.ok)throw new Error(d.detail||"Could not mark reassessment due.");
      setMessage("Reassessment is now due.");await refreshCycles(personId);
    }catch(e){setError(e instanceof Error?e.message:"Reassessment transition failed.");}finally{setBusy(false)}
  }
  return <div className="stack-lg">
    <section className="assessment-library-hero">
      <div><span className="eyebrow">Capability measurement</span><h2>Assess. evidence. reassess.</h2><p>Connect governed assessment instruments to demonstrated capability and measure improvement over time.</p></div>
      <div className="metric-strip"><span><b>{cycles.length}</b> cycles</span><span><b>1–5</b> governed scale</span></div>
    </section>
    {error&&<div className="form-error" role="alert">{error}</div>}
    {message&&<div className="form-success" role="status"><CheckCircle2 size={15}/>{message}</div>}

    {canManage&&<section className="data-panel">
      <div className="section-heading compact"><div><span className="eyebrow">Instrument governance</span><h2>Configure capability measurement</h2><p>Choose the assessment mode, measurement method and validity before mapping targets.</p></div></div>
      <div className="form-grid">
        <label className="form-field"><span>Assessment *</span><select value={assessmentId} onChange={e=>selectAssessment(e.target.value)}>{assessments.map(a=><option key={a.id} value={a.id}>{a.title}</option>)}</select></label>
        <label className="form-field"><span>Assessment mode *</span><select value={assessmentType} onChange={e=>setAssessmentType(e.target.value)}>{[["self","Self assessment"],["manager","Manager assessment"],["assessor","Assessor assessment"],["360","360 assessment"],["knowledge_test","Knowledge test"],["practical","Practical evaluation"],["evidence_review","Evidence review"]].map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label>
        <label className="form-field"><span>Measurement method *</span><select value={measurementMethod} onChange={e=>setMeasurementMethod(e.target.value)}>{[["score_based","Score-based"],["level_based","Level-based"],["review_based","Review-based"],["360_aggregate","360 aggregate"]].map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label>
        <label className="form-field"><span>Validity (days)</span><input type="number" min="1" max="3650" value={validityDays} onChange={e=>setValidityDays(e.target.value)}/></label>
        <label className="form-field"><span>Reassessment interval (days)</span><input type="number" min="1" max="3650" value={reassessmentDays} onChange={e=>setReassessmentDays(e.target.value)}/></label>
      </div>
      <div className="form-actions"><button className="button button-primary" disabled={busy||!assessmentId} onClick={()=>void saveInstrumentSettings()}><Save size={14}/> Save measurement settings</button></div>
      <div className="section-heading compact"><div><span className="eyebrow">Measurement targets</span><h2>Map assessment targets</h2><p>Define exactly which capability, competency or skill the assessment measures.</p></div></div>
      <div className="form-grid">
        <label className="form-field"><span>Assessment *</span><select value={assessmentId} onChange={e=>selectAssessment(e.target.value)}>{assessments.map(a=><option key={a.id} value={a.id}>{a.title} · {a.assessment_type}</option>)}</select></label>
        <label className="form-field"><span>Target *</span><select value={candidateKey} onChange={e=>setCandidateKey(e.target.value)}><option value="">Select a target</option>{candidates.map(x=><option key={x.type+":"+x.id} value={x.type+":"+x.id}>{x.name} · {x.type}</option>)}</select></label>
        <label className="form-field"><span>Required level *</span><select value={targetLevel} onChange={e=>setTargetLevel(e.target.value)}>{[1,2,3,4,5].map(x=><option key={x} value={x}>{x} · {levelName(x)}</option>)}</select></label>
        <label className="form-field"><span>Weight</span><input type="number" min="1" max="100" value={targetWeight} onChange={e=>setTargetWeight(e.target.value)}/></label>
      </div>
      <div className="form-actions"><button className="button button-primary" disabled={busy||!candidateKey} onClick={()=>void saveTarget()}><Save size={14}/>{busy?"Saving…":"Save measurement target"}</button></div>
      {mappedTargets.length>0&&<div className="table-wrap" style={{marginTop:16}}><table className="data-table"><thead><tr><th>Target</th><th>Required</th><th>Weight</th></tr></thead><tbody>{mappedTargets.map(t=><tr key={t.id}><td><strong>{t.target_name||t.target_type}</strong><small>{t.target_type}</small></td><td>{t.target_level.toFixed(2)}/5</td><td>{t.weight}</td></tr>)}</tbody></table></div>}
    </section>}

    {canManage&&<section className="data-panel">
      <div className="section-heading compact"><div><span className="eyebrow">Baseline setup</span><h2>Create assessment cycle</h2><p>Establish a required level before measuring demonstrated capability.</p></div></div>
      <div className="form-grid">
        {canManage ? <PeopleLookupSelect label="Person *" value={personId} onChange={id=>{setPersonId(id);void refreshCycles(id);}} initialPeople={people} /> : <label className="form-field"><span>Person *</span><select value={personId} onChange={e=>{setPersonId(e.target.value);void refreshCycles(e.target.value);}}>{people.map(p=><option key={p.id} value={p.id}>{personName(p)} · {p.job_title||p.email}</option>)}</select></label>}
        <label className="form-field"><span>Assessment *</span><select value={assessmentId} onChange={e=>setAssessmentId(e.target.value)}>{assessments.map(a=><option key={a.id} value={a.id}>{a.title}</option>)}</select></label>
        <label className="form-field"><span>Mapped target *</span><select value={cycleTargetId} onChange={e=>setCycleTargetId(e.target.value)}>{mappedTargets.map(t=><option key={t.id} value={t.id}>{t.target_name||t.target_type} · {t.target_level.toFixed(2)}/5</option>)}</select></label>
        <label className="form-field"><span>Required level *</span><select value={targetLevel} onChange={e=>setTargetLevel(e.target.value)}>{[1,2,3,4,5].map(x=><option key={x} value={x}>{x} · {levelName(x)}</option>)}</select></label>
      </div>
      <div className="form-actions"><button className="button button-primary" disabled={busy||!mappedTargets.length} onClick={()=>void createCycle()}><Plus size={14}/>{busy?"Creating…":"Create baseline cycle"}</button></div>
    </section>}

    <section className="data-panel">
      <div className="section-heading compact"><div><span className="eyebrow">{canManage?"Operational review":"My capability assessments"}</span><h2>Assessment cycles</h2></div><button className="button button-secondary" onClick={()=>void refreshCycles(personId)} disabled={busy}><RefreshCcw size={14}/> Refresh</button></div>
      {cycles.length?<div className="table-wrap"><table className="data-table"><thead><tr><th>Assessment</th><th>Person</th><th>Required</th><th>Baseline</th><th>Current</th><th>Improvement</th><th>Status</th><th>Action</th></tr></thead><tbody>{cycles.map(c=><tr key={c.id}><td><strong>{c.assessment_title}</strong><small>{c.assessment_type} · {c.target_type}</small></td><td>{personName(personMap.get(c.user_id))}</td><td>{c.required_level.toFixed(2)}</td><td>{c.baseline_level===null?"—":c.baseline_level.toFixed(2)}</td><td>{c.current_level===null?"—":c.current_level.toFixed(2)}</td><td>{c.improvement===null?"—":(c.improvement>0?"+":"")+c.improvement.toFixed(2)}</td><td><span className="status-badge">{c.status.replaceAll("_"," ")}</span>{c.next_reassessment_due_at&&<small>Due {new Date(c.next_reassessment_due_at).toLocaleDateString()}</small>}</td><td><div className="inline-actions">{c.status==="baseline_due"&&<button className="button button-secondary" disabled={busy} onClick={()=>void startAttempt(c.id,"baseline")}><ClipboardCheck size={14}/> Baseline</button>}{canManage&&(c.status==="completed"||c.status==="development_in_progress")&&<button className="button button-secondary" disabled={busy} onClick={()=>void markDue(c.id)}><Target size={14}/> Mark due</button>}{(c.status==="reassessment_due"||c.status==="completed"||c.status==="development_in_progress")&&<button className="button button-secondary" disabled={busy} onClick={()=>void startAttempt(c.id,"reassessment")}><RefreshCcw size={14}/> Reassess</button>}</div></td></tr>)}</tbody></table></div>:<div className="empty-state"><Target size={24}/><p>No capability assessment cycles are available for this view yet.</p></div>}
    </section>

    {attempt&&<section className="data-panel">
      <div className="section-heading compact"><div><span className="eyebrow">{attempt.stage==="baseline"?"Baseline assessment":"Reassessment"}</span><h2>Record demonstrated capability</h2><p>Level and confidence become governed evidence after completion.</p></div></div>
      {attemptTargets.map(t=>{const row=outcomes[t.target_id]||{level:"",confidence:"100"};return <div className="compact-row" key={t.id}><div><strong>{t.target_name||t.target_type}</strong><small>Target {t.target_level.toFixed(2)}/5 · Weight {t.weight}</small></div><label className="form-field"><span>Level</span><select value={row.level} onChange={e=>setOutcomes(v=>({...v,[t.target_id]:{...row,level:e.target.value}}))}><option value="">Select</option>{Array.from({length:41},(_,i)=>(1+i*0.1).toFixed(1)).map(x=><option key={x} value={x}>{x}</option>)}</select></label><label className="form-field"><span>Confidence %</span><input type="number" min="0" max="100" value={row.confidence} onChange={e=>setOutcomes(v=>({...v,[t.target_id]:{...row,confidence:e.target.value}}))}/></label><button className="button button-secondary" disabled={busy} onClick={()=>void saveOutcome(t.target_id)}><Save size={14}/></button></div>})}
      <div className="form-actions"><button className="button button-primary" disabled={busy||!attemptTargets.length} onClick={()=>void completeAttempt()}><CheckCircle2 size={14}/>{busy?"Completing…":"Complete assessment"}</button></div>
    </section>}
  </div>
}
