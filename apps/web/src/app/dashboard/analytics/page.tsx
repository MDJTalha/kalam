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
  const user=await requireUser<{permissions?:string[]}>();
  const canReadCapability=user.permissions?.includes("users.read")??false;
  if(!user.permissions?.includes("reports.read")) return <DashboardShell title="Executive analytics" eyebrow="Decision-ready workforce intelligence"><section className="data-panel" role="alert"><h2>Analytics access restricted</h2><p>Your role does not include reporting access.</p></section></DashboardShell>;
  const [summary,intelligence,trends,performance,risk,effectiveness,engagement,assessments,organization]=await Promise.all([
    apiJson<Summary>("/api/v1/reports/summary"),
    canReadCapability?apiJson<Intelligence>("/api/v1/intelligence/capability"):Promise.resolve(null),
    apiJson<Trends>("/api/v1/reports/learning-trends?days=30"),
    apiJson<Performance>("/api/v1/reports/course-performance?page=1&page_size=12&sort_by=enrollments&sort_dir=desc"),
    apiJson<Risk>("/api/v1/reports/compliance-risk"),
    apiJson<Effectiveness>("/api/v1/reports/learning-effectiveness"),
    apiJson<Engagement>("/api/v1/reports/engagement"),
    apiJson<{assessments:Assessment[]}>("/api/v1/reports/assessment-performance"),
    apiJson<{organization_units:OrgUnit[]}>("/api/v1/reports/organization-performance"),
  ]);
  const completion=summary ? (summary.enrollments?Math.round(summary.completed_enrollments/summary.enrollments*100):0) : null;
  const missing=[summary,trends,performance,risk,effectiveness,engagement,assessments,organization,...(canReadCapability?[intelligence]:[])].some(value=>value===null);
  return <DashboardShell title="Executive analytics" eyebrow="Decision-ready workforce intelligence" breadcrumbs={[{label:"Reports",href:"/dashboard/reports"},{label:"Executive analytics"}]}>
    {missing && <section className="data-panel" role="alert"><h2>Some analytics are unavailable</h2><p>One or more reporting sources could not be loaded. A dash means unavailable data, not zero activity.</p></section>}
    <div className="stat-grid"><MetricCard label="Workforce" value={summary?.users??"—"} hint="Workforce population" icon="users"/><MetricCard label="Completion" value={completion===null?"—":completion+"%"} hint="Enrollment completion ratio" icon="chart"/><MetricCard label="Compliance risk" value={risk?.risk_band||intelligence?.risk_band||"—"} hint={risk||intelligence?(risk?.overdue??intelligence?.overdue_compliance??0)+" overdue":"Data unavailable"} icon="shield"/><MetricCard label="Skill gaps" value={canReadCapability?intelligence?.skill_gaps??"—":"Restricted"} hint={canReadCapability?(intelligence?intelligence.people_with_skill_gaps+" people affected":"Data unavailable"):"Requires workforce access"} icon="target"/></div>
    <div className="two-column">
      <Section eyebrow="Learning velocity" title="30-day activity">{trends?.points?.length?<div className="compact-list">{trends.points.slice(-10).map(point=><div className="compact-row" key={point.date}><div><strong>{point.date}</strong><small>{point.enrollments} enrollments · {point.completions} completions</small></div><BarChart3 size={16}/></div>)}</div>:<EmptyState title="No learning activity yet" description="Enrollment and completion activity will appear here once learners begin using the workspace." icon={BarChart3}/>}</Section>
      <Section eyebrow="Compliance posture" title="Risk evidence"><div className="metric-strip"><span><b>{risk?.total??"—"}</b> total</span><span><b>{risk?.open??"—"}</b> open</span><span><b>{risk?.overdue??"—"}</b> overdue</span></div><div className="callout saas-spaced-callout">Risk is derived from persisted compliance assignments; it is not an AI-generated judgment.</div></Section>
    </div>
    <Section eyebrow="Course performance" title="Portfolio completion"><div className="compact-list">{(performance?.courses??[]).slice(0,12).map(item=><div className="compact-row" key={item.course_id}><div><strong>{item.course}</strong><small>{item.enrollments} enrollments · {item.completions} completions</small></div><span className="proficiency">{item.completion_rate}%</span></div>)}</div>{performance && !performance.courses.length?<EmptyState title="No course activity yet" description="Course performance will populate as tenant enrollments are recorded." icon={BarChart3}/>:null}</Section>
    <div className="two-column">
      <Section eyebrow="Learning effectiveness" title="Outcome efficiency"><div className="metric-strip"><span><b>{effectiveness?.completed??"—"}</b> completed</span><span><b>{effectiveness?.completion_rate??"—"}%</b> completion</span><span><b>{effectiveness?.average_days_to_complete??"—"}</b> avg days</span></div><div className="callout saas-spaced-callout">The same persisted timestamp definition is used across the reporting workspace.</div></Section>
      <Section eyebrow="Learner engagement" title="Participation reach"><div className="metric-strip"><span><b>{engagement?.enrolled_learners??"—"}</b> enrolled</span><span><b>{engagement?.active_learners??"—"}</b> active</span><span><b>{engagement?.learner_activation_rate??"—"}%</b> activation</span><span><b>{engagement?.learner_completion_reach??"—"}%</b> completion reach</span></div></Section>
    </div>
    <div className="two-column">
      <Section eyebrow="Assessment intelligence" title="Assessment outcomes"><div className="compact-list">{(assessments?.assessments??[]).slice(0,8).map(item=><div className="compact-row" key={item.assessment_id}><div><strong>{item.assessment}</strong><small>{item.submitted_attempts} submitted attempts · avg {item.average_score}%</small></div><span className="proficiency">{item.pass_rate}% pass</span></div>)}</div>{assessments && !assessments.assessments.length?<EmptyState title="No assessment outcomes yet" description="Assessment analytics populate after attempts are submitted." icon={BarChart3}/>:null}</Section>
      <Section eyebrow="Organization intelligence" title="Learning by org unit"><div className="compact-list">{(organization?.organization_units??[]).slice(0,8).map(item=><div className="compact-row" key={item.org_unit_id}><div><strong>{item.org_unit}</strong><small>{item.people} people</small></div><span className="proficiency">{item.completion_rate}%</span></div>)}</div>{organization && !organization.organization_units.length?<EmptyState title="No org-unit analytics yet" description="Organization analytics populate from workforce org-unit placement." icon={UsersRound}/>:null}</Section>
    </div>
    <div className="two-column"><Section eyebrow="Workforce capability" title="Readiness signals">{intelligence?.top_skill_gaps?.length?<div className="mini-list">{intelligence.top_skill_gaps.map(item=><div className="mini-list-row" key={item.user_name+item.skill}><span><strong>{item.skill}</strong><small>{item.user_name} · {item.role}</small></span><span className="proficiency">gap {item.gap}</span></div>)}</div>:<EmptyState title="No capability gaps surfaced" description={canReadCapability?"Capability intelligence will appear after role requirements and evidence are recorded.":"Capability intelligence requires workforce access."} icon="target"/>}</Section><Section eyebrow="Action pipeline" title="Learning actions identified">{intelligence?.recommended_actions?.length?<div className="compact-list">{intelligence.recommended_actions.map((item,index)=><div className="compact-row" key={item.user_name+item.course_title+index}><div><strong>{item.course_title}</strong><small>{item.user_name} · {item.skill} · gap {item.gap}</small></div><BarChart3 size={16}/></div>)}</div>:<EmptyState title="No actions identified" description="Recommended learning actions will appear when capability gaps are connected to learning interventions." icon={BarChart3}/>}</Section></div>
  </DashboardShell>;
}
