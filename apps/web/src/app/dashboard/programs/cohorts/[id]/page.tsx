import Link from "next/link";
import { ArrowLeft, UsersRound } from "lucide-react";
import { notFound } from "next/navigation";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJson, requireUser } from "@/lib/server-api";

type Member = { user_id: string; name: string; email: string; status: string };
type Cohort = {
  id: string;
  program_id: string;
  name: string;
  code: string;
  status: string;
  starts_at?: string | null;
  ends_at?: string | null;
  capacity?: number | null;
  members: Member[];
};

export default async function CohortDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  await requireUser();
  const { id } = await params;
  const cohort = await apiJson<Cohort>("/api/v1/programs/cohorts/" + id);
  if (!cohort) notFound();

  return (
    <DashboardShell title={cohort.name} eyebrow="Cohort delivery">
      <section className="data-panel">
        <Link href="/dashboard/programs" className="text-link"><ArrowLeft size={15}/> Back to programs</Link>
        <div className="section-heading">
          <span className="eyebrow">{cohort.status} · {cohort.code}</span>
          <h2>{cohort.name}</h2>
          <p>{cohort.starts_at ? new Date(cohort.starts_at).toLocaleDateString() : "No start date"} → {cohort.ends_at ? new Date(cohort.ends_at).toLocaleDateString() : "No end date"}</p>
        </div>
        <div className="metric-strip">
          <span><b>{cohort.members.length}</b> members</span>
          <span><b>{cohort.capacity ?? "Open"}</b> capacity</span>
          <span><b>{cohort.capacity ? Math.round(cohort.members.length / cohort.capacity * 100) : 0}%</b> utilization</span>
        </div>
      </section>

      <section className="data-panel">
        <div className="section-heading compact">
          <div><span className="eyebrow">Roster</span><h2>Learners</h2></div>
          <UsersRound size={20}/>
        </div>
        {cohort.members.length ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead><tr><th>Learner</th><th>Email</th><th>Status</th></tr></thead>
              <tbody>
                {cohort.members.map((member) => (
                  <tr key={member.user_id}>
                    <td><strong>{member.name}</strong></td>
                    <td>{member.email}</td>
                    <td><span className={member.status === "active" ? "status-badge success" : "status-badge warning"}>{member.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <div className="empty-state"><UsersRound size={24}/><p>No learners are enrolled in this cohort yet.</p></div>}
      </section>
    </DashboardShell>
  );
}
