"use client";

import { type FormEvent, useState } from "react";
import Link from "next/link";
import { ArrowLeft, CheckCircle2, LifeBuoy, MessageSquare, Send, ShieldCheck } from "lucide-react";

export type SupportCaseDetail={id:string;case_number:string;category:string;severity:string;subject:string;description:string;route?:string|null;status:string;created_at:string;updated_at:string;resolved_at?:string|null;assignee?:{id:string;name:string;email:string}|null};
export type SupportCaseMessage={id:string;body:string;visibility:string;created_at:string;author:{id:string;name:string}};

export function SupportCaseConversation({supportCase,initialMessages}:{supportCase:SupportCaseDetail;initialMessages:SupportCaseMessage[]}){
  const [messages,setMessages]=useState(initialMessages);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");

  async function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault(); if(busy)return;
    const form=event.currentTarget; const data=new FormData(form); const body=String(data.get("body")||"").trim();
    if(body.length<2)return;
    setBusy(true);setError("");
    try{
      const response=await fetch("/api/lms/support/cases/"+supportCase.id+"/messages",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({body})});
      if(!response.ok){const payload=await response.json().catch(()=>({}));throw new Error(typeof payload.detail==="string"?payload.detail:"Reply could not be sent.")}
      const refresh=await fetch("/api/lms/support/cases/"+supportCase.id+"/messages",{cache:"no-store"});
      if(refresh.ok)setMessages(await refresh.json());
      form.reset();
    }catch(cause){setError(cause instanceof Error?cause.message:"Reply could not be sent.")}finally{setBusy(false)}
  }

  return <div className="support-case-detail">
    <Link className="text-link" href="/dashboard/help"><ArrowLeft size={14}/> Back to Help & Support</Link>
    <section className="support-case-summary">
      <div><span className={"help-severity "+supportCase.severity}>{supportCase.severity}</span><h2>{supportCase.subject}</h2><p>{supportCase.case_number} · {supportCase.category} · opened {new Date(supportCase.created_at).toLocaleString()}</p></div>
      <span className={"status-badge "+(["resolved","closed"].includes(supportCase.status)?"success":"warning")}>{supportCase.status.replace("_"," ")}</span>
    </section>
    <section className="support-case-detail-grid">
      <article><span>Issue description</span><p>{supportCase.description}</p></article>
      <article><span>Support owner</span><strong>{supportCase.assignee?.name||"Not yet assigned"}</strong><small>{supportCase.assignee?"Your case is assigned to a support owner.":"The support queue has not assigned an owner yet."}</small></article>
      <article><span>Source route</span><strong>{supportCase.route||"Not captured"}</strong><small>Context captured when the case was created.</small></article>
    </section>
    <section className="support-conversation">
      <div className="help-section-heading"><div><span className="eyebrow">Conversation</span><h2>Case updates</h2><p>Requester-visible replies appear here. Internal support notes are never shown on this screen.</p></div><MessageSquare size={20}/></div>
      <div className="support-thread-list requester-thread">{messages.length?messages.map(message=><article className="support-message requester" key={message.id}><div><strong>{message.author.name}</strong><span>{new Date(message.created_at).toLocaleString()}</span></div><p>{message.body}</p></article>):<div className="help-empty">No conversation updates yet.</div>}</div>
      {!["closed"].includes(supportCase.status)&&<form className="support-requester-reply" onSubmit={submit}><label><span>Add information or reply</span><textarea name="body" minLength={2} maxLength={4000} rows={5} required placeholder="Add relevant context or answer a support question. Do not include passwords, session tokens, API secrets or unnecessary personal data."/></label><div><button className="button button-primary" type="submit" disabled={busy}><Send size={15}/>{busy?"Sending…":"Send reply"}</button><span><ShieldCheck size={14}/> Replies are visible to your organization&apos;s authorized support administrators.</span></div>{error&&<div className="form-error" role="alert">{error}</div>}</form>}
      {supportCase.status==="closed"&&<div className="help-privacy-note"><CheckCircle2 size={17}/><div><strong>This case is closed.</strong><p>Create a new support case if a separate issue needs attention.</p></div></div>}
    </section>
    <section className="help-boundary"><LifeBuoy size={18}/><div><strong>Need a separate case?</strong><p>Return to Help & Support to open a new case rather than mixing unrelated issues into this conversation.</p></div></section>
  </div>;
}
