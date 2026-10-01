import Link from "next/link";
import { ArrowLeft, BarChart3, ShieldCheck } from "lucide-react";
import { notFound } from "next/navigation";
import { AssessmentAttempts } from "@/components/assessment-attempts";
import { DashboardShell } from "@/components/dashboard-shell";
import { Section } from "@/components/ui";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type Attempt={id:string;learner_id:string;learner:string;attempt_number:number;score:number|null;passed:boolean|null;feedback:string|null;grade_override:boolean;started_at:string;submitted_at?:string|null};
type Assessment={id:string;title:string;passing_score:number};
type Analytics={attempts:number;submitted_attempts:number;passed_attempts:number;failed_attempts:number;pass_rate:number;average_score:number;highest_score:number|null;lowest_score:number|null;overrides:number};
type QuestionAnalytics={questions:Array<{question_id:string;position:number;prompt:string;attempts:number;answered:number;correct:number;correct_rate:number}>};

export default async function AssessmentAttemptsPage({params}:{params:Promise<{id:string}>}){
  await requireUser();
  const {id}=await params;
  const [assessmentResult,attemptsResult,analyticsResult,questionAnalyticsResult]=await Promise.all([
    apiJsonResult<Assessment>(`/api/v1/assessments/${id}`),
    apiJsonResult<Attempt[]>(`/api/v1/assessments/${id}/attempts`),
    apiJsonResult<Analytics>(`/api/v1/assessments/${id}/analytics`),
    apiJsonResult<QuestionAnalytics>(`/api/v1/assessments/${id}/question-analytics`),
  ]);
  if (assessmentResult.status === 404 || assessmentResult.status === 403) notFound();
  if (!assessmentResult.ok || !assessmentResult.data) return <DashboardShell title="Assessment attempts" eyebrow="Assessment operations"><section className="data-panel" role="alert"><h2>Assessment data unavailable</h2><p>{assessmentResult.error || "The assessment could not be loaded. Try again later."}</p></section></DashboardShell>;
  const assessment=assessmentResult.data;
  const attempts=attemptsResult.ok ? (attemptsResult.data ?? []) : [];
  const analytics=analyticsResult.ok ? analyticsResult.data : null;
  const questionAnalytics=questionAnalyticsResult.ok ? questionAnalyticsResult.data : null;
  const stats=analytics??{attempts:0,submitted_attempts:0,passed_attempts:0,failed_attempts:0,pass_rate:0,average_score:0,highest_score:null,lowest_score:null,overrides:0};
  return <DashboardShell title={assessment.title} eyebrow="Assessment operations" breadcrumbs={[{label:"Assessment operations",href:"/dashboard/assessments/admin"},{label:assessment.title,href:`/dashboard/assessments/admin/${id}`},{label:"Attempts & grading"}]}>
    <div className="callout"><ShieldCheck size={16}/><strong>Audited grading</strong><p>Manual overrides require an explicit score, outcome and reason. The API records the grading actor and audit event.</p></div>
    <Section eyebrow="Performance" title="Assessment analytics" action={<BarChart3 size={18}/> }>
      <div className="metric-strip">
        <span><b>{stats.submitted_attempts}</b> submitted</span><span><b>{stats.pass_rate}%</b> pass rate</span><span><b>{stats.average_score}%</b> average</span><span><b>{stats.highest_score??"—"}%</b> highest</span><span><b>{stats.overrides}</b> overrides</span>
      </div>
    </Section>
    <Section eyebrow="Question intelligence" title="Question-level performance">{questionAnalytics?.questions?.length ? <div className="compact-list">{questionAnalytics.questions.map(item=><div className="compact-row" key={item.question_id}><div style={{minWidth:0,flex:1}}><strong>Q{item.position}. {item.prompt}</strong><small>{item.answered} answered · {item.correct} correct · {item.attempts} submitted attempts</small></div><span className="status-badge">{item.correct_rate}% correct</span></div>)}</div> : <div className="empty-state"><p>{questionAnalyticsResult.ok ? "No question analytics are available until learners submit attempts." : "Question analytics are temporarily unavailable."}</p></div>}</Section>
    <Section eyebrow="Attempts" title="Learner submissions" action={<Link className="button button-secondary" href={"/dashboard/assessments/admin/"+id}><ArrowLeft size={14}/> Builder</Link>}>{attempts.length ? <AssessmentAttempts initial={attempts}/> : <div className="empty-state"><p>{attemptsResult.ok ? "No learner submissions have been recorded yet." : "Learner submissions are temporarily unavailable."}</p></div>}</Section>
    <div className="metric-strip"><span><b>{stats.attempts}</b> attempts</span><span><b>{stats.passed_attempts}</b> passed</span><span><b>{stats.failed_attempts}</b> failed</span><span><b>{assessment.passing_score}%</b> default pass score</span></div>
  </DashboardShell>
}
