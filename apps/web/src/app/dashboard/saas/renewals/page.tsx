import Link from "next/link";
import { CalendarClock, CircleDollarSign, RefreshCcw, TriangleAlert } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { GenerateRenewalTasksButton } from "@/components/saas-crm-forms";
import { DataTable, EmptyState, MetricCard, SectionCard, StatusBadge } from "@/components/ui";
import { apiJsonResult } from "@/lib/server-api";

type Renewal={
  subscription_id:string;account_id:string;account_name:string;plan_id?:string|null;plan_name?:string|null;
  currency:string;net_price_minor:number;billing_cycle:string;seats:number;renews_at:string;
  contract_ref?:string|null;days_until_renewal:number|null;
};

function money(minor:number,currency:string){
  return new Intl.NumberFormat("en-US",{style:"currency",currency,maximumFractionDigits:minor%100===0?0:2}).format(minor/100);
}

export default async function SaaSRenewalsPage(){
  const renewals=await apiJsonResult<Renewal[]>("/api/v1/saas/crm/renewals?days=180").then((result) => result.ok ? result.data : null);
  if(!renewals)return <DashboardShell title="Renewals" eyebrow="SaaS CRM"><EmptyState title="Renewal CRM access is restricted" description="This page requires authorized SaaS CRM access."/></DashboardShell>;

  const overdue=renewals.filter(r=>(r.days_until_renewal??9999)<0).length;
  const next30=renewals.filter(r=>(r.days_until_renewal??9999)>=0&&(r.days_until_renewal??9999)<=30).length;
  const next90=renewals.filter(r=>(r.days_until_renewal??9999)>30&&(r.days_until_renewal??9999)<=90).length;
  const later=renewals.filter(r=>(r.days_until_renewal??9999)>90).length;

  return <DashboardShell title="Renewals" eyebrow="SaaS CRM" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Renewals"}]}>
    <SaaSCrmNav/>
    <div className="stat-grid saas-spaced-section">
      <MetricCard label="Overdue" value={overdue} detail="Renewal date has passed" icon={TriangleAlert}/>
      <MetricCard label="Next 30 days" value={next30} detail="Immediate renewal attention" icon={CalendarClock}/>
      <MetricCard label="31–90 days" value={next90} detail="Prepare renewal conversation" icon={RefreshCcw}/>
      <MetricCard label="91–180 days" value={later} detail="Longer-horizon renewals" icon={CircleDollarSign}/>
    </div>
    <SectionCard eyebrow="Renewal horizon" title="Active subscriptions renewing within 180 days" meta={renewals.length+" records"}>
      <div className="section-actions saas-spaced-actions"><GenerateRenewalTasksButton/><Link className="button button-secondary" href="/dashboard/saas/tasks?type=renewal">Open renewal tasks</Link></div>
      <DataTable caption="Subscription renewal horizon"
        columns={["Account","Plan","Contract value","Cycle","Seats","Renewal date","Timing"]}
        empty={<EmptyState title="No renewals in this horizon" description="Active subscriptions with a configured renewal date will appear here."/>}
        rows={renewals.map(item=>[
          <Link className="text-link" href={"/dashboard/saas/clients/"+item.account_id} key="a">{item.account_name}</Link>,
          <span key="b">{item.plan_name||"Custom"}{item.contract_ref&&<small>{item.contract_ref}</small>}</span>,
          <strong key="c">{money(item.net_price_minor,item.currency)}</strong>,
          <span key="d">{item.billing_cycle}</span>,
          <span key="e">{item.seats}</span>,
          <span key="f">{new Date(item.renews_at).toLocaleDateString()}</span>,
          <StatusBadge key="g" status={(item.days_until_renewal??0)<0?"overdue":(item.days_until_renewal??0)<=30?"due_soon":"scheduled"}/>
        ])}
      />
      <p className="muted">This view shows contracted subscription values and renewal dates. It does not label values as ARR/MRR unless revenue-normalization rules are formally configured.</p>
    </SectionCard>
  </DashboardShell>;
}
