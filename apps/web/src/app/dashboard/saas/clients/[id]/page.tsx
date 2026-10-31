import Link from "next/link";
import { Building2, CircleDollarSign, ExternalLink, FlaskConical, Handshake, UsersRound } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { AccountOwnerControl, AccountProfileForm, ActivityCreateForm, ContactCreateForm, OnboardingQuickActions, OnboardingTemplateButton, ProvisionTenantButton } from "@/components/saas-crm-forms";
import { DataTable, EmptyState, MetricCard, SectionCard, StatusBadge } from "@/components/ui";
import { apiJsonResult } from "@/lib/server-api";

type OnboardingItem={id:string;account_id:string;category:string;title:string;status:string;due_at?:string|null;completed_at?:string|null;notes?:string|null};
type TeamMember={id:string;name:string;is_active:boolean};
type Contract={id:string;account_id:string;reference:string;status:string;currency:string;total_value_minor:number;starts_at?:string|null;ends_at?:string|null;signed_at?:string|null};
type Invoice={id:string;account_id:string;invoice_number:string;status:string;currency:string;total_minor:number;paid_minor:number;outstanding_minor:number;due_at?:string|null};
type Payment={id:string;account_id:string;invoice_id:string;amount_minor:number;currency:string;status:string;received_at:string;method?:string|null;reference?:string|null};

type AccountDetail={
  id:string;name:string;slug:string;account_type:string;lifecycle_stage:string;
  industry?:string|null;country?:string|null;website?:string|null;employee_band?:string|null;
  public_showcase:boolean;logo_url?:string|null;testimonial?:string|null;notes?:string|null;
  created_at:string;updated_at:string;
  plan?:{id:string;name:string;code:string}|null;
  managed_tenant?:{id:string;name:string;slug:string;status:string}|null;
  owner?:{id:string;name:string;email:string}|null;
  contacts:Array<{id:string;first_name:string;last_name:string;email:string;job_title?:string|null;phone?:string|null;is_primary:boolean}>;
  trials:Array<{id:string;plan_id?:string|null;status:string;seats:number;starts_at?:string|null;ends_at?:string|null}>;
  subscriptions:Array<{id:string;plan_id?:string|null;status:string;billing_cycle:string;currency:string;seats:number;list_price_minor:number;discount_minor:number;net_price_minor:number;renews_at?:string|null;contract_ref?:string|null}>;
  opportunities:Array<{id:string;name:string;stage:string;currency:string;amount_minor:number;probability_percent:number;expected_close_at?:string|null}>;
  activities:Array<{id:string;activity_type:string;subject:string;body?:string|null;happened_at:string;actor_user_id?:string|null}>;
};

function money(minor:number,currency:string){
  return new Intl.NumberFormat("en-US",{style:"currency",currency,maximumFractionDigits:minor%100===0?0:2}).format(minor/100);
}

export default async function SaaSClientDetailPage({params}:{params:Promise<{id:string}>}){
  const {id}=await params;
  const [account,onboarding,team,contracts,invoices,payments]=await Promise.all([
    apiJsonResult<AccountDetail>("/api/v1/saas/crm/accounts/"+id).then((result) => result.ok ? result.data : null),
    apiJsonResult<OnboardingItem[]>("/api/v1/saas/crm/onboarding?account_id="+encodeURIComponent(id)).then((result) => result.ok ? result.data : null),
    apiJsonResult<TeamMember[]>("/api/v1/saas/crm/team").then((result) => result.ok ? result.data : null),
    apiJsonResult<Contract[]>("/api/v1/saas/crm/contracts?account_id="+encodeURIComponent(id)).then((result) => result.ok ? result.data : null),
    apiJsonResult<Invoice[]>("/api/v1/saas/crm/invoices?account_id="+encodeURIComponent(id)).then((result) => result.ok ? result.data : null),
    apiJsonResult<Payment[]>("/api/v1/saas/crm/payments?account_id="+encodeURIComponent(id)).then((result) => result.ok ? result.data : null),
  ]);
  if(!account)return <DashboardShell title="Client record" eyebrow="SaaS CRM"><EmptyState title="Client record unavailable" description="The account was not found or this user does not have SaaS CRM access."/></DashboardShell>;

  const activeSubscription=account.subscriptions.find(item=>item.status==="active");
  const activeTrial=account.trials.find(item=>item.status==="active");
  const openOpportunities=account.opportunities.filter(item=>!["won","lost"].includes(item.stage));
  const openInvoices=(invoices||[]).filter(item=>item.outstanding_minor>0&&item.status!=="void");

  return <DashboardShell title={account.name} eyebrow="SaaS CRM · Client 360" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Clients",href:"/dashboard/saas/clients"},{label:account.name}]}>
    <SaaSCrmNav/>
    <div className="page-heading saas-spaced-section">
      <div>
        <span className="eyebrow">ACCOUNT 360</span>
        <h2>{account.name}</h2>
        <p>{[account.industry,account.country,account.employee_band].filter(Boolean).join(" · ")||"Commercial organization record"}</p>
      </div>
      <div className="page-heading-actions">
        {account.website&&<a className="button button-secondary" href={account.website} target="_blank" rel="noreferrer">Website <ExternalLink size={14}/></a>}
        <ProvisionTenantButton accountId={account.id} disabled={!!account.managed_tenant}/>
      </div>
    </div>

    <div className="stat-grid">
      <MetricCard label="Lifecycle" value={<StatusBadge status={account.lifecycle_stage}/>} detail={account.account_type} icon={Building2}/>
      <MetricCard label="Contacts" value={account.contacts.length} detail="Commercial stakeholders" icon={UsersRound}/>
      <MetricCard label="Open pipeline" value={openOpportunities.length} detail="Active opportunities" icon={Handshake}/>
      <MetricCard label="Commercial state" value={activeSubscription?"Subscribed":activeTrial?"Trial":"Pre-contract"} detail={(contracts?.length||0)+" contracts · "+openInvoices.length+" open invoices"} icon={CircleDollarSign}/>
    </div>

    <div className="two-column">
      <SectionCard eyebrow="Organization" title="Account profile"><AccountProfileForm account={account}/></SectionCard>
      <SectionCard eyebrow="Workspace linkage" title="Tenant & commercial context">
        <div className="detail-grid">
          <span><b>CRM slug</b>{account.slug}</span>
          <span><b>Lifecycle</b>{account.lifecycle_stage}</span>
          <span><b>Plan</b>{account.plan?.name||"Not assigned"}</span>
          <span><b>Owner</b><AccountOwnerControl accountId={account.id} ownerUserId={account.owner?.id} team={team||[]}/></span>
          <span><b>Tenant</b>{account.managed_tenant?.slug||"Not provisioned"}</span>
          <span><b>Tenant status</b>{account.managed_tenant?.status||"—"}</span>
          <span><b>Public showcase</b>{account.public_showcase?"Published":"Private"}</span>
          <span><b>Created</b>{new Date(account.created_at).toLocaleDateString()}</span>
        </div>
        {account.managed_tenant&&<div className="callout" style={{marginTop:14}}><Building2 size={17}/><span>Technical tenant <strong>{account.managed_tenant.name}</strong> is linked to this CRM account. Manage activation from the <Link className="text-link" href="/dashboard/saas/tenants">Tenants workspace</Link>.</span></div>}
      </SectionCard>
    </div>

    <div className="two-column">
      <SectionCard eyebrow="Stakeholders" title="Contacts" meta={account.contacts.length+" contacts"}>
        <div className="compact-list">
          {account.contacts.length?account.contacts.map(contact=><div className="compact-row" key={contact.id}><div><strong>{contact.first_name} {contact.last_name}{contact.is_primary?" · Primary":""}</strong><small>{contact.job_title||"Commercial stakeholder"}</small><small>{contact.email&&<a className="text-link" href={`mailto:${contact.email}`}>{contact.email}</a>}{contact.email&&contact.phone?" · ":""}{contact.phone&&<a className="text-link" href={`tel:${contact.phone}`}>{contact.phone}</a>}</small></div></div>):<EmptyState title="No contacts recorded" description="Add commercial stakeholders for this organization."/>}
        </div>
      </SectionCard>
      <SectionCard eyebrow="Add stakeholder" title="New contact"><ContactCreateForm accountId={account.id}/></SectionCard>
    </div>

    <SectionCard eyebrow="Pipeline" title="Opportunities" meta={account.opportunities.length+" records"}>
      <DataTable columns={["Opportunity","Stage","Value","Probability","Expected close"]} empty={<EmptyState title="No opportunities" description="Create an opportunity from the Pipeline workspace when this account enters a commercial cycle."/>} rows={account.opportunities.map(item=>[
        <strong key="a">{item.name}</strong>,
        <StatusBadge key="b" status={item.stage}/>,
        <span key="c">{money(item.amount_minor,item.currency)}</span>,
        <span key="d">{item.probability_percent}%</span>,
        <span key="e">{item.expected_close_at?new Date(item.expected_close_at).toLocaleDateString():"—"}</span>,
      ])}/>
    </SectionCard>

    <div className="two-column">
      <SectionCard eyebrow="Evaluation" title="Trials" meta={account.trials.length+" records"}>
        <div className="compact-list">{account.trials.length?account.trials.map(item=><div className="compact-row" key={item.id}><div><strong>{item.seats} seats</strong><small>{item.starts_at?new Date(item.starts_at).toLocaleDateString():"No start date"} → {item.ends_at?new Date(item.ends_at).toLocaleDateString():"No end date"}</small></div><StatusBadge status={item.status}/></div>):<EmptyState title="No trials" description="Trial records for this account will appear here." icon={FlaskConical}/>}</div>
      </SectionCard>
      <SectionCard eyebrow="Revenue" title="Subscriptions" meta={account.subscriptions.length+" records"}>
        <div className="compact-list">{account.subscriptions.length?account.subscriptions.map(item=><div className="compact-row" key={item.id}><div><strong>{money(item.net_price_minor,item.currency)} · {item.seats} seats</strong><small>{item.billing_cycle}{item.contract_ref?" · "+item.contract_ref:""}{item.renews_at?" · renews "+new Date(item.renews_at).toLocaleDateString():""}</small></div><StatusBadge status={item.status}/></div>):<EmptyState title="No subscriptions" description="Signed commercial subscriptions for this account will appear here."/>}</div>
      </SectionCard>
    </div>

    <div className="two-column">
      <SectionCard eyebrow="Commercial agreements" title="Contracts" meta={(contracts?.length||0)+" records"}>
        <div className="compact-list">{contracts?.length?contracts.map(item=><div className="compact-row" key={item.id}><div><strong>{item.reference}</strong><small>{money(item.total_value_minor,item.currency)} · {item.starts_at?new Date(item.starts_at).toLocaleDateString():"No start"} → {item.ends_at?new Date(item.ends_at).toLocaleDateString():"Open end"}</small></div><StatusBadge status={item.status}/></div>):<EmptyState title="No contracts" description="Formal commercial agreements for this account will appear here."/>}</div>
        <Link className="button button-secondary" href="/dashboard/saas/contracts">Open contracts</Link>
      </SectionCard>
      <SectionCard eyebrow="Receivables" title="Invoices & payments" meta={(invoices?.length||0)+" invoices"}>
        <div className="compact-list">{invoices?.length?invoices.slice(0,6).map(item=><div className="compact-row" key={item.id}><div><strong>{item.invoice_number} · {money(item.outstanding_minor,item.currency)} outstanding</strong><small>{money(item.total_minor,item.currency)} total · {item.due_at?"due "+new Date(item.due_at).toLocaleDateString():"no due date"}</small></div><StatusBadge status={item.status}/></div>):<EmptyState title="No invoices" description="Billing records for this account will appear here."/>}</div>
        <p className="muted">{payments?.filter(item=>item.status==="received").length||0} received payments recorded for this account.</p>
        <Link className="button button-secondary" href="/dashboard/saas/billing">Open billing</Link>
      </SectionCard>
    </div>

    <SectionCard eyebrow="Implementation readiness" title="Customer onboarding" meta={(onboarding?.length||0)+" tasks"}>
      <div className="section-actions saas-spaced-actions">{!onboarding?.length&&<OnboardingTemplateButton accountId={account.id}/>}<Link className="button button-secondary" href="/dashboard/saas/onboarding">Open onboarding board</Link></div>
      {onboarding?.length?<DataTable columns={["Task","Category","Due","Status","Update"]} empty={<EmptyState title="No onboarding tasks" description="Create the standard checklist when implementation begins."/>} rows={onboarding.map(item=>[
        <span key="a"><strong>{item.title}</strong>{item.notes&&<small>{item.notes}</small>}</span>,
        <span key="b">{item.category.replaceAll("_"," ")}</span>,
        <span key="c">{item.due_at?new Date(item.due_at).toLocaleDateString():"—"}</span>,
        <StatusBadge key="d" status={item.status}/>,
        <OnboardingQuickActions key="e" id={item.id} status={item.status}/>,
      ])}/>:<EmptyState title="No onboarding checklist yet" description="Create the standard checklist when this organization enters implementation or trial onboarding."/>}
    </SectionCard>

    <div className="two-column">
      <SectionCard eyebrow="Relationship history" title="Activity timeline" meta={account.activities.length+" activities"}>
        <div className="compact-list">{account.activities.length?account.activities.map(item=><div className="compact-row" key={item.id}><div><strong>{item.subject}</strong><small>{item.activity_type} · {new Date(item.happened_at).toLocaleString()}</small>{item.body&&<p className="muted">{item.body}</p>}</div></div>):<EmptyState title="No activity yet" description="Calls, emails, meetings, proposals and notes will build the account history here."/>}</div>
      </SectionCard>
      <SectionCard eyebrow="Log interaction" title="Add sales activity"><ActivityCreateForm accountId={account.id}/></SectionCard>
    </div>
  </DashboardShell>;
}
