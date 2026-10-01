import Link from "next/link";
import { ClipboardCheck } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type Assessment = { id: string; title: string; course_id?: string | null; passing_score: number; max_attempts?: number | null; time_limit_minutes?: number | null; question_count:number; course_title?:string|null };

export default async function AssessmentsPage() {
  const user=await requireUser<{permissions?:string[]}>();
  const canManage=user.permissions?.includes("assessments.manage")??false;
  const result = await apiJsonResult<Assessment[]>("/api/v1/assessments");
  if (!result.ok) {
    const restricted = result.status === 403;
    const serviceFailure = result.status >= 500;
    return <DashboardShell title="Assessments" eyebrow="Assessment operations"><section className="data-panel" role="alert"><h2>{restricted ? "Assessment access restricted" : serviceFailure ? "Assessment service unavailable" : "Assessments could not be loaded"}</h2><p>{restricted ? "Your role does not have access to the assessment library." : serviceFailure ? "The assessment service did not respond successfully. No empty library is being shown." : result.error || "The assessment library could not be loaded. Refresh and try again."}</p></section></DashboardShell>;
  }
  const assessments = result.data ?? [];
  return (
    <DashboardShell title="Assessments" eyebrow="Assessment operations">
      <div className="assessment-library-hero"><div><span className="eyebrow">Assessment library</span><h2>Check learning with evidence.</h2><p>Complete assessments with explicit attempt control, clear scoring thresholds and a reviewable outcome.</p></div>{canManage&&<Link className="button button-primary" href="/dashboard/assessments/admin">Open assessment operations</Link>}</div>
      <div className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Available assessments</span><h2>Assessments</h2></div><span className="section-meta">{assessments?.length ?? 0} assessments</span></div>
        {assessments?.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th scope="col">Assessment</th><th scope="col">Questions</th><th scope="col">Pass score</th><th scope="col">Attempts</th><th scope="col">Time</th></tr></thead><tbody>{assessments.map((item)=><tr key={item.id}><td>{item.question_count?<Link className="text-link" href={`/dashboard/assessments/${item.id}`}>{item.title}</Link>:<strong>{item.title}</strong>}<small>{item.course_title || "Standalone"}{!item.question_count?" · No questions yet":""}</small></td><td>{item.question_count}</td><td>{item.passing_score}%</td><td>{item.max_attempts || "Unlimited"}</td><td>{item.time_limit_minutes ? `${item.time_limit_minutes} min` : "No limit"}</td></tr>)}</tbody></table></div> : <div className="empty-state"><ClipboardCheck size={24}/><p>No assessments have been created yet.</p></div>}
      </div>
    </DashboardShell>
  );
}
