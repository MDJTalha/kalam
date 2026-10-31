import { DashboardShell } from "@/components/dashboard-shell";
import { apiJsonResult, requireUser } from "@/lib/server-api";
import { SupportOperations, type SupportCaseAdmin, type SupportMetrics, type SupportPolicy } from "@/components/support-operations";

export default async function SupportOperationsPage(){
  const user=await requireUser<{permissions?:string[]}>();
  if(!user.permissions?.includes("tenant.manage")){
    return <DashboardShell title="Support Operations" eyebrow="Platform administration"><section className="data-panel"><div className="empty-state"><h2>Support operations unavailable</h2><p>This workspace requires tenant administration permission.</p></div></section></DashboardShell>;
  }
  const [casesResult,policyResult,metricsResult]=await Promise.all([
    apiJsonResult<SupportCaseAdmin[]>("/api/v1/support/admin/cases"),
    apiJsonResult<SupportPolicy>("/api/v1/support/admin/policy"),
    apiJsonResult<SupportMetrics>("/api/v1/support/admin/metrics"),
  ]);
  const cases=casesResult.data;
  const policy=policyResult.data;
  const metrics=metricsResult.data;
  const failed=[casesResult,policyResult,metricsResult].filter(result=>!result.ok);
  return <DashboardShell title="Support Operations" eyebrow="Tenant support queue" breadcrumbs={[{label:"Administration",href:"/dashboard/admin"},{label:"Support Operations"}]}>{failed.length ? <section className="data-panel" role="alert"><h2>Support operations unavailable</h2><p>{failed.map(result=>`HTTP ${result.status}: ${result.error || "request failed"}`).join(" · ")}</p></section> : <SupportOperations initialCases={cases ?? []} initialPolicy={policy!} initialMetrics={metrics!}/>}</DashboardShell>;
}
