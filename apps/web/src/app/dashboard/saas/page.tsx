import Link from "next/link";
import { AlertTriangle, Building2, CircleDollarSign, ClipboardCheck, FlaskConical, Handshake, ReceiptText, ShieldCheck, UsersRound } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { EmptyState, MetricCard, SectionCard } from "@/components/ui";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type Overview={accounts:number;customers:number;active_trials:number;scheduled_trials:number;active_subscriptions:number;open_tasks:number;overdue_tasks:number;overdue_invoices:number;pipeline_by_currency:Array<{currency:string;amount_minor:number;opportunities:number}>;subscriptions_by_currency_cycle:Array<{currency:string;billing_cycle:string;net_value_minor:number;subscriptions:number}>};
type CurrentUser={roles?:Array<{name:string}>;permissions?:string[]};

export default async function SaaSOverviewPage(){
  const user=await requireUser<CurrentUser>();
  const readOnlyRole=(user.roles??[]).map(role=>role.name.trim().toLowerCase()).find(role=>["saas owner","sales viewer"].includes(role));
  const isSaaSReadOnly=Boolean(readOnlyRole);
  if(!user.permissions?.includes("saas.crm.read")){
    return <DashboardShell title="SaaS Operations" eyebrow="Kalam commercial control"><EmptyState title="SaaS CRM access is restricted" description="This workspace is available only to authorized Kalam operations users."/></DashboardShell>;
  }
  const overviewResult=await apiJsonResult<Overview>("/api/v1/saas/crm/overview");
  if(overviewResult.status===403){
    return <DashboardShell title="SaaS Operations" eyebrow="Kalam commercial control"><EmptyState title="SaaS CRM access is restricted" description="Your current permissions do not allow access to commercial operations data."/></DashboardShell>;
  }
  if(!overviewResult.ok||!overviewResult.data){
    return <DashboardShell title="SaaS Operations" eyebrow="Kalam commercial control"><EmptyState title="SaaS operations data unavailable" description={`The commercial operations service could not be loaded (HTTP ${overviewResult.status}). Refresh the workspace or contact an administrator if the problem persists.`}/></DashboardShell>;
  }
  const overview=overviewResult.data;
  return <DashboardShell title="SaaS Operations" eyebrow="Kalam commercial control" breadcrumbs={[{label:"SaaS Operations"}]}>
    <SaaSCrmNav readOnly={isSaaSReadOnly}/>
    {isSaaSReadOnly&&<p className="muted">{readOnlyRole==="saas owner"?"SaaS Owner":"Sales Viewer"} view: commercial portfolio and performance are visible; CRM changes, tenant lifecycle operations and technical support controls are reserved for separately authorized roles.</p>}
    <div className="stat-grid saas-spaced-section">
      <MetricCard label="CRM accounts" value={overview.accounts} detail="Prospects, clients and partners" icon={Building2}/>
      <MetricCard label="Customers" value={overview.customers} detail="Lifecycle stage: customer" icon={UsersRound}/>
      <MetricCard label="Active trials" value={overview.active_trials} detail={overview.scheduled_trials+" scheduled evaluations"} icon={FlaskConical}/>
      <MetricCard label="Subscriptions" value={overview.active_subscriptions} detail="Active commercial agreements" icon={CircleDollarSign}/>
    </div>
    <div className="stat-grid">
      <MetricCard label="Open tasks" value={overview.open_tasks} detail="Commercial follow-up work" icon={ClipboardCheck}/>
      <MetricCard label="Overdue tasks" value={overview.overdue_tasks} detail="Past due and incomplete" icon={AlertTriangle}/>
      <MetricCard label="Overdue invoices" value={overview.overdue_invoices} detail="Receivables requiring attention" icon={ReceiptText}/>
      <MetricCard label="Operating focus" value={overview.overdue_tasks+overview.overdue_invoices} detail="Immediate task + receivables risk" icon={AlertTriangle}/>
    </div>
    <div className="two-column">
      <SectionCard eyebrow="Commercial pipeline" title="Open pipeline by currency" meta="Currencies are never mixed into one total">
        <div className="compact-list">{overview.pipeline_by_currency.length?overview.pipeline_by_currency.map(item=><div className="compact-row" key={item.currency}><div><strong>{new Intl.NumberFormat("en-US",{style:"currency",currency:item.currency,maximumFractionDigits:item.amount_minor%100===0?0:2}).format(item.amount_minor/100)}</strong><small>{item.opportunities} open opportunities · {item.currency}</small></div></div>):<div className="empty-state"><p>No open opportunities yet.</p></div>}</div>
        <p className="muted">Pipeline values remain grouped by currency to avoid misleading cross-currency totals.</p>
        {!isSaaSReadOnly&&<Link className="button button-secondary" href="/dashboard/saas/pipeline"><Handshake size={15}/> Open pipeline</Link>}
      </SectionCard>
      <SectionCard eyebrow="Publishing governance" title="Public website controls">
        <div className="compact-list">
          {!isSaaSReadOnly&&<div className="compact-row"><div><strong>Pricing</strong><small>Only active plans marked public are shown.</small></div><Link className="text-link" href="/dashboard/saas/pricing">Manage</Link></div>}
          <div className="compact-row"><div><strong>Clients</strong><small>Only customer-stage accounts with public showcase enabled are shown.</small></div>{isSaaSReadOnly?<Link className="text-link" href="/dashboard/saas/tenants">View portfolio</Link>:<Link className="text-link" href="/dashboard/saas/clients">Manage</Link>}</div>
          {!isSaaSReadOnly&&<div className="compact-row"><div><strong>Certifications</strong><small>Only registered/active records explicitly published are shown.</small></div><Link className="text-link" href="/dashboard/saas/certifications">Manage</Link></div>}
        </div>
      </SectionCard>
    </div>
    <SectionCard eyebrow="Revenue visibility" title="Active subscription value by currency and billing cycle">
      <div className="compact-list">{overview.subscriptions_by_currency_cycle.length?overview.subscriptions_by_currency_cycle.map(item=><div className="compact-row" key={item.currency+"-"+item.billing_cycle}><div><strong>{new Intl.NumberFormat("en-US",{style:"currency",currency:item.currency,maximumFractionDigits:item.net_value_minor%100===0?0:2}).format(item.net_value_minor/100)}</strong><small>{item.subscriptions} active subscriptions · {item.billing_cycle} · {item.currency}</small></div></div>):<div className="empty-state"><p>No active subscriptions yet.</p></div>}</div>
      <p className="muted">These are contracted values grouped by billing cycle; they are not presented as ARR or MRR until normalization rules are formally configured.</p>
    </SectionCard>
    <SectionCard eyebrow="Commercial architecture" title="Operator-plane principles">
      <div className="three-column">
        <div className="soft-panel"><ShieldCheck size={18}/><h3>Separated from customer admin</h3><p>CRM records live in the Kalam operations tenant rather than inside client tenant administration.</p></div>
        <div className="soft-panel"><Building2 size={18}/><h3>Tenant linkage without leakage</h3><p>CRM accounts can reference managed tenants while commercial records remain operations-scoped.</p></div>
        <div className="soft-panel"><CircleDollarSign size={18}/><h3>Public publishing is explicit</h3><p>Plans, clients, offers and certifications do not appear publicly unless approved and published.</p></div>
      </div>
    </SectionCard>
  </DashboardShell>;
}
