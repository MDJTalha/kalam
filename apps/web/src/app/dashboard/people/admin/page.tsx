import Link from "next/link";
import { DashboardShell } from "@/components/dashboard-shell";
import { RoleAssignment } from "@/components/role-assignment";
import { PeopleBulkInvite } from "@/components/people-bulk-invite";
import { UserLifecyclePanel } from "@/components/user-lifecycle-panel";
import { apiJson, apiJsonResult, requireUser } from "@/lib/server-api";

type Person = { id: string; email: string; first_name: string; last_name: string; employee_number?: string | null; job_title?: string | null; manager_id?: string | null; org_unit_id?: string | null; is_active: boolean };
type Role = { id: string; name: string };\ntype RolePage = { items: Role[]; total: number };
type Unit = { id: string; name: string; unit_type: string };\ntype UnitPage = { items: Unit[]; total: number };
type PeoplePage = { items: Person[]; total: number; page: number; page_size: number };

export default async function UserAdministrationPage({ searchParams }: { searchParams: Promise<{ person?: string; q?: string; page?: string }> }) {
  const user = await requireUser<{ permissions?: string[] }>();
  const permissions = user.permissions ?? [];
  if (!permissions.includes("users.read")) {
    return <DashboardShell title="User administration" eyebrow="People & organization"><section className="data-panel"><h2>Access restricted</h2><p>You need permission to view people in this workspace.</p></section></DashboardShell>;
  }
  const { person, q = "", page: rawPage = "1" } = await searchParams;
  const page = Math.max(1, Number.parseInt(rawPage, 10) || 1);
  const peopleQuery = new URLSearchParams({ page: String(page), page_size: "50", q: q.slice(0, 160), status: "all" });
  const [peopleResult, roles, units] = await Promise.all([
    apiJsonResult<PeoplePage>(`/api/v1/people/page?${peopleQuery}`),
    apiJson<Role[]>("/api/v1/organization/roles"),
    apiJson<Unit[]>("/api/v1/organization/units"),
  ]);
  const people = peopleResult.ok ? peopleResult.data?.items ?? [] : null;
  const peopleTotal = peopleResult.ok ? peopleResult.data?.total ?? 0 : 0;
  return <DashboardShell title="User administration" eyebrow="People & organization" breadcrumbs={[{ label: "People", href: "/dashboard/people" }, { label: "User administration" }]}>
    <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Workforce lifecycle</span><h2>Invite and manage people</h2></div><Link className="text-link" href="/dashboard/people">View directory</Link></div>
      <p>Invite colleagues, update employment details and manage access within your organization.</p>
    </section>
    <form className="form-actions" action="/dashboard/people/admin" method="get"><label className="form-field"><span>Search people</span><input name="q" defaultValue={q} placeholder="Name, email, employee number or title" maxLength={160} /></label><button className="button button-secondary" type="submit">Search</button>{q&&<Link className="button button-ghost" href="/dashboard/people/admin">Clear</Link>}</form>
    {people && roles && units ? <><p className="form-help">Showing {people.length} of {peopleTotal} matching people. Search to find a specific person or manager.</p><UserLifecyclePanel people={people} roles={roles} units={units} initialSelectedId={person} accessPermissions={permissions} />
      {peopleTotal > 50 && <nav className="button-row" aria-label="People pages">{page > 1 && <Link className="button button-secondary" href={`/dashboard/people/admin?q=${encodeURIComponent(q)}&page=${page - 1}`}>Previous</Link>}<span>Page {page} of {Math.ceil(peopleTotal / 50)}</span>{page * 50 < peopleTotal && <Link className="button button-secondary" href={`/dashboard/people/admin?q=${encodeURIComponent(q)}&page=${page + 1}`}>Next</Link>}</nav>}
      <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Access control</span><h2>Assign a role</h2></div></div><RoleAssignment people={people} roles={roles} initialSelectedId={person} accessPermissions={permissions} /></section>{permissions.includes("users.manage") && <PeopleBulkInvite roles={roles} />}</>
      : <section className="data-panel" role="alert"><h2>Workforce data unavailable</h2><p>Check the API connection or your access and try again.</p></section>}
  </DashboardShell>;
}
