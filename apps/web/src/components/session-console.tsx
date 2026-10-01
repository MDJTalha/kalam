"use client";
import { FormEvent, useState } from "react";
import { CalendarPlus } from "lucide-react";
import { Notice, SectionCard } from "./ui";

type Course={id:string;title:string};
export function SessionConsole({courses}:{courses:Course[]}){
  const [courseId,setCourseId]=useState(courses[0]?.id||"");
  const [title,setTitle]=useState("");
  const [starts,setStarts]=useState("");
  const [ends,setEnds]=useState("");
  const [location,setLocation]=useState("");
  const [message,setMessage]=useState<string|null>(null);
  const [busy,setBusy]=useState(false);
  async function submit(e:FormEvent){
    e.preventDefault();
    setBusy(true);
    setMessage(null);
    try{
      if (!starts || !ends) throw new Error("Start and end time are required.");
      const startsAt = new Date(starts);
      const endsAt = new Date(ends);
      if (Number.isNaN(startsAt.getTime()) || Number.isNaN(endsAt.getTime())) throw new Error("Enter valid session times.");
      if (endsAt <= startsAt) throw new Error("End time must be later than start time.");
      if (!courseId) throw new Error("Select a course before creating the session.");
      const r=await fetch("/api/lms/sessions",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({course_id:courseId,title,starts_at:startsAt.toISOString(),ends_at:endsAt.toISOString(),location})});
      const d=await r.json();if(!r.ok)throw new Error(d.detail||"Unable to create session");
      setMessage("Session created successfully.");setTitle("");
    }catch(err){setMessage(err instanceof Error?err.message:"Unable to create session")}
    finally{setBusy(false)}
  }
  return <SectionCard eyebrow="Live learning administration" title="Schedule a session">
    <form className="studio-form" onSubmit={submit}>
      <div className="form-grid">
        <label>Course<select value={courseId} onChange={e=>setCourseId(e.target.value)} required>{courses.map(c=><option value={c.id} key={c.id}>{c.title}</option>)}</select></label>
        <label>Session title<input value={title} onChange={e=>setTitle(e.target.value)} required/></label>
        <label>Starts<input type="datetime-local" value={starts} onChange={e=>setStarts(e.target.value)} required/></label>
        <label>Ends<input type="datetime-local" value={ends} onChange={e=>setEnds(e.target.value)} required/></label>
        <label className="full-span">Location / delivery channel<input value={location} onChange={e=>setLocation(e.target.value)} placeholder="Room, Teams, Zoom, etc."/></label>
      </div>
      {message&&<Notice kind={message.startsWith("Session")?"success":"error"}>{message}</Notice>}
      <button className="button button-primary" disabled={busy}><CalendarPlus size={15}/>{busy?"Saving…":"Create session"}</button>
    </form>
  </SectionCard>;
}