import { DashboardShell } from "@/components/dashboard-shell";
import { OrganizationWorkspace } from "@/components/organization-workspace";
import { apiJson, requireUser } from "@/lib/server-api";

type Unit = { id: string; name: string; unit_type: string; code?: string | null; parent_id?: string | null; member_count: number };
type UnitSummary = { units: Unit[]; active_people: number; assigned_people: number; unassigned_people: number };
export default async function OrganizationPage() {
  const user = await requireUser<{ permissions?: string[] }>();
  const permissions = user.permissions ?? [];
  if (!permissions.includes("users.read")) return <DashboardShell title="Organization" eyebrow="People & organization"><section className="data-panel"><h2>Access restricted</h2><p>You need permission to view the organization structure.</p></section></DashboardShell>;
  const summary = await apiJson<UnitSummary>("/api/v1/organization/units/summary");
  return <DashboardShell title="Organization" eyebrow="People & organization" breadcrumbs={[{ label: "People", href: "/dashboard/people" }, { label: "Organization" }]}>
    <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Workforce structure</span><h2>How your organization is arranged</h2></div></div><p>Set up business units, departments, locations and teams before assigning people and reporting lines.</p></section>
    {summary ? <OrganizationWorkspace initialUnits={summary.units} activePeople={summary.active_people} assignedPeople={summary.assigned_people} unassignedPeople={summary.unassigned_people} canManage={permissions.includes("users.manage")} /> : <section className="data-panel" role="alert"><h2>Organization data unavailable</h2><p>Check the API connection or your access and try again.</p></section>}
  </DashboardShell>;
}
