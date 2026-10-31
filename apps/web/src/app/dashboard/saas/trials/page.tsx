import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { TrialCreateForm, TrialQuickActions } from "@/components/saas-crm-forms";
import { DataTable, EmptyState, SectionCard, StatusBadge } from "@/components/ui";
import { apiJsonResult } from "@/lib/server-api";

type Trial={id:string;account_id:string;account_name:string;plan_id?:string|null;plan_name?:string|null;status:string;seats:number;starts_at?:string|null;ends_at?:string|null};
export default async function SaaSTrialsPage(){
  const trials=await apiJsonResult<Trial[]>("/api/v1/saas/crm/trials").then((result) => result.ok ? result.data : null);
  if(!trials)return <DashboardShell title="Trials" eyebrow="SaaS CRM"><EmptyState title="Trial CRM access is restricted" description="This page requires authorized SaaS CRM access."/></DashboardShell>;
  return <DashboardShell title="Trials" eyebrow="SaaS CRM" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Trials"}]}>
    <SaaSCrmNav/>
    <div className="two-column saas-spaced-section">
      <SectionCard eyebrow="Trial register" title="Evaluation environments" meta={trials.length+" trials"}>
        <DataTable columns={["Account","Plan","Seats","Window","Status"]} empty={<EmptyState title="No trials yet" description="Create a governed trial when an organization is ready to evaluate Kalam."/>} rows={trials.map(t=>[
          <strong key="a">{t.account_name}</strong>,
          <span key="b">{t.plan_name||"Custom / unassigned"}</span>,
          <span key="c">{t.seats}</span>,
          <span key="d">{t.starts_at?new Date(t.starts_at).toLocaleDateString():"—"} → {t.ends_at?new Date(t.ends_at).toLocaleDateString():"—"}</span>,
          <span key="e"><StatusBadge status={t.status}/><TrialQuickActions id={t.id} status={t.status}/></span>
        ])}/>
      </SectionCard>
      <SectionCard eyebrow="New evaluation" title="Create trial"><TrialCreateForm/></SectionCard>
    </div>
  </DashboardShell>;
}
