"use client";

import Image from "next/image";
import { useMemo, useState } from "react";
import { CheckCircle2, Circle, ExternalLink, FileText, Image as ImageIcon, Link2, LogIn, PlayCircle, Video } from "lucide-react";

type Block = {
  id?: string;
  type: string;
  text?: string;
  level?: 2 | 3 | 4;
  variant?: "info" | "success" | "warning" | "important";
  url?: string;
  file_id?: string;
  alt?: string;
  caption?: string;
};
type Lesson = { id:string; title:string; content_type:string; content:Record<string,unknown>; position:number };
type Course = { id:string; title:string; description?:string|null; estimated_minutes?:number|null; enrollment_policy?:string; modules:Array<{id:string;title:string;lessons:Lesson[]}>; enrollment?:{id:string;status:string}|null; completed_lesson_ids?:string[]; progress_percent?:number };

function inlineText(value: string) {
  const parts = value.split(/(\*\*[^*]+\*\*|\*[^*]+\*|https?:\/\/[^\s]+)/g);
  return parts.map((part, index) => {
    if (/^\*\*[^*]+\*\*$/.test(part)) return <strong key={index}>{part.slice(2,-2)}</strong>;
    if (/^\*[^*]+\*$/.test(part)) return <em key={index}>{part.slice(1,-1)}</em>;
    if (/^https?:\/\//.test(part)) return <a key={index} className="text-link" href={part} target="_blank" rel="noreferrer">{part}<ExternalLink size={12}/></a>;
    return <span key={index}>{part}</span>;
  });
}
function fileUrl(fileId?: string, url?: string) {
  return fileId ? "/api/lms/files/" + fileId + "/download" : url || "";
}
function renderBlocks(content: Record<string, unknown>) {
  const blocks = Array.isArray(content.blocks) ? content.blocks as Block[] : [];
  if (!blocks.length && typeof content.body === "string") {
    return content.body.split(/\n\n+/).map((paragraph, index) => <p key={index}>{inlineText(paragraph)}</p>);
  }
  return blocks.map((block, index) => {
    const key = block.id || "block-" + index;
    const lines = (block.text || "").split("\n").map((item) => item.trim()).filter(Boolean);
    if (block.type === "heading") {
      const Tag = block.level === 4 ? "h5" : block.level === 3 ? "h4" : "h3";
      return <Tag key={key}>{inlineText(block.text || "")}</Tag>;
    }
    if (block.type === "paragraph") return <p key={key}>{inlineText(block.text || "")}</p>;
    if (block.type === "bullets") return <ul key={key}>{lines.map((item, itemIndex) => <li key={itemIndex}>{inlineText(item)}</li>)}</ul>;
    if (block.type === "numbered") return <ol key={key}>{lines.map((item, itemIndex) => <li key={itemIndex}>{inlineText(item)}</li>)}</ol>;
    if (block.type === "callout") return <aside key={key} className={"lesson-callout " + (block.variant || "info")}><strong>{block.variant === "important" ? "Important" : block.variant === "warning" ? "Attention" : block.variant === "success" ? "Good to know" : "Information"}</strong><p>{inlineText(block.text || "")}</p></aside>;
    if (block.type === "image") {
      const src = fileUrl(block.file_id, block.url);
      return <figure key={key} className="lesson-media"><ImageIcon size={18}/>{src ? <Image src={src} alt={block.alt || ""} width={1200} height={675} unoptimized /> : <div className="media-missing">Image not configured.</div>}{block.caption ? <figcaption>{block.caption}</figcaption> : null}</figure>;
    }
    return null;
  });
}
function renderResource(block: Block) {
  if (block.type === "video") {
    return <div className="lesson-resource lesson-resource-video"><Video size={24}/><strong>Video learning resource</strong>{block.text ? <p>{block.text}</p> : null}{block.url ? <a className="button button-secondary" href={block.url} target="_blank" rel="noreferrer">Open video <ExternalLink size={13}/></a> : <span>Video resource not configured.</span>}</div>;
  }
  if (block.type === "file") {
    const href = fileUrl(block.file_id, block.url);
    return <div className="lesson-file-card"><FileText size={20}/><div><strong>{block.alt || "Learning document"}</strong><small>Governed learning resource</small></div>{href ? <a className="button button-secondary" href={href} target="_blank" rel="noreferrer">Open <ExternalLink size={13}/></a> : <span className="status-badge muted">Not configured</span>}</div>;
  }
  return <div className="lesson-link-card"><Link2 size={18}/><div><strong>{block.text || "Learning resource"}</strong><small>{block.url || "URL not configured"}</small></div>{block.url ? <a className="button button-secondary" href={block.url} target="_blank" rel="noreferrer">Open <ExternalLink size={13}/></a> : null}</div>;
}

export function CoursePlayer({course,canManage=false}:{course:Course;canManage?:boolean}) {
  const [enrollmentId,setEnrollmentId]=useState(course.enrollment?.id??null);
  const [status,setStatus]=useState(course.enrollment?.status??"not_enrolled");
  const [completedLessons,setCompletedLessons]=useState<string[]>(course.completed_lesson_ids??[]);
  const [selectedId,setSelectedId]=useState<string|null>(course.modules[0]?.lessons[0]?.id??null);
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState("");
  const [isError,setIsError]=useState(false);
  const lessons=useMemo(()=>course.modules.flatMap(module=>module.lessons.map(lesson=>({...lesson,moduleTitle:module.title}))),[course.modules]);
  const selected=lessons.find(item=>item.id===selectedId)??lessons[0];
  const progress=lessons.length?Math.round(completedLessons.length/lessons.length*100):0;
  const learningActive=["enrolled","in_progress","completed"].includes(status);
  const canViewContent=learningActive||canManage;
  const assignmentOnly=course.enrollment_policy==="assignment_only";
  const enrollmentActionable=!assignmentOnly&&(status==="not_enrolled"||status==="rejected");
  const statusLabel:Record<string,string>={pending_approval:"Pending approval",waitlisted:"Waitlisted",rejected:"Request rejected",enrolled:"Enrolled",in_progress:"In progress",completed:"Completed"};

  async function enroll(){
    setBusy(true);setMessage("");setIsError(false);
    try{
      const response=await fetch("/api/lms/courses/"+course.id+"/enroll",{method:"POST",credentials:"include"});
      const data=await response.json();
      if(!response.ok)throw new Error(data.detail||"Enrollment failed");
      setEnrollmentId(data.id);setStatus(data.status);
      setMessage(data.status==="pending_approval"?"Enrollment request submitted for approval.":data.status==="waitlisted"?"You have joined the waitlist.":"Enrollment confirmed. Your learning record is now active.");
    }catch(error){setIsError(true);setMessage(error instanceof Error?error.message:"Enrollment failed");}
    finally{setBusy(false);}
  }
  async function complete(lessonId:string){
    if(!enrollmentId)return;
    setBusy(true);setMessage("");setIsError(false);
    try{
      const response=await fetch("/api/lms/courses/my/enrollments/"+enrollmentId+"/lessons/"+lessonId+"/complete",{method:"POST",credentials:"include"});
      const data=await response.json();
      if(!response.ok)throw new Error(data.detail||"Unable to save progress");
      setCompletedLessons(items=>items.includes(lessonId)?items:[...items,lessonId]);
      setStatus(data.course_status||data.status||status);
      setMessage(data.status==="completed"?"Course completed. Your learning record and mapped skill evidence are now updated.":"Lesson completion saved.");
    }catch(error){setIsError(true);setMessage(error instanceof Error?error.message:"Unable to save progress");}
    finally{setBusy(false);}
  }

  return <section className="data-panel learner-player" aria-labelledby="learner-player-title">
    <div className="player-toolbar"><div><span className="eyebrow">Learner player</span><h2 id="learner-player-title">{assignmentOnly&&status==="not_enrolled"?"Assignment required":enrollmentActionable?"Start this course":"Continue learning"}</h2></div>{enrollmentActionable?<button className="button button-primary" onClick={enroll} disabled={busy}><LogIn size={15}/>{busy?(status==="rejected"?"Requesting…":"Enrolling…"):(status==="rejected"?"Request again":"Enroll now")}</button>:<span className={learningActive?"status-badge success":"status-badge"}>{assignmentOnly&&status==="not_enrolled"?"Assignment required":statusLabel[status]??status}</span>}</div>
    {message&&<div className={isError?"form-error":"form-success"} role={isError?"alert":"status"} aria-live="polite">{message}</div>}
    <div className="progress-summary" aria-label={"Course progress "+progress+"%"}><div><strong>Course progress</strong><span>{progress}%</span></div><div className="progress-bar" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress} aria-label="Course completion"><span style={{width:progress+"%"}}/></div></div>
    <div className="player-layout">
      <nav className="lesson-index" aria-label="Course lessons">
        {course.modules.map(module=><section key={module.id}><div className="eyebrow">{module.title}</div><div className="compact-list">{module.lessons.map(lesson=>{const done=completedLessons.includes(lesson.id);return <button className={"lesson-nav-row "+(selected?.id===lesson.id?"selected":"")} key={lesson.id} onClick={()=>setSelectedId(lesson.id)} aria-current={selected?.id===lesson.id?"step":undefined} aria-label={lesson.title+(done?", completed":"")}><span>{done?<CheckCircle2 size={15}/>:<Circle size={15}/>}</span><div><strong>{lesson.title}</strong><small>{lesson.content_type}</small></div></button>})}</div></section>)}
      </nav>
      <main className="lesson-content" aria-live="polite">
        {selected?<><div className="lesson-content-header"><span className="tag">{selected.moduleTitle}</span><h3>{selected.title}</h3></div>
          {canViewContent ? <div className="lesson-blocks">
            {selected.content_type==="rich_text" ? renderBlocks(selected.content)
              : selected.content_type==="video" ? renderResource({type:"video",url:typeof selected.content.url==="string"?selected.content.url:undefined,text:typeof selected.content.body==="string"?selected.content.body:undefined})
              : selected.content_type==="document" ? renderResource({type:"file",url:typeof selected.content.url==="string"?selected.content.url:undefined,alt:"Learning document"})
              : renderResource({type:"link",url:typeof selected.content.url==="string"?selected.content.url:undefined,text:"Open learning resource"})}
          </div> : <p className="form-help">Lesson content is available after enrollment or assignment approval.</p>}
          <div className="lesson-footer">
            {completedLessons.includes(selected.id)?<span className="status-badge success"><CheckCircle2 size={13}/> Completed</span>
              :learningActive?<button className="button button-primary" onClick={()=>void complete(selected.id)} disabled={busy}><PlayCircle size={15}/>{busy?"Saving…":"Mark lesson complete"}</button>
              :status==="pending_approval"?<span className="status-badge muted">Awaiting L&amp;D approval before learning access.</span>
              :status==="waitlisted"?<span className="status-badge muted">You are on the course waitlist.</span>
              :status==="rejected"?<span className="status-badge muted">Your request was rejected. Submit a new request to rejoin the approval flow.</span>
              :<span className="status-badge muted">{assignmentOnly?"A manager or L&D administrator must assign this course.":"Enroll to continue"}</span>}
          </div>
        </>:<div className="empty-state"><p>This course has no lessons yet.</p></div>}
      </main>
    </div>
  </section>;
}
