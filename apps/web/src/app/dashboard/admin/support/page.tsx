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
  const ready = casesResult.ok && casesResult.data !== null && policyResult.ok && policyResult.data !== null && metricsResult.ok && metricsResult.data !== null;
  const failed = [casesResult, policyResult, metricsResult].filter(result => !result.ok || result.data === null);
  return <DashboardShell title="Support Operations" eyebrow="Tenant support queue" breadcrumbs={[{label:"Administration",href:"/dashboard/admin"},{label:"Support Operations"}]}>{!ready ? <section className="data-panel" role="alert"><h2>{failed.some(result => result.status === 403) ? "Support operations access restricted" : failed.some(result => result.status === 0 || result.status >= 500) ? "Support operations service unavailable" : "Support operations data incomplete"}</h2><p>Cases: HTTP {casesResult.status}; policy: HTTP {policyResult.status}; metrics: HTTP {metricsResult.status}. {failed.map(result => result.error).filter(Boolean).join(" · ") || "Refresh and try again before making an operational decision."}</p></section> : <SupportOperations initialCases={casesResult.data!} initialPolicy={policyResult.data!} initialMetrics={metricsResult.data!}/>}</DashboardShell>;
}
