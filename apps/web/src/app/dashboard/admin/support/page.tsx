import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetch, apiJson, requireUser } from "@/lib/server-api";
import { SupportOperations, type SupportCaseAdmin, type SupportMetrics, type SupportPolicy } from "@/components/support-operations";

export default async function SupportOperationsPage(){
  const user=await requireUser<{permissions?:string[]}>();
  if(!user.permissions?.includes("tenant.manage")){
    return <DashboardShell title="Support Operations" eyebrow="Platform administration"><section className="data-panel"><div className="empty-state"><h2>Support operations unavailable</h2><p>This workspace requires tenant administration permission.</p></div></section></DashboardShell>;
  }
  const [response,policyResult,metricsResult]=await Promise.all([
    apiFetch("/api/v1/support/admin/cases"),
    apiJsonResult<SupportPolicy>("/api/v1/support/admin/policy"),
    apiJsonResult<SupportMetrics>("/api/v1/support/admin/metrics"),
  ]);
  const cases=response.ok?await response.json() as SupportCaseAdmin[]:null;
  return <DashboardShell title="Support Operations" eyebrow="Tenant support queue" breadcrumbs={[{label:"Administration",href:"/dashboard/admin"},{label:"Support Operations"}]}>{cases===null ? <section className="data-panel" role="alert"><h2>Support queue unavailable</h2><p>The support queue could not be loaded. Refresh and try again before making an operational decision.</p></section> : <SupportOperations initialCases={cases} initialPolicy={policy} initialMetrics={metrics}/>}</DashboardShell>;
}
