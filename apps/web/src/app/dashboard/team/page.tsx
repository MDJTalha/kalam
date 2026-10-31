import { DashboardShell } from "@/components/dashboard-shell";
import { TeamWorkspace } from "@/components/team-workspace";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type Member = { id: string; email: string; first_name: string; last_name: string; employee_number?: string | null; job_title?: string | null; completed_learning: number; open_learning: number; overdue_learning: number; open_compliance: number; overdue_compliance: number; active_plans: number };
export default async function TeamPage() {
  const user = await requireUser<{ permissions?: string[] }>();
  if (!user.permissions?.includes("users.read")) return <DashboardShell title="Team" eyebrow="Manager workspace"><section className="data-panel"><h2>Access restricted</h2><p>You need permission to view your direct reports.</p></section></DashboardShell>;
  const team = await apiJson<Member[]>("/api/v1/people/team");
  return <DashboardShell title="Team" eyebrow="Manager workspace" breadcrumbs={[{ label: "Overview", href: "/dashboard" }, { label: "Team" }]}>
    <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">People you manage</span><h2>Turn team signals into action</h2></div></div><p>Review direct reports, prioritize overdue learning and compliance, and open an individual learner to assign learning or discuss development.</p></section>
    {team ? <TeamWorkspace team={team} /> : <section className="data-panel" role="alert"><h2>Team data unavailable</h2><p>Check your access or try again later.</p></section>}
  </DashboardShell>;
}
