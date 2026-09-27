"use client";
import { FormEvent, useState } from "react";
import { Network, Save, Webhook } from "lucide-react";
import { Notice, SectionCard, StatusBadge } from "./ui";

type Integration={id:string;provider:string;status:string;config:Record<string,unknown>};
type Hook={id:string;url:string;event_types:string[];active:boolean;created_at:string};
const providers=["hris","oidc","saml","email","calendar","lti","xapi","scorm","cmi5"];

export function IntegrationConsole({initial,webhooks}:{initial:Integration[];webhooks:Hook[]}){
  const [items,setItems]=useState(initial);const [provider,setProvider]=useState("hris");const [config,setConfig]=useState("{}");
  const [hookUrl,setHookUrl]=useState("");const [events,setEvents]=useState("course.completed,assessment.passed");
  const [message,setMessage]=useState<string|null>(null);const [busy,setBusy]=useState(false);
  async function save(e:FormEvent){
    e.preventDefault();setBusy(true);setMessage(null);
    try{
      let parsed={};try{parsed=JSON.parse(config)}catch{throw new Error("Integration configuration must be valid JSON")}
      const r=await fetch("/api/lms/integrations/"+provider,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({provider,status:"configured",config:parsed})});
      const d=await r.json();if(!r.ok)throw new Error(d.detail||"Unable to save integration");
      setItems(items.filter(x=>x.provider!==provider).concat(d));setMessage(provider+" integration saved.");
    }catch(err){setMessage(err instanceof Error?err.message:"Unable to save integration")}finally{setBusy(false)}
  }
  async function createWebhook(e:FormEvent){
    e.preventDefault();setBusy(true);setMessage(null);
    try{
      const r=await fetch("/api/lms/webhooks",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url:hookUrl,event_types:events.split(",").map(x=>x.trim()).filter(Boolean)})});
      const d=await r.json();if(!r.ok)throw new Error(d.detail||"Unable to create webhook");
      setMessage("Webhook created. Save its secret now; it cannot be recovered.");setHookUrl("");
    }catch(err){setMessage(err instanceof Error?err.message:"Unable to create webhook")}finally{setBusy(false)}
  }
  return <>
    <SectionCard eyebrow="Integration fabric" title="Provider connections" meta="Enterprise boundaries">
      <div className="integration-grid">{providers.map(name=>{const item=items.find(x=>x.provider===name);return <div className="integration-card" key={name}><div className="integration-head"><div className="module-icon"><Network size={18}/></div><div><strong>{name.toUpperCase()}</strong><small>{item?.status||"Not configured"}</small></div><StatusBadge status={item?.status||"not configured"}/></div></div>})}</div>
      <form className="studio-form" onSubmit={save}><div className="form-grid"><label>Provider<select value={provider} onChange={e=>setProvider(e.target.value)}>{providers.map(p=><option key={p}>{p}</option>)}</select></label><label className="full-span">Configuration JSON<textarea rows={6} value={config} onChange={e=>setConfig(e.target.value)}/></label></div><button className="button button-primary" disabled={busy}><Save size={15}/> Save provider configuration</button></form>
    </SectionCard>
    <SectionCard eyebrow="Event delivery" title="Webhooks">
      <form className="studio-form" onSubmit={createWebhook}><div className="form-grid"><label className="full-span">Webhook URL<input type="url" value={hookUrl} onChange={e=>setHookUrl(e.target.value)} required placeholder="https://example.com/lms/events"/></label><label className="full-span">Event types<input value={events} onChange={e=>setEvents(e.target.value)} placeholder="course.completed, assessment.passed"/></label></div><button className="button button-secondary" disabled={busy}><Webhook size={15}/> Create webhook</button></form>
      <div className="compact-list">{webhooks.map(h=><div className="compact-row" key={h.id}><div><strong>{h.url}</strong><small>{h.event_types.join(" · ")}</small></div><StatusBadge status={h.active?"active":"disabled"}/></div>)}</div>
    </SectionCard>
    {message&&<Notice kind="success">{message}</Notice>}
  </>;
}