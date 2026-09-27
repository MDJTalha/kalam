"use client";

/* eslint-disable @next/next/no-img-element */
import { useMemo, useState } from "react";
import { Award, ExternalLink, RotateCcw, Save, ShieldOff, X } from "lucide-react";

type Certificate={id:string;learner:string;course:string;verification_code:string;issued_at:string;expires_at:string|null;status:"active"|"expiring_soon"|"expired"|"revoked"};
type Template={title:string;subtitle:string;issuer_name:string;primary_color:string;accent_color:string;logo_url:string|null;footer_text:string;version?:number};

export function CertificateAdmin({initialCertificates,initialTemplate}:{initialCertificates:Certificate[];initialTemplate:Template}) {
  const [certificates,setCertificates]=useState(initialCertificates);
  const [template,setTemplate]=useState(initialTemplate);
  const [savedTemplate,setSavedTemplate]=useState(initialTemplate);
  const [saving,setSaving]=useState(false);
  const [message,setMessage]=useState("");
  const [error,setError]=useState("");
  const [lifecycleTarget,setLifecycleTarget]=useState<{id:string;action:"renew"|"revoke"}|null>(null);
  const [reason,setReason]=useState("");
  const [search,setSearch]=useState("");
  const [statusFilter,setStatusFilter]=useState<"all"|Certificate["status"]>("all");
  const activeCount=useMemo(()=>certificates.filter(c=>c.status==="active").length,[certificates]);
  const expiringCount=useMemo(()=>certificates.filter(c=>c.status==="expiring_soon").length,[certificates]);
  const expiredCount=useMemo(()=>certificates.filter(c=>c.status==="expired").length,[certificates]);
  const revokedCount=useMemo(()=>certificates.filter(c=>c.status==="revoked").length,[certificates]);
  const statusLabel=(status:Certificate["status"])=>status==="expiring_soon"?"Expiring soon":status[0].toUpperCase()+status.slice(1);
  const isDirty=useMemo(()=>JSON.stringify(template)!==JSON.stringify(savedTemplate),[template,savedTemplate]);
  const visibleCertificates=useMemo(()=>certificates.filter((certificate)=>{
    const query=search.trim().toLowerCase();
    const matchesStatus=statusFilter==="all"||certificate.status===statusFilter;
    const matchesQuery=!query||[certificate.learner,certificate.course,certificate.verification_code].some((value)=>value.toLowerCase().includes(query));
    return matchesStatus&&matchesQuery;
  }),[certificates,search,statusFilter]);

  async function saveTemplate(){
    setSaving(true);setError("");setMessage("");
    try{
      const templatePayload=Object.fromEntries(Object.entries(template).filter(([key])=>key!=="version"));
      const r=await fetch("/api/lms/certificates/templates/default",{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify(templatePayload)});
      const data=await r.json().catch(()=>({}));if(!r.ok)throw new Error(data.detail||"Template could not be saved.");
      setTemplate(data);setSavedTemplate(data);setMessage("Certificate template saved and published.");
    }catch(e){setError(e instanceof Error?e.message:"Save failed.");}finally{setSaving(false);}
  }
  async function lifecycle(){
    if(!lifecycleTarget||reason.trim().length<3)return;
    const {id,action}=lifecycleTarget;
    setSaving(true);setError("");setMessage("");
    try{
      const body=action==="revoke"?{reason:reason.trim()}:{action:"renew",reason:reason.trim()};
      const url=action==="revoke"?"/api/lms/certificates/"+id+"/revoke":"/api/lms/certificates/"+id+"/lifecycle";
      const r=await fetch(url,{method:action==="revoke"?"POST":"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
      const data=await r.json().catch(()=>({}));if(!r.ok)throw new Error(data.detail||"Certificate lifecycle action failed.");
      setCertificates(current=>current.map(c=>c.id===id?(action==="revoke"?{...c,status:"revoked"}:{...c,status:"active",expires_at:data.expires_at}):c));
      setMessage(action==="revoke"?"Certificate revoked and audit recorded.":"Certificate renewed for 12 months.");
      setLifecycleTarget(null);setReason("");
    }catch(e){setError(e instanceof Error?e.message:"Lifecycle action failed.");}finally{setSaving(false);}
  }

  return <div className="stack-lg">
    <div className="metric-strip certificate-admin-metrics" aria-label="Credential status summary">
      <span><b>{certificates.length}</b> credentials</span><span><b>{activeCount}</b> active</span><span><b>{expiringCount}</b> expiring soon</span><span><b>{expiredCount}</b> expired</span><span><b>{revokedCount}</b> revoked</span>
    </div>
    {error&&<div className="form-error" role="alert">{error}</div>}
    {message&&<div className="form-success" role="status">{message}</div>}
    <div className="two-column">
      <section className="data-panel" aria-labelledby="template-title">
        <div className="section-heading"><div><span className="eyebrow">Template studio</span><h2 id="template-title">Certificate branding and verification</h2><p>Changes publish to new and publicly verified credentials for this tenant.</p></div><div className="button-row"><button type="button" className="button button-secondary" disabled={saving||!isDirty} onClick={()=>setTemplate(savedTemplate)}>Discard changes</button><button type="button" className="button button-primary" disabled={saving||!isDirty} onClick={saveTemplate}><Save size={15}/>{saving?"Publishing…":"Publish template"}</button></div></div>
        <div className="template-status" aria-live="polite"><span>Version {template.version??1}</span>{isDirty?<strong>Unsaved changes</strong>:<span>Published configuration</span>}</div>
        <div className="form-grid">
          <label className="form-field full"><span>Certificate title</span><input value={template.title} onChange={e=>setTemplate({...template,title:e.target.value})} /></label>
          <label className="form-field full"><span>Subtitle</span><input value={template.subtitle} onChange={e=>setTemplate({...template,subtitle:e.target.value})} /></label>
          <label className="form-field"><span>Issuer</span><input value={template.issuer_name} onChange={e=>setTemplate({...template,issuer_name:e.target.value})} /></label>
          <label className="form-field"><span>Logo URL</span><input inputMode="url" value={template.logo_url??""} onChange={e=>setTemplate({...template,logo_url:e.target.value||null})} /></label>
          <label className="form-field"><span>Primary color</span><input type="color" value={template.primary_color} aria-label="Primary certificate color" onChange={e=>setTemplate({...template,primary_color:e.target.value})} /></label>
          <label className="form-field"><span>Accent color</span><input type="color" value={template.accent_color} aria-label="Accent certificate color" onChange={e=>setTemplate({...template,accent_color:e.target.value})} /></label>
          <label className="form-field full"><span>Verification footer</span><textarea value={template.footer_text} onChange={e=>setTemplate({...template,footer_text:e.target.value})} /></label>
        </div>
      </section>
      <section className="data-panel" aria-labelledby="preview-title">
        <div className="section-heading"><div><span className="eyebrow">Live preview</span><h2 id="preview-title">Credential certificate</h2></div><Award size={22} aria-hidden="true"/></div>
        <article className="certificate-preview" style={{borderColor:template.accent_color}}>
          {template.logo_url&&<img className="certificate-preview-logo" src={template.logo_url} alt={`${template.issuer_name} logo`} referrerPolicy="no-referrer" />}
          <div className="certificate-preview-issuer" style={{color:template.primary_color}}>{template.issuer_name}</div>
          <div className="certificate-preview-title" style={{color:template.accent_color}}>{template.title}</div>
          <div className="certificate-preview-subtitle">{template.subtitle}</div>
          <div className="certificate-preview-name">Sample learner</div>
          <div className="certificate-preview-copy">has successfully completed</div>
          <div className="certificate-preview-course" style={{color:template.primary_color}}>Sample learning programme</div>
          <div className="certificate-preview-footer">{template.footer_text}</div>
        </article>
      </section>
    </div>
    <section className="data-panel" aria-labelledby="issued-title">
      <div className="section-heading"><div><span className="eyebrow">Issued certificate lifecycle</span><h2 id="issued-title">Credential operations</h2></div><span className="section-meta">{visibleCertificates.length} of {certificates.length} shown</span></div>
      <div className="filter-bar" role="search" aria-label="Filter issued certificates"><label className="filter-control"><span>Search</span><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Learner, course or code" /></label><label className="filter-control"><span>Status</span><select value={statusFilter} onChange={e=>setStatusFilter(e.target.value as "all"|Certificate["status"])}><option value="all">All statuses</option><option value="active">Active</option><option value="expiring_soon">Expiring soon</option><option value="expired">Expired</option><option value="revoked">Revoked</option></select></label></div>
      <div className="compact-list">
        {visibleCertificates.length?visibleCertificates.map(c=><div className="compact-row certificate-admin-row" key={c.id}>
          <div className="certificate-admin-main"><div className="certificate-admin-heading"><strong>{c.course}</strong><span className={"status-badge "+(c.status==="active"?"success":c.status==="revoked"||c.status==="expired"?"danger":"warning")}>{statusLabel(c.status)}</span></div><small>{c.learner} · Issued {new Date(c.issued_at).toLocaleDateString()} · {c.expires_at?"Expires "+new Date(c.expires_at).toLocaleDateString():"No expiry"}</small><a className="text-link" href={"/verify/"+c.verification_code} target="_blank" rel="noreferrer">Public verification <ExternalLink size={13}/></a></div>
          <div className="certificate-admin-actions">{c.status!=="revoked"&&<><button type="button" className="button button-secondary" disabled={saving} onClick={()=>{setLifecycleTarget({id:c.id,action:"renew"});setReason("");}}><RotateCcw size={14}/> Renew 12 months</button><button type="button" className="button button-secondary" disabled={saving} onClick={()=>{setLifecycleTarget({id:c.id,action:"revoke"});setReason("");}}><ShieldOff size={14}/> Revoke</button></>}</div>
        </div>):<div className="empty-state"><Award size={24}/><h3>{certificates.length?"No matching certificates":"No certificates issued"}</h3><p>{certificates.length?"Adjust the search or status filter to view other credentials.":"Issued credentials will appear here after a learner completes certificate-eligible learning."}</p></div>}
      </div>
    </section>
    {lifecycleTarget&&<div className="modal-wrap" role="presentation"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="lifecycle-title">
      <div className="modal-heading"><div><span className="eyebrow">Audited lifecycle action</span><h2 id="lifecycle-title">{lifecycleTarget.action==="revoke"?"Revoke certificate":"Renew certificate"}</h2><p>Record a business reason before applying this credential change.</p></div><button type="button" className="close-button" aria-label="Close lifecycle dialog" onClick={()=>{setLifecycleTarget(null);setReason("");}}><X size={16}/></button></div>
      <label className="form-field"><span>Reason</span><textarea autoFocus minLength={3} maxLength={2000} value={reason} onChange={e=>setReason(e.target.value)} placeholder={lifecycleTarget.action==="revoke"?"Why is this credential being revoked?":"Why is this credential being renewed?"} /><small>{reason.trim().length}/2000 characters</small></label>
      <div className="modal-actions"><button type="button" className="button button-secondary" disabled={saving} onClick={()=>{setLifecycleTarget(null);setReason("");}}>Cancel</button><button type="button" className="button button-primary" disabled={saving||reason.trim().length<3} onClick={lifecycle}>{saving?"Applying…":lifecycleTarget.action==="revoke"?"Revoke certificate":"Renew certificate"}</button></div>
    </section></div>}
  </div>;
}
