import Link from "next/link";
import { ArrowLeft, ClipboardCheck, ShieldCheck } from "lucide-react";
import { notFound } from "next/navigation";
import { AssessmentAttempts } from "@/components/assessment-attempts";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type Attempt={id:string;learner_id:string;learner:string;attempt_number:number;score:number|null;passed:boolean|null;feedback:string|null;grade_override:boolean;started_at:string;submitted_at?:string|null};
type Assessment={id:string;title:string;passing_score:number};
type Analytics={attempts:number;submitted_attempts:number;passed_attempts:number;failed_attempts:number;pass_rate:number;average_score:number;highest_score:number|null;lowest_score:number|null;overrides:number};

export default async function InstructorAssessmentReviewPage({params}:{params:Promise<{id:string}>}) {
  const user=await requireUser<{permissions?:string[]}>();
  if(!user.permissions?.includes("assessments.grade_assigned")&&!user.permissions?.includes("assessments.manage")) {
    return <DashboardShell title="Assessment review" eyebrow="Instructor assessment review"><div className="data-panel"><h2>Review access is restricted</h2><p>Your role does not include grading access for assigned assessments.</p></div></DashboardShell>;
  }
  const {id}=await params;
  const [assessmentResult,attemptsResult,analyticsResult]=await Promise.all([
    apiJsonResult<Assessment>(`/api/v1/assessments/${id}`),
    apiJsonResult<Attempt[]>(`/api/v1/assessments/${id}/attempts`),
    apiJsonResult<Analytics>(`/api/v1/assessments/${id}/analytics`),
  ]);
  if(assessmentResult.status===404||assessmentResult.status===403)notFound();
  if(!assessmentResult.ok||!assessmentResult.data)return <DashboardShell title="Assessment review" eyebrow="Instructor assessment review"><div className="data-panel" role="alert"><h2>Assessment data unavailable</h2><p>{assessmentResult.error||"The assigned assessment could not be loaded."}</p></div></DashboardShell>;
  const attempts=attemptsResult.ok?(attemptsResult.data??[]):[];
  const stats=analyticsResult.ok?analyticsResult.data:null;
  return <DashboardShell title={assessmentResult.data.title} eyebrow="Assigned assessment review" breadcrumbs={[{label:"Instructor workspace",href:"/dashboard/instructor"},{label:"Assessments",href:"/dashboard/assessments"},{label:"Review submissions"}]}>
    <div className="callout"><ShieldCheck size={16}/><div><strong>Assigned-course scope</strong><p>You can review and grade submissions only for courses with live sessions assigned to your instructor account. Assessment authoring and answer-key administration remain with L&D administrators.</p></div></div>
    <div className="metric-strip">
      <span><b>{stats?.submitted_attempts??attempts.filter(item=>item.submitted_at).length}</b> submitted</span>
      <span><b>{stats?.pass_rate??"—"}{stats?"%":""}</b> pass rate</span>
      <span><b>{stats?.average_score??"—"}{stats?"%":""}</b> average score</span>
      <span><b>{stats?.overrides??attempts.filter(item=>item.grade_override).length}</b> overrides</span>
    </div>
    <section className="data-panel">
      <div className="section-heading compact"><div><span className="eyebrow">Learner evidence</span><h2>Submissions and grading</h2></div><ClipboardCheck size={18}/></div>
      {attempts.length?<AssessmentAttempts initial={attempts}/>:<div className="empty-state"><p>{attemptsResult.ok?"No learner submissions have been recorded for this assigned assessment yet.":"Submission data is temporarily unavailable."}</p></div>}
    </section>
    <div className="form-actions"><Link className="button button-secondary" href="/dashboard/assessments"><ArrowLeft size={14}/> Back to assessments</Link></div>
  </DashboardShell>;
}
