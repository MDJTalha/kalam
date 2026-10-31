import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { OpportunityCreateForm, OpportunityQuickActions } from "@/components/saas-crm-forms";
import { DataTable, EmptyState, SectionCard, StatusBadge } from "@/components/ui";
import { apiJsonResult } from "@/lib/server-api";

type Opportunity={id:string;account_id:string;account_name:string;name:string;stage:string;currency:string;amount_minor:number;probability_percent:number;expected_close_at?:string|null};
type Forecast={currency:string;stage:string;gross_amount_minor:number;weighted_amount_minor:number;opportunities:number};

function money(minor:number,currency:string){return new Intl.NumberFormat("en-US",{style:"currency",currency,maximumFractionDigits:minor%100===0?0:2}).format(minor/100);}

export default async function SaaSPipelinePage(){
  const [opportunities,forecast]=await Promise.all([
    apiJsonResult<Opportunity[]>("/api/v1/saas/crm/opportunities").then((result) => result.ok ? result.data : null),
    apiJsonResult<Forecast[]>("/api/v1/saas/crm/forecast").then((result) => result.ok ? result.data : null),
  ]);
  if(!opportunities||!forecast)return <DashboardShell title="Pipeline" eyebrow="SaaS CRM"><EmptyState title="Pipeline CRM access is restricted" description="This page requires authorized SaaS CRM access."/></DashboardShell>;
  const open=opportunities.filter(o=>!["won","lost"].includes(o.stage));
  return <DashboardShell title="Pipeline" eyebrow="SaaS CRM" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Pipeline"}]}>
    <SaaSCrmNav/>
    <div className="stat-grid saas-spaced-section">
      <div className="stat-card"><span>Open opportunities</span><strong>{open.length}</strong><small>Active commercial conversations</small></div>
      <div className="stat-card"><span>Won</span><strong>{opportunities.filter(o=>o.stage==="won").length}</strong><small>Converted opportunities</small></div>
      <div className="stat-card"><span>Proposal+</span><strong>{open.filter(o=>["proposal","negotiation"].includes(o.stage)).length}</strong><small>Late-stage pipeline</small></div>
      <div className="stat-card"><span>Weighted records</span><strong>{open.filter(o=>o.probability_percent>0).length}</strong><small>Probability configured</small></div>
    </div>
    <SectionCard eyebrow="Forecast" title="Probability-weighted pipeline by currency and stage">
      <div className="compact-list">{forecast.length?forecast.map(item=><div className="compact-row" key={item.currency+"-"+item.stage}><div><strong>{money(item.weighted_amount_minor,item.currency)} weighted</strong><small>{money(item.gross_amount_minor,item.currency)} gross · {item.opportunities} opportunities · {item.stage}</small></div><StatusBadge status={item.stage}/></div>):<EmptyState title="No open forecast" description="Open opportunities with values and probability will appear here."/>}</div>
      <p className="muted">Forecast is probability-weighted and kept separate by currency. It is a sales planning view, not recognized revenue.</p>
    </SectionCard>
    <SectionCard eyebrow="Opportunity register" title="Sales pipeline" meta={opportunities.length+" opportunities"}>
      <DataTable caption="Sales pipeline opportunities" columns={["Opportunity","Account","Value","Probability","Expected close","Stage"]} empty={<EmptyState title="No opportunities yet" description="Create the first qualified commercial opportunity from a CRM account."/>} rows={opportunities.map(o=>[
        <strong key="a">{o.name}</strong>,
        <span key="b">{o.account_name}</span>,
        <span key="c">{money(o.amount_minor,o.currency)}</span>,
        <span key="d">{o.probability_percent}%</span>,
        <span key="e">{o.expected_close_at?new Date(o.expected_close_at).toLocaleDateString():"—"}</span>,
        <span key="f"><StatusBadge status={o.stage}/><OpportunityQuickActions id={o.id} stage={o.stage}/></span>
      ])}/>
    </SectionCard>
    <SectionCard eyebrow="New opportunity" title="Add pipeline opportunity"><OpportunityCreateForm/></SectionCard>
  </DashboardShell>;
}
