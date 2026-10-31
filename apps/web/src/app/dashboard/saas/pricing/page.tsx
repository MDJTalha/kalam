import Link from "next/link";
import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { OfferCreateForm, OfferEditForm, PlanCreateForm, PlanQuickActions } from "@/components/saas-crm-forms";
import { DataTable, EmptyState, SectionCard, StatusBadge } from "@/components/ui";
import { apiJsonResult } from "@/lib/server-api";
import { formatCommercialPrice } from "@/lib/public-commercial";

type Plan={id:string;code:string;name:string;tagline?:string|null;status:string;public_visible:boolean;billing_model:string;currency:string;monthly_price_minor?:number|null;annual_price_minor?:number|null;trial_days:number;minimum_seats:number;maximum_seats?:number|null};
type Offer={id:string;plan_id?:string|null;code:string;title:string;description?:string|null;discount_type:string;discount_value:number;status:string;public_visible:boolean;starts_at?:string|null;ends_at?:string|null};

export default async function SaaSPricingPage(){
  const [plans,offers]=await Promise.all([
    apiJsonResult<Plan[]>("/api/v1/saas/crm/plans").then((result) => result.ok ? result.data : null),
    apiJsonResult<Offer[]>("/api/v1/saas/crm/offers").then((result) => result.ok ? result.data : null),
  ]);
  if(!plans||!offers)return <DashboardShell title="Pricing & Offers" eyebrow="SaaS CRM"><EmptyState title="Pricing CRM access is restricted" description="This page requires authorized SaaS CRM access."/></DashboardShell>;
  const options=plans.map(p=>({id:p.id,name:p.name}));
  return <DashboardShell title="Pricing & Offers" eyebrow="SaaS CRM" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Pricing & Offers"}]}>
    <SaaSCrmNav/>
    <SectionCard eyebrow="Plan catalogue" title="SaaS plans" meta={plans.length+" plans"}>
      <DataTable columns={["Plan","Pricing","Trial","Status","Public","Actions"]} empty={<EmptyState title="No SaaS plans yet" description="Create a plan before publishing pricing or enabling trial access."/>} rows={plans.map(p=>[
        <span key="a"><strong><Link className="text-link" href={"/dashboard/saas/pricing/"+p.id}>{p.name}</Link></strong><small>{p.code} · {p.billing_model.replaceAll("_"," ")}</small></span>,
        <span key="b"><strong>{formatCommercialPrice(p.monthly_price_minor,p.currency)||"Custom"}</strong><small>{formatCommercialPrice(p.annual_price_minor,p.currency)?formatCommercialPrice(p.annual_price_minor,p.currency)+" annual":"No annual price"}</small></span>,
        <span key="c">{p.trial_days?p.trial_days+" days":"No public trial"}</span>,
        <StatusBadge key="d" status={p.status}/>,
        <StatusBadge key="e" status={p.public_visible?"published":"private"}/>,
        <PlanQuickActions key="f" id={p.id} publicVisible={p.public_visible} status={p.status}/>
      ])}/>
    </SectionCard>
    <div className="two-column">
      <SectionCard eyebrow="Commercial setup" title="Create plan"><PlanCreateForm/></SectionCard>
      <SectionCard eyebrow="Discounts & campaigns" title="Create offer"><OfferCreateForm plans={options}/></SectionCard>
    </div>
    <SectionCard eyebrow="Offer register" title="Discounts and offers" meta={offers.length+" offers"}>
      {offers.length?<div className="compact-list">{offers.map(o=><details className="data-panel" key={o.id}><summary className="compact-row"><div><strong>{o.title}</strong><small>{o.code} · {o.plan_id?plans.find(p=>p.id===o.plan_id)?.name||"Assigned plan":"All / negotiated"} · {o.discount_type==="percent"?o.discount_value+"%":o.discount_value+" minor units"}</small></div><span><StatusBadge status={o.status}/> <StatusBadge status={o.public_visible?"published":"private"}/></span></summary><OfferEditForm offer={o}/></details>)}</div>:<EmptyState title="No offers configured" description="Offers can be private negotiated incentives or published campaigns."/>}
    </SectionCard>
  </DashboardShell>;
}
