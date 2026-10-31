import Link from "next/link";
import { DashboardShell } from "@/components/dashboard-shell";
import { DevelopmentTeamReview } from "@/components/development-team-review";
import { EmptyState, StateMessage } from "@/components/ui";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type Member = {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  job_title?: string | null;
};
type PeoplePage = { items: Member[]; total: number; page: number; page_size: number };

export default async function DevelopmentTeamPage({
  searchParams,
}: {
  searchParams: Promise<{ person?: string; q?: string }>;
}) {
  const user = await requireUser<{ permissions?: string[] }>();
  const permissions = user.permissions ?? [];
  const canManageDevelopment = permissions.includes("development.manage") || permissions.includes("tenant.manage");
  const canViewDirectReports = permissions.includes("team.read") && canManageDevelopment;
  const canViewWorkforce = permissions.includes("users.read") && canManageDevelopment;

  if (!canViewDirectReports && !canViewWorkforce) {
    return <DashboardShell title="Team development" eyebrow="Development governance">
      <EmptyState title="Team development access is restricted" description="This workspace requires development management permission and an authorized direct-report or workforce scope." />
    </DashboardShell>;
  }

  const query = await searchParams;
  const search = (query.q || "").trim().slice(0, 160);
  const organizationWide = canViewWorkforce;
  const endpoint = organizationWide
    ? "/api/v1/people/page?page=1&page_size=100&status=active" + (search ? "&q=" + encodeURIComponent(search) : "")
    : "/api/v1/people/team";
  const result = await apiJsonResult<Member[] | PeoplePage>(endpoint);
  if (!result.ok || !result.data) {
    return <DashboardShell title="Team development" eyebrow="Development governance">
      <StateMessage tone="danger" title="Authorized employee records are unavailable">
        {result.error || "The permitted employee scope could not be loaded. No wider directory is substituted."}
      </StateMessage>
    </DashboardShell>;
  }

  const members = Array.isArray(result.data) ? result.data : result.data.items;
  return <DashboardShell
    title={organizationWide ? "Development programme review" : "Team development"}
    eyebrow="Manager, HRBP, HR and L&D workspace"
    breadcrumbs={[{ label: "Overview", href: "/dashboard" }, { label: "Development plans", href: "/dashboard/development" }, { label: "Review" }]}
  >
    <div className="page-heading">
      <div>
        <span className="eyebrow">{organizationWide ? "Workforce development governance" : "Direct reports only"}</span>
        <h2>Coach progress without taking ownership of the employee’s plan.</h2>
        <p>{organizationWide
          ? "Review plans within your workforce administration remit, agree milestones and record reviewer feedback. Employee-authored goals remain read-only."
          : "Review plans for your authorized direct reports, agree milestones and record reviewer feedback. Employee-authored goals remain read-only."}</p>
      </div>
      <div className="page-heading-actions">
        <Link className="button button-secondary" href="/dashboard/team">Open team workspace</Link>
        <Link className="button button-secondary" href="/dashboard/development">My development</Link>
      </div>
    </div>
    {organizationWide && <form className="form-actions" action="/dashboard/development/team" method="get">
      <label className="form-field"><span>Find an employee</span><input name="q" defaultValue={search} placeholder="Name, email, employee number or title" maxLength={160} /></label>
      <button className="button button-secondary" type="submit">Search workforce</button>
      {search && <Link className="button button-ghost" href="/dashboard/development/team">Clear</Link>}
      {!Array.isArray(result.data) && <span className="muted">Showing {members.length} of {result.data.total} matching active employees.</span>}
    </form>}
    <DevelopmentTeamReview members={members} initialSelectedId={query.person || null} organizationWide={organizationWide} />
  </DashboardShell>;
}
