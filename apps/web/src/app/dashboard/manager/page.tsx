import Link from "next/link";
import { AlertTriangle, BookOpenCheck, ShieldCheck, UsersRound } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { DataTable, EmptyState, MetricCard, SectionCard, StatusBadge } from "@/components/ui";
import { apiJson, requireUser } from "@/lib/server-api";

type TeamMember = {
  id:string;first_name:string;last_name:string;email:string;job_title?:string|null;
  completed_learning:number;open_learning:number;overdue_learning:number;
  open_compliance:number;overdue_compliance:number;active_plans:number;
};

export default async function ManagerWorkspacePage() {
  const user=await requireUser<{permissions?:string[]}>();
  if(!user.permissions?.includes("team.read")) {
    return <DashboardShell title="Manager workspace" eyebrow="Team leadership"><EmptyState title="Manager access is restricted" description="This workspace requires the direct-report team permission."/></DashboardShell>;
  }
  const team=await apiJson<TeamMember[]>("/api/v1/people/team");
  if(!team)return <DashboardShell title="Manager workspace" eyebrow="Team leadership"><EmptyState title="Team data unavailable" description="Direct-report records could not be loaded. No wider tenant directory is substituted."/></DashboardShell>;
  const completed=team.reduce((sum,item)=>sum+item.completed_learning,0);
  const total=completed+team.reduce((sum,item)=>sum+item.open_learning,0);
  const completion=total?Math.round(completed/total*100):null;
  const overdueLearning=team.reduce((sum,item)=>sum+item.overdue_learning,0);
  const overdueCompliance=team.reduce((sum,item)=>sum+item.overdue_compliance,0);
  const attention=team.filter(item=>item.overdue_learning>0||item.overdue_compliance>0||item.active_plans===0);
  return <DashboardShell title="Manager workspace" eyebrow="Team leadership" breadcrumbs={[{label:"Overview",href:"/dashboard"},{label:"Manager workspace"}]}>
    <div className="page-heading">
      <div><span className="eyebrow">Direct reports only</span><h2>Lead your team with clear follow-up.</h2><p>Review learning progress, compliance obligations and individual development plans for your assigned direct reports.</p></div>
      <div className="page-heading-actions"><Link className="button button-secondary" href="/dashboard/team">Open team workspace</Link><Link className="button button-primary" href="/dashboard/development">Development plans</Link></div>
    </div>
    <div className="stat-grid">
      <MetricCard label="Direct reports" value={team.length} detail="People reporting directly to you" icon={UsersRound}/>
      <MetricCard label="Learning completion" value={completion===null?"—":completion+"%"} detail={completed+" completed of "+total+" tracked enrollments"} icon={BookOpenCheck}/>
      <MetricCard label="Overdue learning" value={overdueLearning} detail="Requires manager follow-up" icon={AlertTriangle}/>
      <MetricCard label="Overdue compliance" value={overdueCompliance} detail="Obligations past due" icon={ShieldCheck}/>
    </div>
    <div className="two-column">
      <SectionCard eyebrow="Manager attention" title="People needing follow-up" meta={attention.length+" direct reports"}>
        {attention.length?<div className="compact-list">{attention.map(item=><div className="compact-row" key={item.id}><div><strong>{item.first_name} {item.last_name}</strong><small>{item.job_title||item.email}</small><small>{item.overdue_learning} overdue learning · {item.overdue_compliance} overdue compliance · {item.active_plans} active plans</small></div><Link className="text-link" href={"/dashboard/development?user_id="+encodeURIComponent(item.id)}>Review development</Link></div>)}</div>:<EmptyState title="No follow-up flags" description="No overdue learning or compliance items are currently recorded for your direct reports."/>}
      </SectionCard>
      <SectionCard eyebrow="Team controls" title="Work within your management scope">
        <div className="role-actions"><Link href="/dashboard/team">Team learning and activity</Link><Link href="/dashboard/capability-gaps">Capability gaps for your team</Link><Link href="/dashboard/capability-risk">Team capability risk</Link><Link href="/dashboard/development">Development plans</Link></div>
        <p className="form-help">You cannot open another department’s people records or tenant-wide HR reports unless separately authorized.</p>
      </SectionCard>
    </div>
    <SectionCard eyebrow="Direct-report register" title="My team" meta={team.length+" people"}>
      <DataTable columns={["Employee","Completed learning","Open learning","Overdue","Compliance overdue","Development plans"]} empty={<EmptyState title="No direct reports assigned" description="Ask your tenant administrator to verify your manager relationship in the organization structure."/>} rows={team.map(item=>[
        <span key="a"><strong>{item.first_name} {item.last_name}</strong><small>{item.job_title||item.email}</small></span>,
        <span key="b">{item.completed_learning}</span>,
        <span key="c">{item.open_learning}</span>,
        <StatusBadge key="d" status={item.overdue_learning>0?"overdue":"clear"}/>,
        <StatusBadge key="e" status={item.overdue_compliance>0?"overdue":"clear"}/>,
        <span key="f">{item.active_plans}</span>
      ])}/>
    </SectionCard>
  </DashboardShell>;
}
