import Link from "next/link";
import { UsersRound, Layers3, ArrowRight } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { ProgramCreateForm } from "@/components/program-create-form";
import { apiJsonResult, requireUser  } from "@/lib/server-api";

type Program = {
  id: string;
  title: string;
  slug: string;
  description?: string | null;
  status: string;
  is_required: boolean;
};

type Cohort = {
  id: string;
  program_id: string;
  name: string;
  code: string;
  status: string;
  starts_at?: string | null;
  ends_at?: string | null;
  capacity?: number | null;
};

export default async function ProgramsPage() {
  const user = await requireUser<{ permissions?: string[] }>();
  const canManage = user.permissions?.includes("courses.manage") ?? false;
  const [programs, cohorts] = await Promise.all([
    apiJsonResult<Program[]>("/api/v1/programs").then((result) => result.ok ? result.data : null),
    apiJsonResult<Cohort[]>("/api/v1/programs/cohorts").then((result) => result.ok ? result.data : null),
  ]);

  return (
    <DashboardShell title="Programs & cohorts" eyebrow="Corporate learning delivery">
      <div className="stat-grid">
        <div className="stat-card"><span>Programs</span><strong>{programs ? programs.length : "—"}</strong><small>{programs ? "Structured learning programs" : "Data unavailable"}</small></div>
        <div className="stat-card"><span>Cohorts</span><strong>{cohorts?.length ?? "—"}</strong><small>Managed learner groups</small></div>
        <div className="stat-card"><span>Active cohorts</span><strong>{cohorts?.filter((item) => item.status === "active").length ?? "—"}</strong><small>Currently running</small></div>
        <div className="stat-card"><span>Required programs</span><strong>{programs?.filter((item) => item.is_required).length ?? "—"}</strong><small>Mandatory pathways</small></div>
      </div>

      {(!programs || !cohorts) && <section className="data-panel" role="alert"><h2>Delivery data unavailable</h2><p>Some program information could not be loaded. Try again.</p></section>}
      <section className="data-panel">
        <div className="section-heading compact">
          <div><span className="eyebrow">Structured learning</span><h2>Programs</h2></div>
          <span className="section-meta">{programs ? `${programs.length} configured` : "Unavailable"}</span>
        </div>
        {programs?.length ? (
          <div className="catalog-grid">
            {programs.map((program) => (
              <Link href={"/dashboard/programs/" + program.id} className="catalog-card" key={program.id}>
                <div className="module-icon"><Layers3 size={19} /></div>
                <div className="catalog-copy">
                  <div className="catalog-top"><span className="tag">{program.is_required ? "REQUIRED" : "ELECTIVE"}</span><span>{program.status}</span></div>
                  <h3>{program.title}</h3>
                  <p>{program.description || "No program description has been published yet."}</p>
                  <small><ArrowRight size={13} /> Open program</small>
                </div>
              </Link>
            ))}
          </div>
        ) : <div className="empty-state"><Layers3 size={24}/><p>{canManage ? "Create a draft program and add its courses." : "Published programs will appear here."}</p></div>}
      </section>

      {canManage && <ProgramCreateForm />}
      <section className="data-panel">
        <div className="section-heading compact">
          <div><span className="eyebrow">Learner groups</span><h2>Cohorts</h2></div>
        </div>
        {cohorts?.length ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead><tr><th scope="col">Cohort</th><th scope="col">Program</th><th scope="col">Status</th><th scope="col">Schedule</th><th scope="col">Capacity</th></tr></thead>
              <tbody>
                {cohorts.map((cohort) => (
                  <tr key={cohort.id}>
                    <td><Link href={"/dashboard/programs/cohorts/" + cohort.id} className="text-link"><strong>{cohort.name}</strong></Link><div>{cohort.code}</div></td>
                    <td>{programs?.find((program) => program.id === cohort.program_id)?.title || "—"}</td>
                    <td><span className={cohort.status === "active" ? "status-badge success" : "status-badge warning"}>{cohort.status}</span></td>
                    <td>{cohort.starts_at ? new Date(cohort.starts_at).toLocaleDateString() : "—"} → {cohort.ends_at ? new Date(cohort.ends_at).toLocaleDateString() : "—"}</td>
                    <td>{cohort.capacity ?? "Open"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <div className="empty-state"><UsersRound size={24}/><p>No cohorts have been created yet.</p></div>}
      </section>
    </DashboardShell>
  );
}
