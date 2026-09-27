import Link from "next/link";
import { notFound } from "next/navigation";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetch, requireUser } from "@/lib/server-api";
type Person = { id: string; first_name: string; last_name: string; email: string; employee_number?: string | null; job_title?: string | null; org_unit?: string | null; manager?: string | null; roles: string[]; is_active: boolean };
export default async function PersonPage({ params }: { params: Promise<{ id: string }> }) {
  const user = await requireUser<{ permissions?: string[] }>();
  const permissions = user.permissions ?? [];
  if (!permissions.includes("users.read")) return <DashboardShell title="Person" eyebrow="People & organization"><section className="data-panel"><h2>Access restricted</h2><p>You need permission to view this record.</p></section></DashboardShell>;
  const { id } = await params;
  if (!/^[0-9a-fA-F-]{36}$/.test(id)) notFound();
  const response = await apiFetch(`/api/v1/people/${id}`);
  if (response.status === 404) notFound();
  if (!response.ok) return <DashboardShell title="Person" eyebrow="People & organization"><section className="data-panel" role="alert"><h2>Person unavailable</h2><p>Check your access or try again later.</p></section></DashboardShell>;
  const person = await response.json() as Person;
  const fullName = `${person.first_name} ${person.last_name}`;
  return <DashboardShell title={fullName} eyebrow="Workforce record" breadcrumbs={[{ label: "People", href: "/dashboard/people" }, { label: fullName }]}>
    <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Person profile</span><h2>{fullName}</h2></div><span className={`status-badge ${person.is_active ? "success" : "muted"}`}>{person.is_active ? "Active" : "Inactive"}</span></div>
      <div className="detail-grid"><span><b>Work email</b>{person.email}</span><span><b>Employee number</b>{person.employee_number || "—"}</span><span><b>Job title</b>{person.job_title || "—"}</span><span><b>Organization unit</b>{person.org_unit || "Unassigned"}</span><span><b>Manager</b>{person.manager || "Unassigned"}</span><span><b>Access roles</b>{person.roles.length ? person.roles.join(", ") : "None assigned"}</span></div>
    </section>
    {permissions.includes("users.manage") && <section className="data-panel"><h2>Manage this person</h2><p>Update the organization placement, account details or access role.</p><Link className="button button-primary" href={`/dashboard/people/admin?person=${person.id}`}>Open user administration</Link></section>}
  </DashboardShell>;
}
