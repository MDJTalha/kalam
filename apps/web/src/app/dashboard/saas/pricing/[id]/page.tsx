import Link from "next/link";
import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { PlanEditForm } from "@/components/saas-crm-forms";
import { EmptyState, SectionCard, StatusBadge } from "@/components/ui";
import { apiJson } from "@/lib/server-api";
import { formatCommercialPrice } from "@/lib/public-commercial";

type Plan={id:string;code:string;name:string;tagline?:string|null;description?:string|null;status:string;public_visible:boolean;billing_model:string;currency:string;monthly_price_minor?:number|null;annual_price_minor?:number|null;trial_days:number;minimum_seats:number;maximum_seats?:number|null;features:unknown[];limits:Record<string,unknown>;sort_order:number};

export default async function SaaSPlanDetailPage({params}:{params:Promise<{id:string}>}){
  const {id}=await params;
  const plans=await apiJson<Plan[]>("/api/v1/saas/crm/plans");
  const plan=plans?.find(item=>item.id===id);
  if(!plan)return <DashboardShell title="Commercial plan" eyebrow="SaaS CRM"><EmptyState title="Plan unavailable" description="The plan was not found or this user does not have SaaS CRM access."/></DashboardShell>;

  return <DashboardShell title={plan.name} eyebrow="SaaS CRM · Pricing" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Pricing & Offers",href:"/dashboard/saas/pricing"},{label:plan.name}]}>
    <SaaSCrmNav/>
    <div className="stat-grid saas-spaced-section">
      <div className="stat-card"><span>Status</span><strong><StatusBadge status={plan.status}/></strong><small>{plan.public_visible?"Published publicly":"Private catalogue record"}</small></div>
      <div className="stat-card"><span>Monthly</span><strong>{formatCommercialPrice(plan.monthly_price_minor,plan.currency)||"Custom"}</strong><small>{plan.billing_model.replaceAll("_"," ")}</small></div>
      <div className="stat-card"><span>Annual</span><strong>{formatCommercialPrice(plan.annual_price_minor,plan.currency)||"Custom"}</strong><small>{plan.currency}</small></div>
      <div className="stat-card"><span>Trial</span><strong>{plan.trial_days?plan.trial_days+" days":"Disabled"}</strong><small>{plan.minimum_seats} minimum seats{plan.maximum_seats?" · "+plan.maximum_seats+" maximum":""}</small></div>
    </div>
    <div className="two-column">
      <SectionCard eyebrow="Commercial control" title="Edit plan"><PlanEditForm plan={plan}/></SectionCard>
      <SectionCard eyebrow="Publishing" title="Public pricing behavior">
        <div className="compact-list">
          <div className="compact-row"><div><strong>Public visibility</strong><small>The plan appears on /pricing only when status is active and public visibility is enabled.</small></div><StatusBadge status={plan.public_visible?"published":"private"}/></div>
          <div className="compact-row"><div><strong>Trial availability</strong><small>The plan appears on /guided-evaluation only when trial days are greater than zero.</small></div><StatusBadge status={plan.trial_days>0?"active":"disabled"}/></div>
          <div className="compact-row"><div><strong>Commercial truth</strong><small>Do not publish placeholder pricing. Keep negotiated terms private in subscriptions and contracts.</small></div></div>
        </div>
        <Link className="button button-secondary" href="/pricing">Open public pricing page</Link>
      </SectionCard>
    </div>
  </DashboardShell>;
}
