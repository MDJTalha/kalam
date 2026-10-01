"use client";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Save } from "lucide-react";
import { SaaSLookupSelect } from "@/components/saas-lookup-select";

type Option = { id: string; name: string };

async function postJson(path: string, body: Record<string, unknown>) {
  const response = await fetch(path, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Unable to save record");
  return payload;
}

function useSubmit() {
  const [busy,setBusy] = useState(false);
  const [message,setMessage] = useState("");
  async function run(work: () => Promise<unknown>) {
    setBusy(true); setMessage("");
    try { await work(); setMessage("Saved successfully."); window.location.reload(); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Unable to save record"); }
    finally { setBusy(false); }
  }
  return {busy,message,run};
}

export function SupportModeBanner({tenantName,expiresAt}:{tenantName:string;expiresAt:string}) {
  const router=useRouter();
  const [busy,setBusy]=useState(false);
  async function stop(){
    setBusy(true);
    await fetch("/api/v1/support/developer/support/stop",{method:"POST"});
    router.push("/dashboard");
  }
  return <div className="support-mode-banner" role="status">
    <div><strong>SUPPORT MODE</strong><span>Viewing <b>{tenantName}</b> as Platform Developer · expires {new Date(expiresAt).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})}</span></div>
    <button className="button button-secondary" type="button" disabled={busy} onClick={stop}>{busy?"Exiting…":"Exit Support Mode"}</button>
  </div>;
}

export function DeveloperSupportControl({tenants}:{tenants:Array<{id:string;name:string;slug:string;status:string}>}) {
  const router=useRouter();
  const [tenantId,setTenantId]=useState(tenants[0]?.id||"");
  const [reason,setReason]=useState("Customer tenant troubleshooting");
  const [minutes,setMinutes]=useState(60);
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState("");
  async function start(){
    setBusy(true); setMessage("");
    try{
      const response=await fetch("/api/v1/support/developer/support/start",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({tenant_id:tenantId,reason,duration_minutes:minutes})});
      const payload=await response.json().catch(()=>({}));
      if(!response.ok) throw new Error(typeof payload.detail==="string"?payload.detail:"Unable to enter support mode");
      router.push("/dashboard");
    }catch(error){setMessage(error instanceof Error?error.message:"Unable to enter support mode");setBusy(false);}
  }
  return <div className="studio-form">
    <div className="form-grid">
      <label>Customer tenant<select value={tenantId} onChange={e=>setTenantId(e.target.value)}>{tenants.map(t=><option key={t.id} value={t.id}>{t.name} · {t.slug}</option>)}</select></label>
      <label>Session duration<select value={minutes} onChange={e=>setMinutes(Number(e.target.value))}><option value={30}>30 minutes</option><option value={60}>1 hour</option><option value={120}>2 hours</option><option value={240}>4 hours</option></select></label>
    </div>
    <label>Support reason<input value={reason} onChange={e=>setReason(e.target.value)} minLength={10} maxLength={500}/></label>
    <button className="button button-primary" type="button" disabled={busy||!tenantId||reason.trim().length<10} onClick={start}>{busy?"Entering…":"Enter Support Mode"}</button>
    {message&&<p className="form-status">{message}</p>}
  </div>;
}

export function AccountCreateForm({plans}:{plans:Option[]}) {
  const state=useSubmit();
  function submit(event:FormEvent<HTMLFormElement>){event.preventDefault();const d=new FormData(event.currentTarget);void state.run(()=>postJson("/api/lms/saas/crm/accounts",{name:d.get("name"),slug:String(d.get("slug")||"").toLowerCase(),account_type:d.get("account_type"),lifecycle_stage:d.get("lifecycle_stage"),industry:d.get("industry")||null,country:d.get("country")||null,employee_band:d.get("employee_band")||null,plan_id:d.get("plan_id")||null,public_showcase:false}));}
  return <form className="studio-form" onSubmit={submit}><div className="form-grid"><label>Name<input name="name" required/></label><label>CRM slug<input name="slug" required placeholder="acme-corp"/></label><label>Account type<select name="account_type"><option value="prospect">Prospect</option><option value="client">Client</option><option value="partner">Partner</option></select></label><label>Lifecycle<select name="lifecycle_stage"><option value="lead">Lead</option><option value="qualified">Qualified</option><option value="trial">Trial</option><option value="customer">Customer</option><option value="churned">Churned</option></select></label><label>Industry<input name="industry"/></label><label>Country<input name="country"/></label><label>Employee band<input name="employee_band" placeholder="1,000–5,000"/></label><label>Plan<select name="plan_id"><option value="">Not assigned</option>{plans.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label></div><button className="button button-primary" disabled={state.busy}><Plus size={15}/> Add account</button>{state.message&&<p className="form-status">{state.message}</p>}</form>;
}

export function PlanCreateForm() {
  const state=useSubmit();
  function submit(event:FormEvent<HTMLFormElement>){event.preventDefault();const d=new FormData(event.currentTarget);const features=String(d.get("features")||"").split("\n").map(v=>v.trim()).filter(Boolean);const maxSeats=String(d.get("maximum_seats")||"").trim();const merchandising={featured:d.get("featured")==="on",badge_label:String(d.get("badge_label")||"").trim()||null,cta_type:String(d.get("cta_type")||"auto"),cta_label:String(d.get("cta_label")||"").trim()||null,comparison_label:String(d.get("comparison_label")||"").trim()||null};void state.run(()=>postJson("/api/lms/saas/crm/plans",{code:String(d.get("code")||"").toLowerCase(),name:d.get("name"),tagline:d.get("tagline")||null,description:d.get("description")||null,billing_model:d.get("billing_model"),currency:d.get("currency"),monthly_price_minor:d.get("monthly")?Math.round(Number(d.get("monthly"))*100):null,annual_price_minor:d.get("annual")?Math.round(Number(d.get("annual"))*100):null,trial_days:Number(d.get("trial_days")||0),minimum_seats:Number(d.get("minimum_seats")||1),maximum_seats:maxSeats?Number(maxSeats):null,features,limits:{public_merchandising:merchandising},sort_order:Number(d.get("sort_order")||100),public_visible:d.get("public_visible")==="on",status:"active"}));}
  return <form className="studio-form" onSubmit={submit}><div className="form-grid"><label>Plan code<input name="code" required placeholder="growth"/></label><label>Plan name<input name="name" required/></label><label>Tagline<input name="tagline"/></label><label>Billing model<select name="billing_model"><option value="per_user">Per user</option><option value="flat">Flat</option><option value="custom">Custom</option></select></label><label>Currency<select name="currency"><option>USD</option><option>PKR</option><option>EUR</option><option>GBP</option></select></label><label>Monthly price<input name="monthly" type="number" min="0" step="0.01"/></label><label>Annual price<input name="annual" type="number" min="0" step="0.01"/></label><label>Trial days<input name="trial_days" type="number" min="0" max="365" defaultValue="0"/></label><label>Minimum seats<input name="minimum_seats" type="number" min="1" defaultValue="1"/></label><label>Maximum seats<input name="maximum_seats" type="number" min="1"/></label><label>Display order<input name="sort_order" type="number" min="0" defaultValue="100"/></label><label>Public badge<input name="badge_label" maxLength={40} placeholder="Most popular"/></label><label>Public CTA<select name="cta_type"><option value="auto">Automatic</option><option value="evaluation">Guided evaluation</option><option value="sales">Contact sales</option></select></label><label>CTA label<input name="cta_label" maxLength={60} placeholder="Evaluate Growth"/></label><label>Comparison label<input name="comparison_label" maxLength={80} placeholder="Best for scaling teams"/></label></div><label>Description<textarea name="description" rows={3}/></label><label>Features, one per line<textarea name="features" rows={6}/></label><label className="compact-row"><span><strong>Feature this plan publicly</strong><small>Controls featured styling.</small></span><input name="featured" type="checkbox"/></label><label className="compact-row"><span><strong>Publish on pricing page</strong><small>Only enable after commercial approval.</small></span><input name="public_visible" type="checkbox"/></label><button className="button button-primary" disabled={state.busy}><Save size={15}/> Create plan</button>{state.message&&<p className="form-status">{state.message}</p>}</form>;
}

export function OfferCreateForm({plans}:{plans:Option[]}) {
  const state=useSubmit();
  function submit(event:FormEvent<HTMLFormElement>){event.preventDefault();const d=new FormData(event.currentTarget);void state.run(()=>postJson("/api/lms/saas/crm/offers",{plan_id:d.get("plan_id")||null,code:String(d.get("code")||"").toUpperCase(),title:d.get("title"),description:d.get("description")||null,discount_type:d.get("discount_type"),discount_value:Number(d.get("discount_value")||0),status:d.get("status"),starts_at:d.get("starts_at")?new Date(String(d.get("starts_at"))).toISOString():null,ends_at:d.get("ends_at")?new Date(String(d.get("ends_at"))).toISOString():null,public_visible:d.get("public_visible")==="on"}));}
  return <form className="studio-form" onSubmit={submit}><div className="form-grid"><label>Offer code<input name="code" required/></label><label>Title<input name="title" required/></label><label>Plan<select name="plan_id"><option value="">All / negotiated</option>{plans.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label><label>Discount type<select name="discount_type"><option value="percent">Percent</option><option value="fixed">Fixed minor units</option></select></label><label>Discount value<input name="discount_value" type="number" min="0" defaultValue="0"/></label><label>Status<select name="status"><option value="draft">Draft</option><option value="active">Active</option><option value="expired">Expired</option></select></label><label>Starts<input name="starts_at" type="datetime-local"/></label><label>Ends<input name="ends_at" type="datetime-local"/></label></div><label>Description<textarea name="description" rows={4}/></label><label className="compact-row"><span><strong>Publish offer</strong><small>Visible on public pricing only while active and within its validity window.</small></span><input name="public_visible" type="checkbox"/></label><button className="button button-primary" disabled={state.busy}><Save size={15}/> Create offer</button>{state.message&&<p className="form-status">{state.message}</p>}</form>;
}

export function TrialCreateForm() {
  const state=useSubmit();
  function submit(event:FormEvent<HTMLFormElement>){event.preventDefault();const d=new FormData(event.currentTarget);void state.run(()=>postJson("/api/lms/saas/crm/trials",{account_id:d.get("account_id"),plan_id:d.get("plan_id")||null,status:d.get("status"),seats:Number(d.get("seats")||25),starts_at:d.get("starts_at")?new Date(String(d.get("starts_at"))).toISOString():null,ends_at:d.get("ends_at")?new Date(String(d.get("ends_at"))).toISOString():null,notes:d.get("notes")||null}));}
  return <form className="studio-form" onSubmit={submit}>
    <div className="form-grid">
      <SaaSLookupSelect name="account_id" label="Account" endpoint="/api/lms/saas/crm/lookups/accounts" required />
      <SaaSLookupSelect name="plan_id" label="Plan" endpoint="/api/lms/saas/crm/lookups/plans" placeholder="Search plans (optional)" />
      <label>Status<select name="status"><option value="scheduled">Scheduled</option><option value="active">Active</option><option value="expired">Expired</option><option value="converted">Converted</option></select></label>
      <label>Seats<input name="seats" type="number" min="1" defaultValue="25"/></label>
      <label>Starts<input name="starts_at" type="datetime-local"/></label>
      <label>Ends<input name="ends_at" type="datetime-local"/></label>
    </div>
    <p className="muted">To activate a trial, provision the customer tenant and set dates that include today.</p>
    <label>Notes<textarea name="notes" rows={4}/></label>
    <button className="button button-primary" disabled={state.busy}><Plus size={15}/> Create trial</button>
    {state.message&&<p className="form-status">{state.message}</p>}
  </form>;
}

export function SubscriptionCreateForm() {
  const state=useSubmit();
  function submit(event:FormEvent<HTMLFormElement>){event.preventDefault();const d=new FormData(event.currentTarget);const list=Math.round(Number(d.get("list_price")||0)*100);const discount=Math.round(Number(d.get("discount")||0)*100);void state.run(()=>postJson("/api/lms/saas/crm/subscriptions",{account_id:d.get("account_id"),plan_id:d.get("plan_id")||null,offer_id:d.get("offer_id")||null,status:d.get("status"),billing_cycle:d.get("billing_cycle"),currency:d.get("currency"),seats:Number(d.get("seats")||1),list_price_minor:list,discount_minor:discount,net_price_minor:Math.max(0,list-discount),contract_ref:d.get("contract_ref")||null}));}
  return <form className="studio-form" onSubmit={submit}>
    <div className="form-grid">
      <SaaSLookupSelect name="account_id" label="Account" endpoint="/api/lms/saas/crm/lookups/accounts" required />
      <SaaSLookupSelect name="plan_id" label="Plan" endpoint="/api/lms/saas/crm/lookups/plans" placeholder="Search plans (optional)" />
      <SaaSLookupSelect name="offer_id" label="Offer" endpoint="/api/lms/saas/crm/lookups/offers" placeholder="Search offers (optional)" />
      <label>Status<select name="status"><option value="draft">Draft</option><option value="active">Active</option><option value="paused">Paused</option><option value="cancelled">Cancelled</option></select></label>
      <label>Billing cycle<select name="billing_cycle"><option value="annual">Annual</option><option value="monthly">Monthly</option><option value="custom">Custom</option></select></label>
      <label>Currency<select name="currency"><option>USD</option><option>PKR</option><option>EUR</option><option>GBP</option></select></label>
      <label>Seats<input name="seats" type="number" min="1" defaultValue="1"/></label>
      <label>List price<input name="list_price" type="number" min="0" step="0.01"/></label>
      <label>Negotiated discount<input name="discount" type="number" min="0" step="0.01"/><small>When an offer is selected, its discount is calculated from the list price on save.</small></label>
      <label>Contract reference<input name="contract_ref"/></label>
    </div>
    <button className="button button-primary" disabled={state.busy}><Save size={15}/> Create subscription</button>
    {state.message&&<p className="form-status">{state.message}</p>}
  </form>;
}

export function OpportunityCreateForm() {
  const state=useSubmit();
  function submit(event:FormEvent<HTMLFormElement>){event.preventDefault();const d=new FormData(event.currentTarget);void state.run(()=>postJson("/api/lms/saas/crm/opportunities",{account_id:d.get("account_id"),name:d.get("name"),stage:d.get("stage"),currency:d.get("currency"),amount_minor:Math.round(Number(d.get("amount")||0)*100),probability_percent:Number(d.get("probability")||0),expected_close_at:d.get("expected_close_at")?new Date(String(d.get("expected_close_at"))).toISOString():null,notes:d.get("notes")||null}));}
  return <form className="studio-form" onSubmit={submit}><div className="form-grid"><SaaSLookupSelect name="account_id" label="Account" endpoint="/api/lms/saas/crm/lookups/accounts" required /><label>Opportunity<input name="name" required/></label><label>Stage<select name="stage"><option value="discovery">Discovery</option><option value="qualified">Qualified</option><option value="proposal">Proposal</option><option value="negotiation">Negotiation</option><option value="won">Won</option><option value="lost">Lost</option></select></label><label>Currency<select name="currency"><option>USD</option><option>PKR</option><option>EUR</option><option>GBP</option></select></label><label>Amount<input name="amount" type="number" min="0" step="0.01"/></label><label>Probability %<input name="probability" type="number" min="0" max="100" defaultValue="0"/></label><label>Expected close<input name="expected_close_at" type="datetime-local"/></label></div><label>Notes<textarea name="notes" rows={4}/></label><button className="button button-primary" disabled={state.busy}><Plus size={15}/> Add opportunity</button>{state.message&&<p className="form-status">{state.message}</p>}</form>;
}

export function CertificationCreateForm() {
  const state=useSubmit();
  const [status,setStatus]=useState("planned");
  const canPublish=["registered","active"].includes(status);
  function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();
    const d=new FormData(event.currentTarget);
    void state.run(()=>postJson("/api/lms/saas/crm/certifications",{
      title:d.get("title"),
      issuer:d.get("issuer"),
      registration_number:d.get("registration_number")||null,
      status:d.get("status"),
      public_visible:d.get("public_visible")==="on",
      issued_at:d.get("issued_at")?new Date(String(d.get("issued_at"))).toISOString():null,
      expires_at:d.get("expires_at")?new Date(String(d.get("expires_at"))).toISOString():null,
      verification_url:d.get("verification_url")||null,
      display_order:100,
    }));
  }
  return <form className="studio-form certification-form" onSubmit={submit}>
    <div className="form-grid">
      <label>Certification title<input name="title" required placeholder="ISO 9001:2015"/></label>
      <label>Issuer<input name="issuer" required placeholder="Certification body"/></label>
      <label>Registration number<input name="registration_number" placeholder="Certificate / registration reference"/></label>
      <label>Status<select name="status" value={status} onChange={(event)=>setStatus(event.target.value)}><option value="planned">Planned</option><option value="registered">Registered</option><option value="active">Active</option><option value="expired">Expired</option></select></label>
      <label>Issue date<input name="issued_at" type="date"/></label>
      <label>Expiry date<input name="expires_at" type="date"/></label>
      <label className="certification-form-wide">Verification URL<input name="verification_url" type="url" placeholder="https://…"/></label>
    </div>
    <label className={"compact-row certification-publish-row"+(!canPublish?" disabled":"")}>
      <span><strong>Publish publicly</strong><small>{canPublish ? "Makes this certification available to external viewers." : "Available after the certification is registered or active."}</small></span>
      <input name="public_visible" type="checkbox" disabled={!canPublish}/>
    </label>
    <button className="button button-primary certification-submit" disabled={state.busy}><Save size={15}/>{state.busy ? "Registering…" : "Register certification"}</button>
    {state.message&&<p className="form-status">{state.message}</p>}
  </form>;
}


async function patchJson(path:string,body:Record<string,unknown>){
  const response=await fetch(path,{method:"PATCH",headers:{"content-type":"application/json"},body:JSON.stringify(body)});
  const payload=await response.json().catch(()=>({}));
  if(!response.ok)throw new Error(typeof payload.detail==="string"?payload.detail:"Unable to update record");
  return payload;
}

export function AccountQuickActions({id,lifecycleStage,publicShowcase}:{id:string;lifecycleStage:string;publicShowcase:boolean}){
  const state=useSubmit();
  return <div className="certificate-admin-actions">
    <select aria-label="Lifecycle stage" defaultValue={lifecycleStage} onChange={e=>void state.run(()=>patchJson("/api/lms/saas/crm/accounts/"+id,{lifecycle_stage:e.target.value}))}>
      <option value="lead">Lead</option><option value="qualified">Qualified</option><option value="trial">Trial</option><option value="customer">Customer</option><option value="churned">Churned</option>
    </select>
    <button className="button button-secondary" type="button" disabled={state.busy} onClick={()=>void state.run(()=>patchJson("/api/lms/saas/crm/accounts/"+id,{public_showcase:!publicShowcase}))}>{publicShowcase?"Unpublish":"Publish client"}</button>
  </div>;
}

export function PlanQuickActions({id,publicVisible,status}:{id:string;publicVisible:boolean;status:string}){
  const state=useSubmit();
  return <div className="certificate-admin-actions">
    <select aria-label="Plan status" defaultValue={status} onChange={e=>void state.run(()=>patchJson("/api/lms/saas/crm/plans/"+id,{status:e.target.value}))}><option value="active">Active</option><option value="draft">Draft</option><option value="retired">Retired</option></select>
    <button className="button button-secondary" type="button" disabled={state.busy} onClick={()=>void state.run(()=>patchJson("/api/lms/saas/crm/plans/"+id,{public_visible:!publicVisible}))}>{publicVisible?"Hide public":"Publish plan"}</button>
  </div>;
}

export function TrialQuickActions({id,status}:{id:string;status:string}){
  const state=useSubmit();
  return <span><select aria-label="Trial status" defaultValue={status} onChange={e=>void state.run(()=>patchJson("/api/lms/saas/crm/trials/"+id,{status:e.target.value}))}><option value="scheduled">Scheduled</option><option value="active">Active</option><option value="expired">Expired</option><option value="converted">Converted</option><option value="cancelled">Cancelled</option></select>{state.message&&<small role="status" className="form-status">{state.message}</small>}</span>;
}

export function SubscriptionQuickActions({id,status}:{id:string;status:string}){
  const state=useSubmit();
  return <select aria-label="Subscription status" defaultValue={status} onChange={e=>void state.run(()=>patchJson("/api/lms/saas/crm/subscriptions/"+id,{status:e.target.value}))}><option value="draft">Draft</option><option value="active">Active</option><option value="paused">Paused</option><option value="cancelled">Cancelled</option><option value="expired">Expired</option></select>;
}

export function OpportunityQuickActions({id,stage}:{id:string;stage:string}){
  const state=useSubmit();
  return <select aria-label="Opportunity stage" defaultValue={stage} onChange={e=>void state.run(()=>patchJson("/api/lms/saas/crm/opportunities/"+id,{stage:e.target.value}))}><option value="discovery">Discovery</option><option value="qualified">Qualified</option><option value="proposal">Proposal</option><option value="negotiation">Negotiation</option><option value="won">Won</option><option value="lost">Lost</option></select>;
}

export function CertificationQuickActions({id,status,publicVisible}:{id:string;status:string;publicVisible:boolean}){
  const state=useSubmit();
  const canPublish=["active","registered"].includes(status);
  return <div className="certificate-admin-actions"><select aria-label="Certification status" defaultValue={status} onChange={e=>void state.run(()=>patchJson("/api/lms/saas/crm/certifications/"+id,{status:e.target.value}))}><option value="planned">Planned</option><option value="registered">Registered</option><option value="active">Active</option><option value="expired">Expired</option></select><button className="button button-secondary" type="button" disabled={state.busy||(!publicVisible&&!canPublish)} onClick={()=>void state.run(()=>patchJson("/api/lms/saas/crm/certifications/"+id,{public_visible:!publicVisible}))}>{publicVisible?"Unpublish":"Publish"}</button></div>;
}


export function ProvisionTenantButton({accountId,disabled=false}:{accountId:string;disabled?:boolean}){
  const state=useSubmit();
  return <button className="button button-secondary" type="button" disabled={disabled||state.busy} onClick={()=>void state.run(()=>postJson("/api/lms/saas/crm/accounts/"+accountId+"/provision-tenant",{}))}>{disabled?"Tenant linked":"Provision tenant"}</button>;
}

export function TenantStatusControl({id,status}:{id:string;status:string}){
  const state=useSubmit();
  return <select aria-label="Tenant status" defaultValue={status} onChange={e=>void state.run(()=>patchJson("/api/lms/saas/crm/tenants/"+id,{status:e.target.value}))}><option value="active">Active</option><option value="inactive">Inactive</option></select>;
}

export function InquiryConvertButton({id,accountId,requestType}:{id:string;accountId?:string|null;requestType?:"demo"|"sales"|"trial"}){
  const state=useSubmit();
  if(accountId)return <Link className="button button-secondary" href={"/dashboard/saas/clients/"+accountId}>Open CRM account</Link>;
  const isTrial=requestType==="trial";
  function submit(event:FormEvent<HTMLFormElement>){event.preventDefault();const d=new FormData(event.currentTarget);void state.run(()=>postJson("/api/lms/saas/crm/inquiries/"+id+"/convert",{lifecycle_stage:isTrial?"trial":"qualified",create_opportunity:true,create_trial:isTrial,currency:d.get("currency"),opportunity_amount_minor:Math.round(Number(d.get("amount")||0)*100),trial_seats:isTrial?Number(d.get("trial_seats")||25):25}));}
  return <form className="toolbar-row" onSubmit={submit}><label>Opportunity value<input name="amount" type="number" min="0" step="0.01" defaultValue="0" aria-label="Opportunity value"/></label><label>Currency<select name="currency" defaultValue="USD" aria-label="Opportunity currency"><option>USD</option><option>EUR</option><option>GBP</option><option>PKR</option></select></label>{isTrial&&<label>Trial seats<input name="trial_seats" type="number" min="1" defaultValue="25" aria-label="Trial seats"/></label>}<button className="button button-primary" type="submit" disabled={state.busy}>{isTrial?"Convert + schedule trial":"Convert to CRM"}</button>{state.message&&<small role="status" className="form-status">{state.message}</small>}</form>;
}


export function AccountProfileForm({account}:{account:{id:string;name:string;industry?:string|null;country?:string|null;website?:string|null;employee_band?:string|null;testimonial?:string|null;notes?:string|null}}){
  const state=useSubmit();
  function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();
    const d=new FormData(event.currentTarget);
    void state.run(()=>patchJson("/api/lms/saas/crm/accounts/"+account.id,{
      name:d.get("name"),
      industry:d.get("industry")||null,
      country:d.get("country")||null,
      website:d.get("website")||null,
      employee_band:d.get("employee_band")||null,
      testimonial:d.get("testimonial")||null,
      notes:d.get("notes")||null,
    }));
  }
  return <form className="studio-form" onSubmit={submit}>
    <div className="form-grid">
      <label>Account name<input name="name" defaultValue={account.name} required/></label>
      <label>Industry<input name="industry" defaultValue={account.industry||""}/></label>
      <label>Country<input name="country" defaultValue={account.country||""}/></label>
      <label>Website<input name="website" type="url" defaultValue={account.website||""}/></label>
      <label>Employee band<input name="employee_band" defaultValue={account.employee_band||""}/></label>
    </div>
    <label>Public testimonial<textarea name="testimonial" rows={4} defaultValue={account.testimonial||""}/></label>
    <label>Internal notes<textarea name="notes" rows={6} defaultValue={account.notes||""}/></label>
    <button className="button button-primary" disabled={state.busy}><Save size={15}/> Save account profile</button>
    {state.message&&<p className="form-status">{state.message}</p>}
  </form>;
}

export function ContactCreateForm({accountId}:{accountId:string}){
  const state=useSubmit();
  function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();
    const d=new FormData(event.currentTarget);
    void state.run(()=>postJson("/api/lms/saas/crm/contacts",{
      account_id:accountId,
      first_name:d.get("first_name"),
      last_name:d.get("last_name"),
      email:d.get("email"),
      job_title:d.get("job_title")||null,
      phone:d.get("phone")||null,
      is_primary:d.get("is_primary")==="on",
    }));
  }
  return <form className="studio-form" onSubmit={submit}>
    <div className="form-grid">
      <label>First name<input name="first_name" required/></label>
      <label>Last name<input name="last_name" required/></label>
      <label>Work email<input name="email" type="email" required/></label>
      <label>Job title<input name="job_title"/></label>
      <label>Phone<input name="phone"/></label>
    </div>
    <label className="compact-row"><span><strong>Primary contact</strong><small>Use as the main commercial contact for the account.</small></span><input name="is_primary" type="checkbox"/></label>
    <button className="button button-primary" disabled={state.busy}><Plus size={15}/> Add contact</button>
    {state.message&&<p className="form-status">{state.message}</p>}
  </form>;
}

export function ActivityCreateForm({accountId}:{accountId:string}){
  const state=useSubmit();
  function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();
    const d=new FormData(event.currentTarget);
    void state.run(()=>postJson("/api/lms/saas/crm/activities",{
      account_id:accountId,
      activity_type:d.get("activity_type"),
      subject:d.get("subject"),
      body:d.get("body")||null,
    }));
  }
  return <form className="studio-form" onSubmit={submit}>
    <div className="form-grid">
      <label>Activity type<select name="activity_type"><option value="note">Note</option><option value="call">Call</option><option value="email">Email</option><option value="meeting">Meeting</option><option value="proposal">Proposal</option><option value="contract">Contract</option></select></label>
      <label>Subject<input name="subject" required/></label>
    </div>
    <label>Details<textarea name="body" rows={5}/></label>
    <button className="button button-primary" disabled={state.busy}><Plus size={15}/> Add activity</button>
    {state.message&&<p className="form-status">{state.message}</p>}
  </form>;
}


export function PlanEditForm({plan}:{plan:{
  id:string;name:string;tagline?:string|null;description?:string|null;status:string;public_visible:boolean;
  billing_model:string;currency:string;monthly_price_minor?:number|null;annual_price_minor?:number|null;
  trial_days:number;minimum_seats:number;maximum_seats?:number|null;features:unknown[];sort_order:number;
  limits?:Record<string,unknown>;
}}){
  const state=useSubmit();
  function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();
    const d=new FormData(event.currentTarget);
    const monthly=String(d.get("monthly")||"").trim();
    const annual=String(d.get("annual")||"").trim();
    const maxSeats=String(d.get("maximum_seats")||"").trim();
    const features=String(d.get("features")||"").split("\n").map(v=>v.trim()).filter(Boolean);
    const existingLimits=plan.limits&&typeof plan.limits==="object"?plan.limits:{};
    const merchandising={
      featured:d.get("featured")==="on",
      badge_label:String(d.get("badge_label")||"").trim()||null,
      cta_type:String(d.get("cta_type")||"").trim()||"auto",
      cta_label:String(d.get("cta_label")||"").trim()||null,
      comparison_label:String(d.get("comparison_label")||"").trim()||null,
    };
    void state.run(()=>patchJson("/api/lms/saas/crm/plans/"+plan.id,{
      name:d.get("name"),
      tagline:d.get("tagline")||null,
      description:d.get("description")||null,
      status:d.get("status"),
      public_visible:d.get("public_visible")==="on",
      currency:d.get("currency"),
      monthly_price_minor:monthly?Math.round(Number(monthly)*100):null,
      annual_price_minor:annual?Math.round(Number(annual)*100):null,
      trial_days:Number(d.get("trial_days")||0),
      minimum_seats:Number(d.get("minimum_seats")||1),
      maximum_seats:maxSeats?Number(maxSeats):null,
      features,
      limits:{...existingLimits,public_merchandising:merchandising},
      sort_order:Number(d.get("sort_order")||100),
    }));
  }
  const features=Array.isArray(plan.features)?plan.features.filter((v):v is string=>typeof v==="string").join("\n"):"";
  const merchandisingRaw=plan.limits&&typeof plan.limits==="object"?(plan.limits as Record<string,unknown>).public_merchandising:null;
  const merchandising=merchandisingRaw&&typeof merchandisingRaw==="object"?merchandisingRaw as Record<string,unknown>:{};
  return <form className="studio-form" onSubmit={submit}>
    <div className="form-grid">
      <label>Plan name<input name="name" defaultValue={plan.name} required/></label>
      <label>Tagline<input name="tagline" defaultValue={plan.tagline||""}/></label>
      <label>Status<select name="status" defaultValue={plan.status}><option value="draft">Draft</option><option value="active">Active</option><option value="retired">Retired</option></select></label>
      <label>Currency<select name="currency" defaultValue={plan.currency}><option>USD</option><option>PKR</option><option>EUR</option><option>GBP</option></select></label>
      <label>Monthly price<input name="monthly" type="number" min="0" step="0.01" defaultValue={plan.monthly_price_minor==null?"":plan.monthly_price_minor/100}/></label>
      <label>Annual price<input name="annual" type="number" min="0" step="0.01" defaultValue={plan.annual_price_minor==null?"":plan.annual_price_minor/100}/></label>
      <label>Trial days<input name="trial_days" type="number" min="0" max="365" defaultValue={plan.trial_days}/></label>
      <label>Minimum seats<input name="minimum_seats" type="number" min="1" defaultValue={plan.minimum_seats}/></label>
      <label>Maximum seats<input name="maximum_seats" type="number" min="1" defaultValue={plan.maximum_seats??""}/></label>
      <label>Display order<input name="sort_order" type="number" defaultValue={plan.sort_order}/></label>
      <label>Public badge<input name="badge_label" maxLength={40} defaultValue={typeof merchandising.badge_label==="string"?merchandising.badge_label:""} placeholder="Most popular"/></label>
      <label>Public CTA<select name="cta_type" defaultValue={typeof merchandising.cta_type==="string"?merchandising.cta_type:"auto"}><option value="auto">Automatic</option><option value="evaluation">Guided evaluation</option><option value="sales">Contact sales</option></select></label>
      <label>CTA label<input name="cta_label" maxLength={60} defaultValue={typeof merchandising.cta_label==="string"?merchandising.cta_label:""} placeholder="Evaluate Scale"/></label>
      <label>Comparison label<input name="comparison_label" maxLength={80} defaultValue={typeof merchandising.comparison_label==="string"?merchandising.comparison_label:""} placeholder="Best for multi-team organizations"/></label>
    </div>
    <label className="compact-row"><span><strong>Feature this plan publicly</strong><small>Controls featured styling and does not depend on card position.</small></span><input name="featured" type="checkbox" defaultChecked={merchandising.featured===true}/></label>
    <label>Description<textarea name="description" rows={4} defaultValue={plan.description||""}/></label>
    <label>Features, one per line<textarea name="features" rows={8} defaultValue={features}/></label>
    <label className="compact-row"><span><strong>Publish on public pricing</strong><small>Only approved prices and terms should be exposed publicly.</small></span><input name="public_visible" type="checkbox" defaultChecked={plan.public_visible}/></label>
    <button className="button button-primary" disabled={state.busy}><Save size={15}/> Save commercial plan</button>
    {state.message&&<p className="form-status">{state.message}</p>}
  </form>;
}

export function OfferEditForm({offer}:{offer:{
  id:string;title:string;description?:string|null;discount_type:string;discount_value:number;
  status:string;public_visible:boolean;starts_at?:string|null;ends_at?:string|null;
}}){
  const state=useSubmit();
  function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();
    const d=new FormData(event.currentTarget);
    void state.run(()=>patchJson("/api/lms/saas/crm/offers/"+offer.id,{
      title:d.get("title"),
      description:d.get("description")||null,
      discount_type:d.get("discount_type"),
      discount_value:Number(d.get("discount_value")||0),
      status:d.get("status"),
      public_visible:d.get("public_visible")==="on",
      starts_at:d.get("starts_at")?new Date(String(d.get("starts_at"))).toISOString():null,
      ends_at:d.get("ends_at")?new Date(String(d.get("ends_at"))).toISOString():null,
    }));
  }
  const localInput=(value?:string|null)=>value?new Date(value).toISOString().slice(0,16):"";
  return <form className="studio-form" onSubmit={submit}>
    <div className="form-grid">
      <label>Title<input name="title" defaultValue={offer.title} required/></label>
      <label>Discount type<select name="discount_type" defaultValue={offer.discount_type}><option value="percent">Percent</option><option value="fixed">Fixed minor units</option></select></label>
      <label>Discount value<input name="discount_value" type="number" min="0" defaultValue={offer.discount_value}/></label>
      <label>Status<select name="status" defaultValue={offer.status}><option value="draft">Draft</option><option value="active">Active</option><option value="expired">Expired</option></select></label>
      <label>Starts<input name="starts_at" type="datetime-local" defaultValue={localInput(offer.starts_at)}/></label>
      <label>Ends<input name="ends_at" type="datetime-local" defaultValue={localInput(offer.ends_at)}/></label>
    </div>
    <label>Description<textarea name="description" rows={4} defaultValue={offer.description||""}/></label>
    <label className="compact-row"><span><strong>Publish offer</strong><small>Visible on public pricing only while status is active.</small></span><input name="public_visible" type="checkbox" defaultChecked={offer.public_visible}/></label>
    <button className="button button-primary" disabled={state.busy}><Save size={15}/> Save offer</button>
    {state.message&&<p className="form-status">{state.message}</p>}
  </form>;
}


export function OnboardingTemplateButton({accountId}:{accountId:string}){
  const state=useSubmit();
  return <button className="button button-secondary" type="button" disabled={state.busy} onClick={()=>void state.run(()=>postJson("/api/lms/saas/crm/accounts/"+accountId+"/onboarding-template",{}))}>Create onboarding checklist</button>;
}

export function OnboardingItemCreateForm({accounts}:{accounts:Option[]}){
  const state=useSubmit();
  function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();
    const d=new FormData(event.currentTarget);
    void state.run(()=>postJson("/api/lms/saas/crm/onboarding",{
      account_id:d.get("account_id"),
      category:d.get("category"),
      title:d.get("title"),
      status:d.get("status"),
      due_at:d.get("due_at")?new Date(String(d.get("due_at"))).toISOString():null,
      notes:d.get("notes")||null,
      sort_order:Number(d.get("sort_order")||100),
    }));
  }
  return <form className="studio-form" onSubmit={submit}>
    <div className="form-grid">
      <label>Account<select name="account_id" required>{accounts.map(a=><option key={a.id} value={a.id}>{a.name}</option>)}</select></label>
      <label>Category<select name="category"><option value="commercial">Commercial</option><option value="tenant">Tenant</option><option value="identity">Identity</option><option value="data">Data</option><option value="integration">Integration</option><option value="validation">Validation</option><option value="go_live">Go-live</option><option value="success">Customer success</option><option value="general">General</option></select></label>
      <label>Title<input name="title" required/></label>
      <label>Status<select name="status"><option value="pending">Pending</option><option value="in_progress">In progress</option><option value="blocked">Blocked</option><option value="completed">Completed</option></select></label>
      <label>Due date<input name="due_at" type="datetime-local"/></label>
      <label>Sort order<input name="sort_order" type="number" defaultValue="100"/></label>
    </div>
    <label>Notes<textarea name="notes" rows={4}/></label>
    <button className="button button-primary" disabled={state.busy}><Plus size={15}/> Add onboarding task</button>
    {state.message&&<p className="form-status">{state.message}</p>}
  </form>;
}

export function OnboardingQuickActions({id,status}:{id:string;status:string}){
  const state=useSubmit();
  return <select aria-label="Onboarding status" defaultValue={status} onChange={e=>void state.run(()=>patchJson("/api/lms/saas/crm/onboarding/"+id,{status:e.target.value}))}>
    <option value="pending">Pending</option>
    <option value="in_progress">In progress</option>
    <option value="blocked">Blocked</option>
    <option value="completed">Completed</option>
  </select>;
}


export function AccountOwnerControl({accountId,ownerUserId,team}:{accountId:string;ownerUserId?:string|null;team:Array<{id:string;name:string;is_active:boolean}>}){
  const state=useSubmit();
  return <select aria-label="Account owner" defaultValue={ownerUserId||""} onChange={e=>void state.run(()=>patchJson("/api/lms/saas/crm/accounts/"+accountId,{owner_user_id:e.target.value||null}))}>
    <option value="">Unassigned</option>
    {team.filter(member=>member.is_active).map(member=><option key={member.id} value={member.id}>{member.name}</option>)}
  </select>;
}


export function ContractCreateForm(){
  const state=useSubmit();
  function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();
    const d=new FormData(event.currentTarget);
    void state.run(()=>postJson("/api/lms/saas/crm/contracts",{
      account_id:d.get("account_id"),subscription_id:d.get("subscription_id")||null,reference:d.get("reference"),
      status:d.get("status"),currency:d.get("currency"),total_value_minor:Math.round(Number(d.get("total_value")||0)*100),
      starts_at:d.get("starts_at")?new Date(String(d.get("starts_at"))).toISOString():null,
      ends_at:d.get("ends_at")?new Date(String(d.get("ends_at"))).toISOString():null,
      signed_at:d.get("signed_at")?new Date(String(d.get("signed_at"))).toISOString():null,
      renewal_terms:d.get("renewal_terms")||null,notes:d.get("notes")||null,
    }));
  }
  return <form className="studio-form" onSubmit={submit}>
    <div className="form-grid">
      <SaaSLookupSelect name="account_id" label="Account" endpoint="/api/lms/saas/crm/lookups/accounts" required />
      <SaaSLookupSelect name="subscription_id" label="Subscription" endpoint="/api/lms/saas/crm/lookups/subscriptions" placeholder="Search subscriptions (optional)" />
      <label>Contract reference<input name="reference" required/></label>
      <label>Status<select name="status"><option value="draft">Draft</option><option value="review">Review</option><option value="signed">Signed</option><option value="active">Active</option><option value="expired">Expired</option><option value="terminated">Terminated</option></select></label>
      <label>Currency<select name="currency"><option>USD</option><option>PKR</option><option>EUR</option><option>GBP</option></select></label>
      <label>Total contract value<input name="total_value" type="number" min="0" step="0.01"/></label>
      <label>Starts<input name="starts_at" type="datetime-local"/></label>
      <label>Ends<input name="ends_at" type="datetime-local"/></label>
      <label>Signed at<input name="signed_at" type="datetime-local"/></label>
    </div>
    <label>Renewal terms<textarea name="renewal_terms" rows={3}/></label>
    <label>Internal notes<textarea name="notes" rows={4}/></label>
    <button className="button button-primary" disabled={state.busy}><Plus size={15}/> Create contract</button>
    {state.message&&<p className="form-status">{state.message}</p>}
  </form>;
}

export function InvoiceCreateForm(){
  const state=useSubmit();
  function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();
    const d=new FormData(event.currentTarget);
    void state.run(()=>postJson("/api/lms/saas/crm/invoices",{
      account_id:d.get("account_id"),subscription_id:d.get("subscription_id")||null,contract_id:d.get("contract_id")||null,
      invoice_number:d.get("invoice_number"),status:d.get("status"),currency:d.get("currency"),
      amount_minor:Math.round(Number(d.get("amount")||0)*100),tax_minor:Math.round(Number(d.get("tax")||0)*100),
      issued_at:d.get("issued_at")?new Date(String(d.get("issued_at"))).toISOString():null,
      due_at:d.get("due_at")?new Date(String(d.get("due_at"))).toISOString():null,
      external_ref:d.get("external_ref")||null,notes:d.get("notes")||null,
    }));
  }
  return <form className="studio-form" onSubmit={submit}>
    <div className="form-grid">
      <SaaSLookupSelect name="account_id" label="Account" endpoint="/api/lms/saas/crm/lookups/accounts" required />
      <SaaSLookupSelect name="subscription_id" label="Subscription" endpoint="/api/lms/saas/crm/lookups/subscriptions" placeholder="Search subscriptions (optional)" />
      <SaaSLookupSelect name="contract_id" label="Contract" endpoint="/api/lms/saas/crm/lookups/contracts" placeholder="Search contracts (optional)" />
      <label>Invoice number<input name="invoice_number" required/></label>
      <label>Status<select name="status"><option value="draft">Draft</option><option value="issued">Issued</option></select></label>
      <label>Currency<select name="currency"><option>USD</option><option>PKR</option><option>EUR</option><option>GBP</option></select></label>
      <label>Amount before tax<input name="amount" type="number" min="0" step="0.01" required/></label>
      <label>Tax<input name="tax" type="number" min="0" step="0.01" defaultValue="0"/></label>
      <label>Issued at<input name="issued_at" type="datetime-local"/></label>
      <label>Due at<input name="due_at" type="datetime-local"/></label>
      <label>External reference<input name="external_ref"/></label>
    </div>
    <label>Notes<textarea name="notes" rows={4}/></label>
    <button className="button button-primary" disabled={state.busy}><Plus size={15}/> Create invoice</button>
    {state.message&&<p className="form-status">{state.message}</p>}
  </form>;
}

export function PaymentCreateForm(){
  const state=useSubmit();
  function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();
    const d=new FormData(event.currentTarget);
    void state.run(()=>postJson("/api/lms/saas/crm/payments",{
      invoice_id:d.get("invoice_id"),amount_minor:Math.round(Number(d.get("amount")||0)*100),currency:d.get("currency"),
      status:"received",received_at:d.get("received_at")?new Date(String(d.get("received_at"))).toISOString():null,
      method:d.get("method")||null,reference:d.get("reference")||null,notes:d.get("notes")||null,
    }));
  }
  return <form className="studio-form" onSubmit={submit}>
    <div className="form-grid">
      <SaaSLookupSelect name="invoice_id" label="Invoice" endpoint="/api/lms/saas/crm/lookups/invoices" placeholder="Search outstanding invoices" required />
      <label>Amount received<input name="amount" type="number" min="0.01" step="0.01" required/></label>
      <label>Currency<select name="currency"><option>USD</option><option>PKR</option><option>EUR</option><option>GBP</option></select></label>
      <label>Received at<input name="received_at" type="datetime-local"/></label>
      <label>Method<input name="method" placeholder="Bank transfer"/></label>
      <label>Reference<input name="reference"/></label>
    </div>
    <label>Notes<textarea name="notes" rows={4}/></label>
    <button className="button button-primary" disabled={state.busy}><Save size={15}/> Record payment</button>
    {state.message&&<p className="form-status">{state.message}</p>}
  </form>;
}

export function ContractStatusControl({id,status}:{id:string;status:string}){
  const state=useSubmit();
  return <select aria-label="Contract status" defaultValue={status} onChange={e=>void state.run(()=>patchJson("/api/lms/saas/crm/contracts/"+id,{status:e.target.value}))}>
    <option value="draft">Draft</option><option value="review">Review</option><option value="signed">Signed</option><option value="active">Active</option><option value="expired">Expired</option><option value="terminated">Terminated</option>
  </select>;
}

export function InvoiceStatusControl({id,status}:{id:string;status:string}){
  const state=useSubmit();
  if(["paid","partially_paid","overdue"].includes(status))return <span className="muted">System reconciled</span>;
  return <select aria-label="Invoice status" defaultValue={status} onChange={e=>void state.run(()=>patchJson("/api/lms/saas/crm/invoices/"+id,{status:e.target.value}))}>
    <option value="draft">Draft</option><option value="issued">Issued</option><option value="void">Void</option>
  </select>;
}

export function PaymentStatusControl({id,status}:{id:string;status:string}){
  const state=useSubmit();
  return <select aria-label="Payment status" defaultValue={status} onChange={e=>void state.run(()=>patchJson("/api/lms/saas/crm/payments/"+id,{status:e.target.value}))}>
    <option value="received">Received</option><option value="reversed">Reversed</option>
  </select>;
}


export function TaskCreateForm({accounts,team}:{accounts:Option[];team:Array<{id:string;name:string;is_active:boolean}>}){
  const state=useSubmit();
  function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();
    const d=new FormData(event.currentTarget);
    void state.run(()=>postJson("/api/lms/saas/crm/tasks",{
      account_id:d.get("account_id")||null,
      owner_user_id:d.get("owner_user_id")||null,
      task_type:d.get("task_type"),
      title:d.get("title"),
      description:d.get("description")||null,
      status:d.get("status"),
      priority:d.get("priority"),
      due_at:d.get("due_at")?new Date(String(d.get("due_at"))).toISOString():null,
    }));
  }
  return <form className="studio-form" onSubmit={submit}>
    <div className="form-grid">
      <label>Account<select name="account_id"><option value="">No account</option>{accounts.map(a=><option key={a.id} value={a.id}>{a.name}</option>)}</select></label>
      <label>Owner<select name="owner_user_id"><option value="">Unassigned</option>{team.filter(t=>t.is_active).map(t=><option key={t.id} value={t.id}>{t.name}</option>)}</select></label>
      <label>Task type<select name="task_type"><option value="follow_up">Follow-up</option><option value="renewal">Renewal</option><option value="trial">Trial</option><option value="proposal">Proposal</option><option value="contract">Contract</option><option value="billing">Billing</option><option value="customer_success">Customer success</option></select></label>
      <label>Status<select name="status"><option value="open">Open</option><option value="in_progress">In progress</option><option value="blocked">Blocked</option><option value="completed">Completed</option></select></label>
      <label>Priority<select name="priority"><option value="low">Low</option><option value="normal">Normal</option><option value="high">High</option><option value="urgent">Urgent</option></select></label>
      <label>Due date<input name="due_at" type="datetime-local"/></label>
    </div>
    <label>Title<input name="title" required/></label>
    <label>Description<textarea name="description" rows={4}/></label>
    <button className="button button-primary" disabled={state.busy}><Plus size={15}/> Add task</button>
    {state.message&&<p className="form-status">{state.message}</p>}
  </form>;
}

export function TaskQuickActions({id,status}:{id:string;status:string}){
  const state=useSubmit();
  return <select aria-label="Task status" defaultValue={status} onChange={e=>void state.run(()=>patchJson("/api/lms/saas/crm/tasks/"+id,{status:e.target.value}))}>
    <option value="open">Open</option><option value="in_progress">In progress</option><option value="blocked">Blocked</option><option value="completed">Completed</option>
  </select>;
}

export function GenerateRenewalTasksButton(){
  const state=useSubmit();
  return <button className="button button-secondary" type="button" disabled={state.busy} onClick={()=>void state.run(()=>postJson("/api/lms/saas/crm/tasks/generate-renewals?horizon_days=120",{}))}>Generate renewal tasks</button>;
}
