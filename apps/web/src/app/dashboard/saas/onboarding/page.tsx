import Link from "next/link";
import { AlertTriangle, CheckCircle2, CircleDot, LoaderCircle } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { OnboardingItemCreateForm, OnboardingQuickActions } from "@/components/saas-crm-forms";
import { DataTable, EmptyState, MetricCard, SectionCard, StatusBadge } from "@/components/ui";
import { apiJson } from "@/lib/server-api";

type Item={
  id:string;account_id:string;account_name:string;managed_tenant_id?:string|null;owner_user_id?:string|null;
  category:string;title:string;status:string;due_at?:string|null;completed_at?:string|null;
  notes?:string|null;sort_order:number;created_at:string;
};

async function requestTimestamp():Promise<number>{
  return Date.now();
}

export default async function SaaSOnboardingPage(){
  const items=await apiJson<Item[]>("/api/v1/saas/crm/onboarding");
  if(!items)return <DashboardShell title="Onboarding" eyebrow="SaaS CRM"><EmptyState title="Onboarding CRM access is restricted" description="This page requires authorized SaaS CRM access."/></DashboardShell>;

  const now=await requestTimestamp();
  const pending=items.filter(i=>i.status==="pending").length;
  const inProgress=items.filter(i=>i.status==="in_progress").length;
  const blocked=items.filter(i=>i.status==="blocked").length;
  const overdue=items.filter(i=>i.status!=="completed"&&i.due_at&&new Date(i.due_at).getTime()<now).length;

  return <DashboardShell title="Onboarding" eyebrow="SaaS CRM" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Onboarding"}]}>
    <SaaSCrmNav/>
    <div className="stat-grid saas-spaced-section">
      <MetricCard label="Pending" value={pending} detail="Not started" icon={CircleDot}/>
      <MetricCard label="In progress" value={inProgress} detail="Active onboarding work" icon={LoaderCircle}/>
      <MetricCard label="Blocked" value={blocked} detail="Needs intervention" icon={AlertTriangle}/>
      <MetricCard label="Overdue" value={overdue} detail="Past due and incomplete" icon={CheckCircle2}/>
    </div>

    <SectionCard eyebrow="Customer onboarding" title="Implementation checklist" meta={items.length+" tasks"}>
      <DataTable
        columns={["Account","Task","Category","Due","Status","Update"]}
        empty={<EmptyState title="No onboarding tasks yet" description="Create a standard checklist from a client record or add an individual onboarding task here."/>}
        rows={items.map(item=>[
          <Link className="text-link" href={"/dashboard/saas/clients/"+item.account_id} key="a">{item.account_name}</Link>,
          <span key="b"><strong>{item.title}</strong>{item.notes&&<small>{item.notes}</small>}</span>,
          <span key="c">{item.category.replaceAll("_"," ")}</span>,
          <span key="d">{item.due_at?new Date(item.due_at).toLocaleDateString():"—"}</span>,
          <StatusBadge key="e" status={item.status}/>,
          <OnboardingQuickActions key="f" id={item.id} status={item.status}/>
        ])}
      />
    </SectionCard>

    <SectionCard eyebrow="Add task" title="Create onboarding item">
      <OnboardingItemCreateForm />
    </SectionCard>
  </DashboardShell>;
}
