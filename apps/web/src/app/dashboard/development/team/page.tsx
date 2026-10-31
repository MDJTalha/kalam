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
  completed_learning: number;
  open_learning: number;
  overdue_learning: number;
  open_compliance: number;
  overdue_compliance: number;
  active_plans: number;
};

export default async function DevelopmentTeamPage({
  searchParams,
}: {
  searchParams: Promise<{ person?: string }>;
}) {
  const user = await requireUser<{ permissions?: string[] }>();
  const permissions = user.permissions ?? [];
  if (!permissions.includes("team.read") || !permissions.includes("development.manage")) {
    return <DashboardShell title="Team development" eyebrow="Development governance">
      <EmptyState title="Team development access is restricted" description="This workspace requires direct-report visibility and development management permission." />
    </DashboardShell>;
  }

  const query = await searchParams;
  const result = await apiJsonResult<Member[]>("/api/v1/people/team");
  if (!result.ok || !result.data) {
    return <DashboardShell title="Team development" eyebrow="Development governance">
      <StateMessage tone="danger" title="Direct-report records are unavailable">
        {result.error || "The team scope could not be loaded. No wider employee directory is substituted."}
      </StateMessage>
    </DashboardShell>;
  }

  return <DashboardShell
    title="Team development"
    eyebrow="Manager and HRBP workspace"
    breadcrumbs={[{ label: "Overview", href: "/dashboard" }, { label: "Development plans", href: "/dashboard/development" }, { label: "Team review" }]}
  >
    <div className="page-heading">
      <div>
        <span className="eyebrow">Direct reports only</span>
        <h2>Coach progress without taking ownership of the employee’s plan.</h2>
        <p>Review plans for your authorized direct reports, agree milestones, and record reviewer feedback. Employee-authored goals remain read-only in this workspace.</p>
      </div>
      <div className="page-heading-actions">
        <Link className="button button-secondary" href="/dashboard/team">Open team workspace</Link>
        <Link className="button button-secondary" href="/dashboard/development">My development</Link>
      </div>
    </div>
    <DevelopmentTeamReview members={result.data} initialSelectedId={query.person || null} />
  </DashboardShell>;
}
