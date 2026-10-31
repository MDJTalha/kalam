import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Building2 } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { ManagedTenantUsersPanel } from "@/components/managed-tenant-users-panel";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { EmptyState, SectionCard, StateMessage, StatusBadge } from "@/components/ui";
import { apiJson, apiJsonResult, requireUser } from "@/lib/server-api";

type TenantRow={
  id:string;name:string;slug:string;status:string;user_count:number;
  crm_account_id?:string|null;crm_account_name?:string|null;lifecycle_stage?:string|null;
};
type CustomerUser={
  id:string;email:string;first_name:string;last_name:string;job_title?:string|null;
  is_active:boolean;locked:boolean;last_login_at?:string|null;
  roles:Array<{id:string;name:string;role_kind:string}>;
};
type Role={id:string;name:string;role_kind:string;description?:string|null};

export default async function SaaSTenantUsersPage({params}:{params:Promise<{id:string}>}) {
  const user=await requireUser<{permissions?:string[]}>();
  const permissions=user.permissions??[];
  const canRead=permissions.includes("saas.customer_users.read");
  const canManage=permissions.includes("saas.customer_success.manage");
  const canManageRoles=permissions.includes("saas.roles.manage");
  if(!canRead)return <DashboardShell title="Customer user access" eyebrow="SaaS Customer Success"><EmptyState title="Customer user access is restricted" description="Only Customer Success and SaaS Super Admin roles can view customer employee accounts."/></DashboardShell>;
  const {id}=await params;
  const tenants=await apiJson<TenantRow[]>("/api/v1/saas/crm/tenants");
  const tenant=tenants?.find(item=>item.id===id);
  if(!tenant)notFound();
  const [usersResult,rolesResult]=await Promise.all([
    apiJsonResult<CustomerUser[]>(`/api/v1/saas/crm/tenants/${id}/users`),
    canManageRoles?apiJsonResult<Role[]>(`/api/v1/saas/crm/tenants/${id}/roles`):Promise.resolve({ok:true as const,status:200,data:[],error:null}),
  ]);
  if(usersResult.status===404)notFound();
  if(!usersResult.ok||!usersResult.data)return <DashboardShell title="Customer user access" eyebrow="SaaS Customer Success"><StateMessage tone="danger" title="Customer user records are unavailable">{usersResult.error||"Unable to load customer users."}</StateMessage></DashboardShell>;
  if(canManageRoles&&!rolesResult.ok)return <DashboardShell title="Customer user access" eyebrow="SaaS governance"><StateMessage tone="danger" title="Tenant role definitions are unavailable">{rolesResult.error||"Unable to load tenant role definitions."}</StateMessage></DashboardShell>;

  return <DashboardShell title="Customer user access" eyebrow="SaaS Customer Success" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Tenants",href:"/dashboard/saas/tenants"},{label:tenant.name}]}>
    <SaaSCrmNav/>
    <div className="page-heading">
      <div><span className="eyebrow">Customer tenant</span><h2>{tenant.name}</h2><p>{tenant.slug} · {tenant.user_count} user records · <StatusBadge status={tenant.status}/></p></div>
      <div className="page-heading-actions"><Link className="button button-secondary" href="/dashboard/saas/tenants"><ArrowLeft size={14}/> Back to tenants</Link></div>
    </div>
    <SectionCard eyebrow="Account relationship" title="Customer organization">
      <div className="detail-grid">
        <span><b>CRM account</b>{tenant.crm_account_name||"Not linked"}</span>
        <span><b>Lifecycle stage</b>{tenant.lifecycle_stage||"—"}</span>
        <span><b>Technical status</b><StatusBadge status={tenant.status}/></span>
        <span><b>User count</b>{tenant.user_count}</span>
      </div>
    </SectionCard>
    <ManagedTenantUsersPanel tenantId={tenant.id} initialUsers={usersResult.data} roles={rolesResult.data??[]} canManage={canManage} canManageRoles={canManageRoles}/>
    {canManageRoles&&<div className="form-actions"><Link className="button button-secondary" href="/dashboard/saas/roles"><Building2 size={14}/> Open tenant role governance</Link></div>}
  </DashboardShell>;
}
