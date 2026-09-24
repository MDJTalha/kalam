import Link from "next/link";
import { ClipboardCheck } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJson, requireUser } from "@/lib/server-api";

type Assessment = { id: string; title: string; course_id?: string | null; passing_score: number; max_attempts?: number | null; time_limit_minutes?: number | null };

export default async function AssessmentsPage() {
  await requireUser();
  const assessments = await apiJson<Assessment[]>("/api/v1/assessments");
  return (
    <DashboardShell title="Assessments" eyebrow="Assessment operations">
      <div className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Assessment library</span><h2>Examinations</h2></div><span className="section-meta">{assessments?.length ?? 0} assessments</span></div>
        {assessments?.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Assessment</th><th>Pass score</th><th>Attempts</th><th>Time</th></tr></thead><tbody>{assessments.map((item)=><tr key={item.id}><td><Link className="text-link" href={`/dashboard/assessments/${item.id}`}>{item.title}</Link><small>{item.course_id || "Standalone"}</small></td><td>{item.passing_score}%</td><td>{item.max_attempts || "Unlimited"}</td><td>{item.time_limit_minutes ? `${item.time_limit_minutes} min` : "No limit"}</td></tr>)}</tbody></table></div> : <div className="empty-state"><ClipboardCheck size={24}/><p>No assessments have been created yet.</p></div>}
      </div>
    </DashboardShell>
  );
}
