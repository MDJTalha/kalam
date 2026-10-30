"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, Clock3, Send } from "lucide-react";

type Question={id:string;question_type:string;prompt:string;options:string[];points:number;position:number};
type Assessment={id:string;title:string;passing_score:number;max_attempts?:number|null;time_limit_minutes?:number|null;questions:Question[]};
type Result={score:number;passed:boolean;certificate_id?:string|null;attempt_id?:string;feedback?:string|null};
type Attempt={id:string;attempt_number:number;started_at:string;submitted_at?:string|null;score?:number|null;passed?:boolean|null;feedback?:string|null};

export function AssessmentRunner({assessment}:{assessment:Assessment}){
  const [answers,setAnswers]=useState<Record<string,unknown>>({});
  const [result,setResult]=useState<Result|null>(null);
  const [attemptId,setAttemptId]=useState<string|null>(null);
  const [attemptNumber,setAttemptNumber]=useState<number|null>(null);
  const [startedAt,setStartedAt]=useState<string|null>(null);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const [started,setStarted]=useState(false);
  const [history,setHistory]=useState<Attempt[]>([]);const [remaining,setRemaining]=useState<number|null>(null);
  const [historyLoading,setHistoryLoading]=useState(true);const [historyError,setHistoryError]=useState("");const [historyRequest,setHistoryRequest]=useState(0);
  useEffect(()=>{
    const controller=new AbortController();
    fetch(`/api/lms/assessments/${assessment.id}/my-attempts`,{cache:"no-store",signal:controller.signal})
      .then(async response=>{
        const data:unknown=await response.json().catch(()=>null);
        if(!response.ok)throw new Error(data&&typeof data==="object"&&"detail" in data&&typeof data.detail==="string"?data.detail:"Unable to load attempt history.");
        if(!Array.isArray(data))throw new Error("Attempt history returned an invalid response.");
        setHistory(data as Attempt[]);setHistoryLoading(false);
      })
      .catch(error=>{
        if(!controller.signal.aborted){setHistoryError(error instanceof Error?error.message:"Unable to load attempt history.");setHistoryLoading(false);}
      })
    return()=>controller.abort();
  },[assessment.id,historyRequest]);
  useEffect(()=>{if(!startedAt||!assessment.time_limit_minutes||result)return;const update=()=>setRemaining(Math.max(0,Math.ceil((new Date(startedAt).getTime()+assessment.time_limit_minutes!*60000-Date.now())/1000)));const timer=window.setInterval(update,1000);update();return()=>window.clearInterval(timer)},[startedAt,assessment.time_limit_minutes,result]);
  const answeredCount=useMemo(()=>assessment.questions.filter(q=>{
    const answer=answers[q.id];
    return Array.isArray(answer)?answer.length>0:typeof answer==="string"&&answer.length>0;
  }).length,[answers,assessment.questions]);
  const unanswered=Math.max(assessment.questions.length-answeredCount,0);
  const pending=history.find(item=>!item.submitted_at);
  const remainingAttempts=assessment.max_attempts===null||assessment.max_attempts===undefined?null:Math.max(0,assessment.max_attempts-history.length);

  function retryHistory(){
    setHistoryLoading(true);setHistoryError("");setHistoryRequest(value=>value+1);
  }

  function setSingle(id:string,value:string){setAnswers(current=>{const next={...current,[id]:value};if(attemptId)localStorage.setItem(`assessment-answers-${attemptId}`,JSON.stringify(next));return next});}
  function setMultiple(id:string,value:string,checked:boolean){
    setAnswers(state=>{
      const current=Array.isArray(state[id])?state[id] as string[]:[];
      const next=checked?[...new Set([...current,value])]:current.filter(item=>item!==value);
      const updated={...state,[id]:next};
      if(attemptId)localStorage.setItem(`assessment-answers-${attemptId}`,JSON.stringify(updated));
      return updated;
    });
  }

  async function start(){
    setBusy(true);setError("");
    try{
      const response=await fetch("/api/lms/assessments/"+assessment.id+"/start",{method:"POST",credentials:"include"});
      const data=await response.json().catch(()=>({}));
      if(!response.ok)throw new Error(data.detail||"Unable to start assessment");
      setAttemptId(data.attempt_id);setAttemptNumber(data.attempt_number);setStartedAt(data.started_at);setStarted(true);
      try{const saved=localStorage.getItem(`assessment-answers-${data.attempt_id}`);setAnswers(saved?JSON.parse(saved):{})}catch{setAnswers({})}
    }catch(error){setError(error instanceof Error?error.message:"Unable to start assessment")}
    finally{setBusy(false)}
  }
  async function submit(event:FormEvent){
    event.preventDefault();
    if(!attemptId)return;
    if(remaining!==0&&unanswered>0&&!window.confirm("You have "+unanswered+" unanswered question(s). Submit anyway?"))return;
    setBusy(true);setError("");
    try{
      const response=await fetch("/api/lms/assessments/"+assessment.id+"/submit",{
        method:"POST",headers:{"Content-Type":"application/json"},credentials:"include",
        body:JSON.stringify({attempt_id:attemptId,answers})
      });
      const data=await response.json().catch(()=>({}));
      if(!response.ok)throw new Error(data.detail||"Submission failed");
      setResult(data);localStorage.removeItem(`assessment-answers-${attemptId}`);
      setHistory(current=>[{id:attemptId,attempt_number:attemptNumber??current.length+1,started_at:startedAt??new Date().toISOString(),submitted_at:new Date().toISOString(),score:data.score,passed:data.passed,feedback:data.feedback},...current.filter(item=>item.id!==attemptId)]);
    }catch(error){setError(error instanceof Error?error.message:"Submission failed")}
    finally{setBusy(false)}
  }

  return <section className="data-panel assessment-player" aria-labelledby="assessment-player-title">
    <div className="assessment-player-header">
      <div><span className="eyebrow">Assessment player</span><h2 id="assessment-player-title">{assessment.title}</h2><p>Pass threshold {assessment.passing_score}%{assessment.max_attempts?" · Maximum "+assessment.max_attempts+" attempt"+(assessment.max_attempts===1?"":"s"):""}{assessment.time_limit_minutes?" · "+assessment.time_limit_minutes+" minute limit":""}</p></div>
      <div className="assessment-player-status"><span className="status-badge warning">Pass {assessment.passing_score}%</span>{attemptNumber&&<span className="status-badge muted">Attempt {attemptNumber}</span>}</div>
    </div>
    {error&&<div className="form-error" role="alert" aria-live="assertive"><AlertCircle size={15}/>{error}</div>}
    {result?<div className={result.passed?"assessment-result assessment-result-success":"assessment-result assessment-result-failure"} role="status">{result.passed?<CheckCircle2 size={42}/>:<AlertCircle size={42}/>}<span className="eyebrow">{result.passed?"Completed":"Review required"}</span><h2>{result.passed?"Assessment passed":"Assessment not passed"}</h2><strong>{result.score}%</strong><p>{result.feedback||(result.passed?(result.certificate_id?"Your result is recorded and a credential was issued where applicable.":"Your score met the required threshold."):"Review the learning material and use another permitted attempt.")}</p></div>:
    !started?<div className="assessment-start">
      <div className="assessment-start-icon"><Clock3 size={24}/></div>
      <div><h3>Ready to begin?</h3><p>The attempt starts when you select Begin assessment. Any configured time limit is measured from that point.</p><div className="assessment-start-meta"><span>{assessment.questions.length} questions</span><span>{assessment.max_attempts?`${remainingAttempts} of ${assessment.max_attempts} attempts remaining`:"Unlimited attempts"}</span>{assessment.time_limit_minutes&&<span>{assessment.time_limit_minutes} minutes</span>}</div></div>
      <button className="button button-primary button-large" type="button" onClick={()=>void start()} disabled={busy||historyLoading||Boolean(historyError)||!assessment.questions.length||(!pending&&remainingAttempts===0)}>{busy?"Starting…":historyLoading?"Checking attempts…":pending?"Resume attempt":remainingAttempts===0?"No attempts remaining":"Begin assessment"}</button>
    </div>:
    <form className="assessment-form" onSubmit={submit}>
      {remaining!==null&&<div className={remaining===0?"form-error":"status-pill"} role="timer" aria-live="off"><Clock3 size={15}/>{remaining===0?"Time expired. Submit to record this attempt.":`Time remaining: ${Math.floor(remaining/60)}:${String(remaining%60).padStart(2,"0")}`}</div>}
      <div className="assessment-progress-strip" aria-label={answeredCount+" of "+assessment.questions.length+" questions answered"}><div><strong>{answeredCount} of {assessment.questions.length}</strong><span>answered</span></div><div className="assessment-progress"><span style={{width:(assessment.questions.length?answeredCount/assessment.questions.length*100:0)+"%"}}/></div><small>{unanswered?unanswered+" unanswered":"All questions answered"}{startedAt?" · Started "+new Date(startedAt).toLocaleTimeString():""}</small></div>
      {assessment.questions.map((question,index)=><fieldset className="question-card" key={question.id} aria-describedby={"question-"+question.id+"-meta"}>
        <legend><span>{index+1}</span>{question.prompt}</legend>
        <small id={"question-"+question.id+"-meta"}>{question.points} point{question.points===1?"":"s"} · {question.question_type==="multiple_choice"?"Select all that apply":"Select one"}</small>
        <div className="option-list">
          {question.options.map(option=>question.question_type==="multiple_choice"?
            <label key={option}><input type="checkbox" checked={Array.isArray(answers[question.id])&&(answers[question.id] as string[]).includes(option)} onChange={event=>setMultiple(question.id,option,event.target.checked)}/><span>{option}</span></label>:
            <label key={option}><input type="radio" name={question.id} checked={answers[question.id]===option} onChange={()=>setSingle(question.id,option)}/><span>{option}</span></label>
          )}
        </div>
      </fieldset>)}
      <div className="assessment-submit-bar"><div><strong>Ready to submit?</strong><small>{unanswered?unanswered+" question(s) remain unanswered.":"All questions have an answer."}</small></div><button className="button button-primary button-large" type="submit" disabled={busy}><Send size={16}/>{busy?"Submitting…":remaining===0?"Record expired attempt":"Submit assessment"}</button></div>
    </form>}
    {historyError&&<div className="form-error" role="alert"><span>Previous attempts could not be checked, so a new attempt cannot be started safely. {historyError}</span><button className="button button-secondary" type="button" onClick={retryHistory} disabled={historyLoading}>{historyLoading?"Checking…":"Retry"}</button></div>}
    {historyLoading&&!started&&<p className="section-meta" role="status">Checking your previous attempts…</p>}
    {!!history.length&&<div className="compact-list" aria-label="My attempt history"><h3>My attempts</h3>{history.map(item=><div className="compact-row" key={item.id}><div><strong>Attempt {item.attempt_number}</strong><small>{item.submitted_at?new Date(item.submitted_at).toLocaleDateString():"In progress"} · {item.score===null||item.score===undefined?"Awaiting submission":`${item.score}%`}</small></div><span className={`status-badge ${item.submitted_at?(item.passed?"success":"warning"):"muted"}`}>{item.submitted_at?(item.passed?"Passed":"Not passed"):"In progress"}</span></div>)}</div>}
  </section>;
}
