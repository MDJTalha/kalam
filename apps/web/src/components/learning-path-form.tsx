"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Save } from "lucide-react";
import { Notice, SectionCard } from "./ui";

export function LearningPathForm(){
  const router = useRouter();
  const [title,setTitle]=useState("");const [slug,setSlug]=useState("");const [description,setDescription]=useState("");const [busy,setBusy]=useState(false);const [slugEdited,setSlugEdited]=useState(false);const [message,setMessage]=useState<string|null>(null);
  async function submit(e:FormEvent){e.preventDefault();setBusy(true);setMessage(null);try{const r=await fetch("/api/lms/programs/paths",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({title,slug,description})});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Unable to create path");router.push("/dashboard/learning-paths/"+d.id);}catch(err){setMessage(err instanceof Error?err.message:"Unable to create path")}finally{setBusy(false)}}
  return <SectionCard eyebrow="Path builder" title="Create a structured learning journey"><form className="studio-form" onSubmit={submit}><div className="form-grid"><label>Path title<input required minLength={3} value={title} onChange={e=>{setTitle(e.target.value);if(!slugEdited)setSlug(e.target.value.toLowerCase().trim().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,""))}}/></label><label>Slug<input required minLength={3} pattern="[a-z0-9]+(-[a-z0-9]+)*" value={slug} onChange={e=>{setSlugEdited(true);setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g,"-"))}}/></label><label className="full-span">Description<textarea rows={5} value={description} onChange={e=>setDescription(e.target.value)}/></label></div>{message&&<Notice kind="error">{message}</Notice>}<button className="button button-primary" disabled={busy}><Save size={15}/>{busy?"Saving…":"Create learning path"}</button></form></SectionCard>;
}