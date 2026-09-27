import Link from "next/link";
import { DashboardShell } from "@/components/dashboard-shell";
import { RoleAssignment } from "@/components/role-assignment";
import { PeopleBulkInvite } from "@/components/people-bulk-invite";
import { UserLifecyclePanel } from "@/components/user-lifecycle-panel";
import { apiJson, requireUser } from "@/lib/server-api";

type Person = { id: string; email: string; first_name: string; last_name: string; employee_number?: string | null; job_title?: string | null; manager_id?: string | null; org_unit_id?: string | null; is_active: boolean };
type Role = { id: string; name: string };
type Unit = { id: string; name: string; unit_type: string };

export default async function UserAdministrationPage({ searchParams }: { searchParams: Promise<{ person?: string }> }) {
  const user = await requireUser<{ permissions?: string[] }>();
  const permissions = user.permissions ?? [];
  if (!permissions.includes("users.read")) {
    return <DashboardShell title="User administration" eyebrow="People & organization"><section className="data-panel"><h2>Access restricted</h2><p>You need permission to view people in this workspace.</p></section></DashboardShell>;
  }
  const { person } = await searchParams;
  const [people, roles, units] = await Promise.all([
    apiJson<Person[]>("/api/v1/people"),
    apiJson<Role[]>("/api/v1/organization/roles"),
    apiJson<Unit[]>("/api/v1/organization/units"),
  ]);
  return <DashboardShell title="User administration" eyebrow="People & organization" breadcrumbs={[{ label: "People", href: "/dashboard/people" }, { label: "User administration" }]}>
    <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Workforce lifecycle</span><h2>Invite and manage people</h2></div><Link className="text-link" href="/dashboard/people">View directory</Link></div>
      <p>Invite colleagues, update employment details and manage access within your organization.</p>
    </section>
    {people && roles && units ? <><UserLifecyclePanel people={people} roles={roles} units={units} initialSelectedId={person} accessPermissions={permissions} />
      <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Access control</span><h2>Assign a role</h2></div></div><RoleAssignment people={people} roles={roles} initialSelectedId={person} accessPermissions={permissions} /></section>{permissions.includes("users.manage") && <PeopleBulkInvite roles={roles} />}</>
      : <section className="data-panel" role="alert"><h2>Workforce data unavailable</h2><p>Check the API connection or your access and try again.</p></section>}
  </DashboardShell>;
}
