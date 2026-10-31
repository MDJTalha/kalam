import { DashboardShell } from "@/components/dashboard-shell";
import { DeveloperSupportControl } from "@/components/saas-crm-forms";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { TenantStatusControl } from "@/components/saas-crm-forms";
import { DataTable, EmptyState, SectionCard, StatusBadge } from "@/components/ui";
import { apiJsonResult } from "@/lib/server-api";

type TenantRow={
  id:string;name:string;slug:string;status:string;user_count:number;created_at:string;
  crm_account_id?:string|null;crm_account_name?:string|null;lifecycle_stage?:string|null;
};

export default async function SaaSTenantsPage(){
  const tenants=await apiJsonResult<TenantRow[]>("/api/v1/saas/crm/tenants").then((result) => result.ok ? result.data : null);
  const supportTenants=await apiJsonResult<Array<{id:string;name:string;slug:string;status:string}>>("/api/v1/support/developer/tenants").then((result) => result.ok ? result.data : null);
  if(!tenants)return <DashboardShell title="Tenants" eyebrow="SaaS CRM"><EmptyState title="Tenant CRM access is restricted" description="This page requires authorized SaaS CRM access."/></DashboardShell>;
  return <DashboardShell title="Tenants" eyebrow="SaaS CRM" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Tenants"}]}>
    <SaaSCrmNav/>
    {supportTenants && <SectionCard eyebrow="Engineering control" title="Customer support access" meta="Platform Developer only">
      <p className="muted">Enter a time-limited, audited support session without changing the developer account&apos;s home tenant.</p>
      <DeveloperSupportControl tenants={supportTenants}/>
    </SectionCard>}
    <SectionCard eyebrow="Tenant lifecycle" title="Provisioned Kalam tenants" meta={tenants.length+" technical workspaces"}>
      <DataTable
        columns={["Tenant","CRM account","Lifecycle","Users","Created","Technical status"]}
        empty={<EmptyState title="No customer tenants provisioned" description="Provision a tenant from the Clients workspace when an approved organization is ready for a trial or deployment."/>}
        rows={tenants.map(t=>[
          <span key="a"><strong>{t.name}</strong><small>{t.slug}</small></span>,
          <span key="b">{t.crm_account_name||"Not linked"}</span>,
          t.lifecycle_stage?<StatusBadge key="c" status={t.lifecycle_stage}/>:<span key="c">—</span>,
          <span key="d">{t.user_count}</span>,
          <span key="e">{new Date(t.created_at).toLocaleDateString()}</span>,
          <span key="f"><StatusBadge status={t.status}/><TenantStatusControl id={t.id} status={t.status}/></span>
        ])}
      />
    </SectionCard>
  </DashboardShell>;
}
