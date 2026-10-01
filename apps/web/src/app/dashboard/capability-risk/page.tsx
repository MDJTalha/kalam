import { DashboardShell } from "@/components/dashboard-shell";
import { CapabilityRiskWorkspace } from "@/components/capability-risk-workspace";
import { apiJsonResult, requireUser } from "@/lib/server-api";
import { ShieldAlert } from "lucide-react";
import { StateMessage } from "@/components/ui";

type Risk={capability_id:string;capability:string;risk_score:number;risk_level:string;affected_people:number;affected_roles:number;critical_roles_affected:number;evidence_count:number;development_active_count:number;certification_expiring_count:number;dimensions:Record<string,number>;explanation:{reasons:string[];impact:string;action:string;weights:Record<string,number>};calculation_version:string};
export default async function CapabilityRiskPage(){
 const user=await requireUser<{permissions?:string[]}>(); const permissions=user.permissions||[];
 const canManage=permissions.includes("capability_risk.manage");
 if(!permissions.includes("capability_risk.read")&&!canManage)return <DashboardShell title="Capability Risk" eyebrow="Capability intelligence"><section className="data-panel"><ShieldAlert size={22}/><h2>Access restricted</h2><p>Your role does not have access to capability risk intelligence.</p></section></DashboardShell>; const result=await apiJsonResult<Risk[]>("/api/v1/capability-risks");
 return <DashboardShell title="Capability Risk" eyebrow="Capability intelligence" breadcrumbs={[{label:"Overview",href:"/dashboard"},{label:"Capability Risk"}]}>
   {!result.ok
     ? <StateMessage tone="danger" title="Capability risk intelligence is unavailable">The risk calculation service could not be loaded. No risk value is shown as zero. Refresh the workspace or check the service status before acting on risk signals.</StateMessage>
     : <CapabilityRiskWorkspace initialRisks={result.data ?? []} canManage={canManage}/>}
 </DashboardShell>;
}
