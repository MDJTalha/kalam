import Link from "next/link";
import { DashboardShell } from "@/components/dashboard-shell";
import { AdminCenter } from "@/components/admin-center";
import { StateMessage } from "@/components/ui";
import { apiJsonResult, requireUser } from "@/lib/server-api";
type Role={id:string;name:string;description?:string|null;role_kind?:string};type OrgUnit={id:string;name:string;unit_type:string;code?:string|null;parent_id?:string|null};type Person={id:string;first_name:string;last_name:string;email:string;job_title?:string|null;is_active:boolean};type PeoplePage={items:Person[];total:number;tenant_total:number};type Tenant={id:string;name:string;slug:string;status:string;settings:Record<string,unknown>};type CurrentUser={permissions?:string[];roles?:Array<{name:string}>};
type SupportContext={active:boolean;tenant_id?:string;tenant_name?:string;expires_at?:string};
export default async function AdminPage(){
  const currentUser=await requireUser<CurrentUser>();
  const roleIsDeveloper=currentUser.roles?.some(role=>role.name.trim().toLowerCase()==="platform developer")??false;
  const supportContext=await apiJsonResult<SupportContext>("/api/v1/support/developer/support/current");
  const isPlatformDeveloper=roleIsDeveloper||(supportContext.ok&&supportContext.data?.active===true);
  const [tenant,roles,units,people]=await Promise.all([
    apiJsonResult<Tenant>("/api/v1/admin/tenant-settings"),
    apiJsonResult<Role[]>("/api/v1/organization/roles"),
    apiJsonResult<OrgUnit[]>("/api/v1/admin/org-units"),
    apiJsonResult<PeoplePage>("/api/v1/people/page?page=1&page_size=50"),
  ]);
  if(tenant.status===403)return <DashboardShell title="Administration" eyebrow="Tenant control"><StateMessage tone="warning" title="Administration access is restricted">Your role does not have permission to view tenant administration.</StateMessage></DashboardShell>;
  const failures=[tenant,roles,units,people].flatMap(result=>result.ok?[]:[`HTTP ${result.status}: ${result.error||"request failed"}`]);
  if(failures.length)return <DashboardShell title="Administration" eyebrow="Tenant control"><StateMessage tone="danger" title="Administration data is incomplete">{failures.join(" · ")} Refresh after the failed services are available. No partially loaded administration controls are shown.</StateMessage></DashboardShell>;
  if(!tenant.data)return <DashboardShell title="Administration" eyebrow="Tenant control"><StateMessage tone="danger" title="Tenant settings unavailable">The administration service returned an empty tenant record.</StateMessage></DashboardShell>;
  const inquiries=isPlatformDeveloper?await apiJsonResult<unknown[]>("/api/v1/marketing/inquiries?limit=1"):null;
  return <DashboardShell title="Administration" eyebrow="Tenant control">{inquiries?.ok&&<div className="data-panel"><h2>Demo requests</h2><p>Review inquiries from organizations evaluating Kalam.</p><Link href="/dashboard/admin/inquiries">Open the review queue</Link></div>}<AdminCenter tenant={tenant.data} roles={roles.data??[]} units={units.data??[]} people={people.data?.items??[]} peopleTotal={people.data?.tenant_total??0} accessPermissions={currentUser.permissions??[]} isPlatformDeveloper={isPlatformDeveloper}/></DashboardShell>;
}
