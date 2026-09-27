import { DashboardShell } from "@/components/dashboard-shell";
import { PeopleDirectory } from "@/components/people-directory";
import { apiJson, requireUser } from "@/lib/server-api";
type Person = { id: string; email: string; first_name: string; last_name: string; employee_number?: string | null; job_title?: string | null; org_unit_id?: string | null; is_active: boolean };
type Unit = { id: string; name: string };
export default async function PeoplePage() {
  const user = await requireUser<{ permissions?: string[] }>();
  const permissions = user.permissions ?? [];
  if (!permissions.includes("users.read")) return <DashboardShell title="People" eyebrow="Workforce administration"><section className="data-panel"><h2>Access restricted</h2><p>You need permission to view the people directory.</p></section></DashboardShell>;
  const [people, units] = await Promise.all([
    apiJson<Person[]>("/api/v1/people"),
    apiJson<Unit[]>("/api/v1/organization/units"),
  ]);
  return <DashboardShell title="People" eyebrow="Workforce administration">
    {people && units ? <PeopleDirectory people={people} units={units} canManage={permissions.includes("users.manage")} /> : <section className="data-panel" role="alert"><h2>People directory unavailable</h2><p>Check your access or try again later.</p></section>}
  </DashboardShell>;
}
