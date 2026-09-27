import { BarChart3, UsersRound } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { EmptyState, MetricCard, Section } from "@/components/ui";
import { apiJson, requireUser } from "@/lib/server-api";

type Summary={users:number;courses:number;enrollments:number;completed_enrollments:number;certificates:number;compliance_assignments:number};
type Intelligence={population:number;skill_gaps:number;people_with_skill_gaps:number;open_compliance:number;overdue_compliance:number;risk_band:string;top_skill_gaps:Array<{user_name:string;role:string;skill:string;current:number;required:number;gap:number}>;recommended_actions:Array<{course_title:string;user_name:string;skill:string;gap:number}>};
type Trends={days:number;points:Array<{date:string;enrollments:number;completions:number}>};
type Performance={courses:Array<{course_id:string;course:string;status:string;enrollments:number;completions:number;completion_rate:number}>};
type Risk={total:number;open:number;overdue:number;risk_band:string};
type Effectiveness={completed:number;in_progress:number;completion_rate:number;average_days_to_complete:number|null;measured_completions:number};
type Engagement={enrolled_learners:number;active_learners:number;learner_activation_rate:number;learner_completion_reach:number};
type Assessment={assessment_id:string;assessment:string;submitted_attempts:number;average_score:number;pass_rate:number};
type OrgUnit={org_unit_id:string;org_unit:string;people:number;completion_rate:number};

export default async function AnalyticsPage(){
  await requireUser();
  const [summary,intelligence,trends,performance,risk,effectiveness,engagement,assessments,organization]=await Promise.all([
    apiJson<Summary>("/api/v1/reports/summary"),
    apiJson<Intelligence>("/api/v1/intelligence/capability"),
    apiJson<Trends>("/api/v1/reports/learning-trends?days=30"),
    apiJson<Performance>("/api/v1/reports/course-performance?page=1&page_size=12&sort_by=enrollments&sort_dir=desc"),
    apiJson<Risk>("/api/v1/reports/compliance-risk"),
    apiJson<Effectiveness>("/api/v1/reports/learning-effectiveness"),
    apiJson<Engagement>("/api/v1/reports/engagement"),
    apiJson<{assessments:Assessment[]}>("/api/v1/reports/assessment-performance"),
    apiJson<{organization_units:OrgUnit[]}>("/api/v1/reports/organization-performance"),
  ]);
  const completion=summary?.enrollments?Math.round(summary.completed_enrollments/summary.enrollments*100):0;
  return <DashboardShell title="Executive analytics" eyebrow="Decision-ready workforce intelligence" breadcrumbs={[{label:"Reports",href:"/dashboard/reports"},{label:"Executive analytics"}]}>
    <div className="stat-grid"><MetricCard label="Workforce" value={summary?.users??0} hint="Tenant population" icon="users"/><MetricCard label="Completion" value={completion+"%"} hint="Enrollment completion ratio" icon="chart"/><MetricCard label="Compliance risk" value={risk?.risk_band||intelligence?.risk_band||"—"} hint={(risk?.overdue??intelligence?.overdue_compliance??0)+" overdue"} icon="shield"/><MetricCard label="Skill gaps" value={intelligence?.skill_gaps??0} hint={(intelligence?.people_with_skill_gaps??0)+" people affected"} icon="target"/></div>
    <div className="two-column">
      <Section eyebrow="Learning velocity" title="30-day activity"><div className="compact-list">{(trends?.points??[]).slice(-10).map(point=><div className="compact-row" key={point.date}><div><strong>{point.date}</strong><small>{point.enrollments} enrollments · {point.completions} completions</small></div><BarChart3 size={16}/></div>)}</div></Section>
      <Section eyebrow="Compliance posture" title="Risk evidence"><div className="metric-strip"><span><b>{risk?.total??0}</b> total</span><span><b>{risk?.open??0}</b> open</span><span><b>{risk?.overdue??0}</b> overdue</span></div><div className="callout" style={{marginTop:12}}>Risk is derived from persisted compliance assignments; it is not an AI-generated judgment.</div></Section>
    </div>
    <Section eyebrow="Course performance" title="Portfolio completion"><div className="compact-list">{(performance?.courses??[]).slice(0,12).map(item=><div className="compact-row" key={item.course_id}><div><strong>{item.course}</strong><small>{item.enrollments} enrollments · {item.completions} completions</small></div><span className="proficiency">{item.completion_rate}%</span></div>)}</div>{!performance?.courses?.length?<EmptyState title="No course activity yet" description="Course performance will populate as tenant enrollments are recorded." icon={BarChart3}/>:null}</Section>
    <div className="two-column">
      <Section eyebrow="Learning effectiveness" title="Outcome efficiency"><div className="metric-strip"><span><b>{effectiveness?.completed??0}</b> completed</span><span><b>{effectiveness?.completion_rate??0}%</b> completion</span><span><b>{effectiveness?.average_days_to_complete??"—"}</b> avg days</span></div><div className="callout" style={{marginTop:12}}>Same persisted timestamp definition used by the Phase 6 Reports workspace.</div></Section>
      <Section eyebrow="Learner engagement" title="Participation reach"><div className="metric-strip"><span><b>{engagement?.enrolled_learners??0}</b> enrolled</span><span><b>{engagement?.active_learners??0}</b> active</span><span><b>{engagement?.learner_activation_rate??0}%</b> activation</span><span><b>{engagement?.learner_completion_reach??0}%</b> completion reach</span></div></Section>
    </div>
    <div className="two-column">
      <Section eyebrow="Assessment intelligence" title="Assessment outcomes"><div className="compact-list">{(assessments?.assessments??[]).slice(0,8).map(item=><div className="compact-row" key={item.assessment_id}><div><strong>{item.assessment}</strong><small>{item.submitted_attempts} submitted attempts · avg {item.average_score}%</small></div><span className="proficiency">{item.pass_rate}% pass</span></div>)}</div>{!assessments?.assessments?.length?<EmptyState title="No assessment outcomes yet" description="Assessment analytics populate after attempts are submitted." icon={BarChart3}/>:null}</Section>
      <Section eyebrow="Organization intelligence" title="Learning by org unit"><div className="compact-list">{(organization?.organization_units??[]).slice(0,8).map(item=><div className="compact-row" key={item.org_unit_id}><div><strong>{item.org_unit}</strong><small>{item.people} people</small></div><span className="proficiency">{item.completion_rate}%</span></div>)}</div>{!organization?.organization_units?.length?<EmptyState title="No org-unit analytics yet" description="Organization analytics populate from workforce org-unit placement." icon={UsersRound}/>:null}</Section>
    </div>
    <div className="two-column"><Section eyebrow="Workforce capability" title="Readiness signals"><div className="mini-list">{(intelligence?.top_skill_gaps??[]).map(item=><div className="mini-list-row" key={item.user_name+item.skill}><span><strong>{item.skill}</strong><small>{item.user_name} · {item.role}</small></span><span className="proficiency">gap {item.gap}</span></div>)}</div></Section><Section eyebrow="Action pipeline" title="Learning actions identified"><div className="compact-list">{(intelligence?.recommended_actions??[]).map((item,index)=><div className="compact-row" key={item.user_name+item.course_title+index}><div><strong>{item.course_title}</strong><small>{item.user_name} · {item.skill} · gap {item.gap}</small></div><BarChart3 size={16}/></div>)}</div></Section></div>
  </DashboardShell>;
}
