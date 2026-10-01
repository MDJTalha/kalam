"use client";

import Link from "next/link";
import { type FormEvent, useMemo, useState } from "react";
import {
  AlertTriangle, BookOpenCheck, CheckCircle2, ChevronDown, ChevronRight, CircleHelp,
  ClipboardCheck, Copy, FileCheck2, KeyRound, LifeBuoy, Network, Search, Settings2,
  ShieldAlert, ShieldCheck, Sparkles, UsersRound, Wrench,
} from "lucide-react";

type SupportCase={id:string;case_number:string;category:string;severity:string;subject:string;status:string;route?:string|null;created_at:string;resolved_at?:string|null};
type Props={user:{first_name:string;last_name:string;email:string;tenant_name?:string|null;job_title?:string|null;roles?:Array<{name:string}>;permissions?:string[];preferences?:{timezone?:string}};initialCases:SupportCase[]};

const faqs=[
  ["I cannot access a screen or action. What should I check?","Access is role and tenant scoped. Confirm you are signed into the correct organization, then ask an authorized administrator to verify your role and permissions. Do not share another user's account to bypass missing access."],
  ["A course, assessment or record looks wrong. What should I capture?","Capture the affected screen, route, approximate time, item name or reference, your role, and the expected versus observed result. Avoid attaching unnecessary employee data."],
  ["What should I do if I suspect unauthorized access?","Treat it as a security issue: review Active Sessions, revoke sessions you do not recognize, preserve relevant evidence, and use your organization's approved incident or administrator channel immediately."],
  ["Can I send passwords, tokens or sensitive employee data to support?","No. Never include passwords, session tokens, API secrets or unnecessary personal data in a support request. Share only the minimum information needed to diagnose the issue."],
  ["Where should configuration or product-change requests go?","Role, permission, integration, compliance and organization configuration should go through the authorized tenant administrator. Product changes should enter the organization's change-control process with an owner, requirement and test evidence."],
] as const;

export function HelpCenter({user,initialCases}:Props){
  const [copied,setCopied]=useState(false);
  const [openFaq,setOpenFaq]=useState<number|null>(0);
  const [cases,setCases]=useState(initialCases);
  const [caseBusy,setCaseBusy]=useState(false);
  const [caseMessage,setCaseMessage]=useState("");
  const [caseError,setCaseError]=useState("");
  const permissions=user.permissions||[];
  const roles=useMemo(()=>user.roles?.map(item=>item.name)||[],[user.roles]);
  const canAdmin=permissions.includes("tenant.manage");
  const canIntegrations=permissions.includes("integrations.manage");
  const canAudit=permissions.includes("audit.read");
  const timezone=user.preferences?.timezone||"UTC";

  const diagnosticText=useMemo(()=>{
    const now=new Date();
    const local=(()=>{try{return now.toLocaleString(undefined,{timeZone:timezone})}catch{return now.toISOString()}})();
    return [
      "Kalam support context",
      "Organization: "+(user.tenant_name||"Not available"),
      "User role(s): "+(roles.length?roles.join(", "):"Not assigned"),
      "Job title: "+(user.job_title||"Not provided"),
      "Time zone: "+timezone,
      "Captured: "+local,
      "Current route: "+(typeof window!=="undefined"?window.location.pathname:"/dashboard/help"),
      "Browser: "+(typeof navigator!=="undefined"?navigator.userAgent:"Not available"),
      "",
      "Describe the issue:",
      "Expected result:",
      "Observed result:",
      "Approximate time of issue:",
      "Item / record reference (if applicable):",
    ].join("\n");
  },[roles,timezone,user.job_title,user.tenant_name]);

  async function copyContext(){
    try{await navigator.clipboard.writeText(diagnosticText);setCopied(true);window.setTimeout(()=>setCopied(false),2200)}catch{setCopied(false)}
  }

  async function submitCase(event:FormEvent<HTMLFormElement>){
    event.preventDefault();
    setCaseBusy(true);setCaseMessage("");setCaseError("");
    const form=event.currentTarget; const data=new FormData(form);
    const payload={
      category:String(data.get("category")||"other"),
      severity:String(data.get("severity")||"routine"),
      subject:String(data.get("subject")||"").trim(),
      description:String(data.get("description")||"").trim(),
      route:typeof window!=="undefined"?window.location.pathname:"/dashboard/help",
    };
    try{
      const response=await fetch("/api/lms/support/cases",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(payload)});
      const body=await response.json().catch(()=>({}));
      if(!response.ok)throw new Error(typeof body.detail==="string"?body.detail:"Support case could not be created.");
      const created:SupportCase={id:String(body.id),case_number:String(body.case_number),category:payload.category,severity:payload.severity,subject:payload.subject,status:String(body.status||"open"),route:payload.route,created_at:String(body.created_at||new Date().toISOString())};
      setCases(current=>[created,...current].slice(0,20));form.reset();setCaseMessage("Support case "+created.case_number+" created. Keep the case number for follow-up.");
    }catch(cause){setCaseError(cause instanceof Error?cause.message:"Support case could not be created.")}finally{setCaseBusy(false)}
  }

  return <div className="help-center">
    <section className="help-hero">
      <div>
        <span className="eyebrow"><LifeBuoy size={14}/> Kalam support center</span>
        <h2>Resolve issues quickly. Escalate with the right context.</h2>
        <p>Use self-service guidance first, protect sensitive information, and route access or configuration issues through the authorized administrator for your organization.</p>
        <div className="help-hero-actions"><Link className="button button-primary" href="/dashboard/search"><Search size={15}/> Search Kalam</Link><Link className="button button-secondary" href="/dashboard/settings/sessions"><ShieldCheck size={15}/> Review active sessions</Link></div>
      </div>
      <div className="help-hero-status"><span>SUPPORT CONTEXT</span><strong>{user.tenant_name||"Your organization"}</strong><small>{roles.length?roles.join(" · "):"Workspace user"}</small><div><CheckCircle2 size={14}/> Signed-in workspace support</div></div>
    </section>

    <section className="help-section">
      <div className="help-section-heading"><div><span className="eyebrow">Start here</span><h2>Choose the issue you need to resolve</h2><p>Each path takes you to the most relevant Kalam workspace or recovery action.</p></div><CircleHelp size={20}/></div>
      <div className="help-topic-grid">
        <Link href="/dashboard/settings"><Settings2 size={19}/><span><strong>Profile & preferences</strong><small>Display name, time zone, workspace density, password and account settings.</small></span><ChevronRight size={16}/></Link>
        <Link href="/dashboard/settings/sessions"><KeyRound size={19}/><span><strong>Sign-in & session access</strong><small>Review active sessions, revoke unrecognized access and check sign-in security.</small></span><ChevronRight size={16}/></Link>
        <Link href="/dashboard/catalog"><BookOpenCheck size={19}/><span><strong>Learning & assignments</strong><small>Find learning, check assignments, prerequisites, enrollment and course access.</small></span><ChevronRight size={16}/></Link>
        <Link href="/dashboard/assessments"><ClipboardCheck size={19}/><span><strong>Assessments</strong><small>Review available assessments, attempts, submission and completion requirements.</small></span><ChevronRight size={16}/></Link>
        <Link href="/dashboard/certificates"><FileCheck2 size={19}/><span><strong>Credentials & evidence</strong><small>Review certificates, verification state, expiry and learning evidence.</small></span><ChevronRight size={16}/></Link>
        <Link href="/dashboard/notifications"><Sparkles size={19}/><span><strong>Notifications & reminders</strong><small>Review learning, compliance, approval and credential notifications.</small></span><ChevronRight size={16}/></Link>
      </div>
    </section>

    <section className="help-section">
      <div className="help-section-heading"><div><span className="eyebrow">Troubleshooting</span><h2>Before you escalate</h2><p>These checks resolve common issues and produce better evidence when escalation is required.</p></div><Wrench size={20}/></div>
      <div className="help-checklist">
        <article><span>01</span><div><strong>Confirm organization and role</strong><p>Make sure you are signed into the intended organization and that the requested action is appropriate for your assigned role.</p></div></article>
        <article><span>02</span><div><strong>Retry from the source workflow</strong><p>Return to the originating course, person, assessment, report or admin record rather than relying on an old browser tab or bookmarked deep link.</p></div></article>
        <article><span>03</span><div><strong>Capture useful evidence</strong><p>Record the route, item name or reference, time of the issue, expected behavior and observed behavior. A screenshot may help when it contains no unnecessary sensitive data.</p></div></article>
        <article><span>04</span><div><strong>Check security state</strong><p>For access or sign-in issues, review Active Sessions and use password recovery or your configured enterprise SSO path where applicable.</p></div></article>
      </div>
    </section>

    <section className="help-section help-case-section">
      <div className="help-section-heading"><div><span className="eyebrow">Support request</span><h2>Create a tracked support case</h2><p>Use this for product, access, workflow or technical issues. Security incidents should also follow your organization&apos;s approved incident-response channel.</p></div><LifeBuoy size={20}/></div>
      <form className="help-case-form" onSubmit={event=>void submitCase(event)}>
        <label><span>Category</span><select name="category" defaultValue="technical" required><option value="access">Access & sign-in</option><option value="learning">Learning & assignments</option><option value="assessment">Assessments</option><option value="credentials">Credentials & evidence</option><option value="compliance">Compliance & readiness</option><option value="reporting">Reports & analytics</option><option value="integration">Integrations</option><option value="technical">Technical issue</option><option value="security">Security concern</option><option value="other">Other</option></select></label>
        <label><span>Severity</span><select name="severity" defaultValue="routine" required><option value="routine">Routine — guidance or non-blocking issue</option><option value="important">Important — blocked workflow or access issue</option><option value="urgent">Urgent — suspected security/data incident</option></select></label>
        <label className="wide"><span>Subject</span><input name="subject" minLength={5} maxLength={180} required placeholder="Summarize the issue clearly"/></label>
        <label className="wide"><span>What happened?</span><textarea name="description" minLength={10} maxLength={4000} required rows={6} placeholder="Include the expected result, observed result, approximate time and any relevant item or record reference. Do not include passwords, tokens or unnecessary personal data."/></label>
        <div className="help-case-actions"><button className="button button-primary" disabled={caseBusy} type="submit">{caseBusy?"Creating case…":"Create support case"}</button><span>Cases are recorded inside your Kalam tenant and linked to your signed-in account.</span></div>
        {caseMessage&&<div className="form-success" role="status">{caseMessage}</div>}{caseError&&<div className="form-error" role="alert">{caseError}</div>}
      </form>
      <div className="help-case-list"><div className="help-case-list-head"><strong>Your recent cases</strong><span>{cases.length} shown</span></div>{cases.length?cases.map(item=><article key={item.id}><div><Link className="help-case-link" href={"/dashboard/help/cases/"+item.id}><strong>{item.subject}</strong></Link><small>{item.case_number} · {item.category} · {new Date(item.created_at).toLocaleString(undefined,{timeZone:timezone})}</small></div><div className="help-case-row-action"><span className={"status-badge "+(["resolved","closed"].includes(item.status)?"success":"warning")}>{item.status.replace("_"," ")}</span><Link className="text-link" href={"/dashboard/help/cases/"+item.id}>Open case <ChevronRight size={14}/></Link></div></article>):<div className="help-empty">No support cases have been created from this account.</div>}</div>
    </section>

    <section className="help-section help-diagnostics">
      <div className="help-section-heading"><div><span className="eyebrow">Support case readiness</span><h2>Prepare safe diagnostic context</h2><p>Copy a support template with workspace context. It intentionally excludes passwords, tokens, raw tenant IDs and application secrets.</p></div><Copy size={20}/></div>
      <div className="help-diagnostic-box"><pre>{diagnosticText}</pre><button className="button button-secondary" type="button" onClick={()=>void copyContext()}><Copy size={15}/>{copied?"Copied":"Copy support context"}</button></div>
      <div className="help-privacy-note"><ShieldAlert size={17}/><div><strong>Protect sensitive information</strong><p>Do not include passwords, session tokens, API keys, secrets, unnecessary employee records or confidential content in a support request.</p></div></div>
    </section>

    {(canAdmin||canIntegrations||canAudit)&&<section className="help-section">
      <div className="help-section-heading"><div><span className="eyebrow">Administrator support</span><h2>Administrative diagnostics</h2><p>These routes are permission-aware and are shown only when your account is authorized.</p></div><UsersRound size={20}/></div>
      <div className="help-topic-grid admin">{canAdmin&&<><Link href="/dashboard/admin"><UsersRound size={19}/><span><strong>Roles & permissions</strong><small>Verify user lifecycle, role assignment and tenant administration.</small></span><ChevronRight size={16}/></Link><Link href="/dashboard/admin/support"><LifeBuoy size={19}/><span><strong>Support Operations</strong><small>Triage, assign, respond to and resolve tracked support cases.</small></span><ChevronRight size={16}/></Link></>}{canIntegrations&&<Link href="/dashboard/integrations"><Network size={19}/><span><strong>Integrations</strong><small>Review connected services, configuration and connection testing.</small></span><ChevronRight size={16}/></Link>}{canAudit&&<Link href="/dashboard/audit"><ShieldCheck size={19}/><span><strong>Audit log</strong><small>Review governed actions and security-relevant administrative events.</small></span><ChevronRight size={16}/></Link>}</div>
    </section>}

    <section className="help-section security-support">
      <div className="help-section-heading"><div><span className="eyebrow">Security & incidents</span><h2>Use the right escalation path</h2><p>Not every support issue has the same urgency or handling requirements.</p></div><AlertTriangle size={20}/></div>
      <div className="help-severity-grid"><article><span className="help-severity routine">Routine</span><strong>How-to or expected-use questions</strong><p>Use search, the relevant workspace, or your organization administrator for normal product guidance and configuration questions.</p></article><article><span className="help-severity important">Important</span><strong>Access, incorrect configuration or blocked workflow</strong><p>Capture the affected route, role, record reference and time, then escalate through the approved administrator/support channel.</p></article><article><span className="help-severity urgent">Urgent</span><strong>Suspected security or data incident</strong><p>Preserve evidence, revoke suspicious sessions where appropriate, avoid modifying logs, and use your organization&apos;s incident-response channel immediately.</p></article></div>
    </section>

    <section className="help-section">
      <div className="help-section-heading"><div><span className="eyebrow">Frequently asked questions</span><h2>Common support guidance</h2></div><CircleHelp size={20}/></div>
      <div className="help-faq">{faqs.map(([question,answer],index)=><div className="help-faq-item" key={question}><button type="button" aria-expanded={openFaq===index} onClick={()=>setOpenFaq(openFaq===index?null:index)}><span>{question}</span><ChevronDown size={16}/></button>{openFaq===index&&<p>{answer}</p>}</div>)}</div>
    </section>

    <section className="help-boundary"><ShieldCheck size={19}/><div><strong>Support and service boundaries</strong><p>Kalam support handling, response targets, service levels and incident channels depend on the deployment and the organization&apos;s approved commercial and operational arrangements. This screen does not create or imply an SLA. Your organization administrator remains the first escalation point for role, permission and tenant-configuration changes unless another support process has been formally agreed.</p></div></section>
  </div>;
}
