import { UserRoundCog, UsersRound } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { SaaSTeamAdmin } from "@/components/saas-team-admin";
import { SaaSPlatformRoleGovernance } from "@/components/saas-platform-role-governance";
import { DataTable, EmptyState, MetricCard, SectionCard, StatusBadge } from "@/components/ui";
import { apiJson, requireUser } from "@/lib/server-api";

type Assignment={id:string;name:string;role_kind:string};
type TeamMember={
  id:string;name:string;email:string;job_title?:string|null;is_active:boolean;roles:string[];
  role_assignments:Assignment[];
};
type Role={id:string;name:string;role_kind:string;description?:string|null};

export default async function SaaSTeamPage(){
  const user=await requireUser<{permissions?:string[];roles?:Array<{name:string}>}>();
  const canManage=user.permissions?.includes("saas.team.manage")??false;
  const roleNames=(user.roles??[]).map(role=>role.name.trim().toLowerCase());
  const canManagePlatformRoles=roleNames.includes("saas super admin")||roleNames.includes("platform developer");
  if(!user.permissions?.includes("saas.team.read"))return <DashboardShell title="SaaS Team" eyebrow="Platform operations"><EmptyState title="SaaS team access is restricted" description="This role does not include internal SaaS team visibility."/></DashboardShell>;
  const [team,roles]=await Promise.all([
    apiJson<TeamMember[]>("/api/v1/saas/crm/team"),
    canManage?apiJson<Role[]>("/api/v1/organization/roles"):Promise.resolve(null),
  ]);
  if(!team)return <DashboardShell title="SaaS Team" eyebrow="Platform operations"><EmptyState title="SaaS team data is unavailable" description="Check your role, SaaS operations workspace and API availability."/></DashboardShell>;

  const active=team.filter(member=>member.is_active);
  const operators=team.filter(member=>member.roles.some(role=>["SaaS Administrator","Sales Operations","Sales Viewer","SaaS Finance Administrator","Customer Success Manager"].includes(role)));

  return <DashboardShell title="SaaS Team" eyebrow="Platform operations" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Team"}]}>
    <SaaSCrmNav/>
    <div className="stat-grid saas-spaced-section">
      <MetricCard label="Operations users" value={team.length} detail="Internal Kalam workspace" icon={UsersRound}/>
      <MetricCard label="Active users" value={active.length} detail="Available for assignments" icon={UserRoundCog}/>
      <MetricCard label="Assigned operators" value={operators.length} detail="Sales, finance and customer success" icon={UsersRound}/>
      <MetricCard label="Inactive" value={team.length-active.length} detail="Access currently disabled" icon={UserRoundCog}/>
    </div>

    {canManage&&roles
      ? <><SaaSTeamAdmin initialMembers={team} roles={roles}/><SaaSPlatformRoleGovernance enabled={canManagePlatformRoles}/></>
      : <SectionCard eyebrow="Least-privilege overview" title="Kalam operations team" meta={team.length+" users"}>
          <DataTable
            columns={["Team member","Email","Role(s)","Account status"]}
            empty={<EmptyState title="No operations users yet" description="No internal SaaS team members are provisioned yet."/>}
            rows={team.map(member=>[
              <span key="a"><strong>{member.name}</strong><small>{member.job_title||"No job title"}</small></span>,
              <span key="b">{member.email}</span>,
              <span key="c">{member.roles.length?member.roles.join(" · "):"No role assigned"}</span>,
              <StatusBadge key="d" status={member.is_active?"active":"inactive"}/>,
            ])}
          />
          <p className="muted">This is a read-only team view. Account and role changes require the SaaS team-management permission.</p>
        </SectionCard>}
  </DashboardShell>;
}
