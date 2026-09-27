"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Loader2, CheckCircle2 } from "lucide-react";

export function CourseCreateForm(){
  const router = useRouter();
  const [values,setValues]=useState({title:"",slug:"",estimated_minutes:"",description:""});
  const [busy,setBusy]=useState(false);const [error,setError]=useState("");const [message,setMessage]=useState("");
  function update(name:string,value:string){setValues(v=>({...v,[name]:value}));}
  async function submit(e:FormEvent){e.preventDefault();setBusy(true);setError("");setMessage("");
    try{const response=await fetch("/api/lms/courses",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...values,estimated_minutes:values.estimated_minutes?Number(values.estimated_minutes):null})});
      const data=await response.json().catch(()=>({}));if(!response.ok)throw new Error(data.detail||"Course creation failed");
      setMessage("Course created as a draft. Opening the authoring workspace…");router.push("/dashboard/course-studio/"+data.id);
    }catch(err){setError(err instanceof Error?err.message:"Course creation failed");setBusy(false)}
  }
  return <form className="resource-form" onSubmit={submit}>
    <div className="section-heading compact"><div><span className="eyebrow">Workspace action</span><h2>Create a learning course</h2><p>Start with the core learning object. The studio will take you through curriculum and content next.</p></div></div>
    <div className="form-grid">
      <label className="form-field"><span>Course title</span><input required value={values.title} placeholder="e.g. Workplace Ethics & Responsible Conduct" onChange={e=>update("title",e.target.value)}/></label>
      <label className="form-field"><span>URL slug</span><input required value={values.slug} placeholder="workplace-ethics" onChange={e=>update("slug",e.target.value.toLowerCase().replace(/[^a-z0-9-]/g,"-"))}/></label>
      <label className="form-field"><span>Duration (minutes)</span><input type="number" min={1} value={values.estimated_minutes} placeholder="45" onChange={e=>update("estimated_minutes",e.target.value)}/></label>
      <label className="form-field full"><span>Description</span><textarea value={values.description} placeholder="What will employees learn?" onChange={e=>update("description",e.target.value)}/></label>
    </div>
    {error&&<div className="form-error" role="alert">{error}</div>}
    {message&&<div className="form-success" role="status"><CheckCircle2 size={14}/> {message}</div>}
    <div className="form-actions"><button className="button button-primary" disabled={busy}>{busy?<><Loader2 size={15}/> Creating…</>:<>Create course <ArrowRight size={15}/></>}</button></div>
  </form>;
}
