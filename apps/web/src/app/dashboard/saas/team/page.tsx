import { UserRoundCog, UsersRound } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { DataTable, EmptyState, MetricCard, SectionCard, StatusBadge } from "@/components/ui";
import { apiJsonResult } from "@/lib/server-api";

type TeamMember={
  id:string;name:string;email:string;job_title?:string|null;is_active:boolean;roles:string[];
};

export default async function SaaSTeamPage(){
  const result=await apiJsonResult<TeamMember[]>("/api/v1/saas/crm/team");
  if(!result.ok || !result.data) return <DashboardShell title="Sales Team" eyebrow="SaaS CRM"><EmptyState title={result.status===403?"SaaS team access is restricted":result.status===0 || result.status>=500?"SaaS team service unavailable":"SaaS team data could not be loaded"} description={result.error || `The team request failed with HTTP ${result.status}. The failed response is not treated as an empty team.`}/></DashboardShell>;
  const team=result.data;

  const active=team.filter(member=>member.is_active);
  const operators=team.filter(member=>member.roles.some(role=>["SaaS Administrator","Sales Operations","Sales Viewer"].includes(role)));

  return <DashboardShell title="Sales Team" eyebrow="SaaS CRM" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Sales Team"}]}>
    <SaaSCrmNav/>
    <div className="stat-grid saas-spaced-section">
      <MetricCard label="Operations users" value={team.length} detail="Kalam operations tenant" icon={UsersRound}/>
      <MetricCard label="Active users" value={active.length} detail="Available for assignment" icon={UserRoundCog}/>
      <MetricCard label="CRM-role users" value={operators.length} detail="SaaS Admin / Sales Operations / Viewer" icon={UsersRound}/>
      <MetricCard label="Inactive" value={team.length-active.length} detail="Not available for new ownership" icon={UserRoundCog}/>
    </div>

    <SectionCard eyebrow="Commercial ownership" title="Kalam operations team" meta={team.length+" users"}>
      <DataTable
        columns={["Team member","Email","Role(s)","Account status"]}
        empty={<EmptyState title="No operations users yet" description="Provision Kalam operations users through the approved administration process before assigning CRM ownership."/>}
        rows={team.map(member=>[
          <span key="a"><strong>{member.name}</strong><small>{member.job_title||"No job title"}</small></span>,
          <span key="b">{member.email}</span>,
          <span key="c">{member.roles.length?member.roles.join(" · "):"No role assigned"}</span>,
          <StatusBadge key="d" status={member.is_active?"active":"inactive"}/>,
        ])}
      />
      <p className="muted">This view does not create credentials. Operations users should be provisioned through the approved user/role administration workflow, then assigned to CRM accounts and opportunities.</p>
    </SectionCard>
  </DashboardShell>;
}
