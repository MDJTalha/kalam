import Link from "next/link";
import { Activity, AlertTriangle, ArrowRight, Award, BookOpenCheck, CalendarDays, CheckCircle2, Clock3, FileText, ShieldCheck, Target, TrendingUp, UsersRound } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { LearningMomentumChart, WorkforceUnitChart } from "./dashboard-visuals";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type Summary = { users:number; courses:number; enrollments:number; completed_enrollments:number; certificates:number };
type Engagement = { active_learners:number; enrolled_learners:number; learner_activation_rate?:number; learner_completion_reach?:number };
type Trends = { days:number; points:Array<{date:string;enrollments:number;completions:number}> };
type Risk = { total:number; open:number; overdue:number; risk_band:string };
type Effectiveness = { completed:number; in_progress:number; completion_rate:number; average_days_to_complete:number|null; measured_completions:number };
type Course = { id:string; title:string; status:string; estimated_minutes?:number|null };
type CoursePage = { items:Course[]; total:number; page:number; page_size:number };
type Enrollment = { id:string; course_id:string; status:string; due_at?:string|null };
type Compliance = { id:string; requirement:string; status:string; due_state?:string };
type Intelligence = { population:number; skill_gaps:number; people_with_skill_gaps:number; open_compliance:number; overdue_compliance:number; risk_band:string; top_skill_gaps:{user_name:string;skill:string;gap:number}[]; recommended_actions?:{course_title:string;user_name:string;skill:string;gap:number}[] };
type Audit = { id:string; action:string; summary?:string|null; created_at:string };
type OrgUnit = { org_unit_id:string; org_unit:string; people:number; completion_rate:number };
type TeamMember = { id:string; email:string; first_name:string; last_name:string; job_title?:string|null; completed_learning:number; open_learning:number; overdue_learning:number; open_compliance:number; overdue_compliance:number; active_plans:number };
type QueueSummary = { pending_approval:number; waitlisted:number; total:number };
type LiveSession = { id:string; course_id:string; instructor_id?:string|null; title:string; starts_at:string; ends_at:string; status:string; location?:string|null };
type SessionAnalytics = { session:{id:string;title:string;starts_at:string;ends_at:string}; attendance:{total_marked:number;present:number;late:number;absent:number;excused:number;attendance_rate:number} };

const pct = (value:number,total:number) => total ? Math.round(value / total * 100) : 0;

export default async function DashboardPage(){
  const user = await requireUser<{ id:string; job_title?:string|null; org_unit_name?:string|null; roles?:Array<{name:string}>; permissions?:string[] }>();
  const permissions = user.permissions ?? [];
  const roleNames = (user.roles ?? []).map(role => role.name.toLowerCase());
  const jobTitle = (user.job_title ?? "").toLowerCase();
  const isTrainer = roleNames.some(name => name.includes("instructor") || name.includes("trainer")) || /trainer|instructor|facilitator/.test(jobTitle);
  const isManager = roleNames.some(name => name === "manager" || name.includes("manager")) || /manager|head of|department head/.test(jobTitle);
  const isHrBp = roleNames.some(name => name.includes("hrbp") || name.includes("hr business partner")) || /hrbp|hr business partner|human resources business partner/.test(jobTitle);
  const isLd = roleNames.some(name => name.includes("hr/l&d") || name.includes("l&d") || name.includes("learning")) || /l&d|learning and development|learning & development/.test(jobTitle);
  // Platform Developer uses the same standardized executive dashboard experience as tenant leadership.
  // Scope and permissions remain different; the product surface stays consistent across tenants.
  const isExecutive = roleNames.some(name => name.includes("tenant admin") || name.includes("global executive") || name.includes("executive") || name === "platform developer") || /ceo|chief|chro|coo|president|managing director/.test(jobTitle);
  const canReport = permissions.includes("reports.read");
  const canSeeCapability = permissions.includes("users.read");
  const canAudit = permissions.includes("audit.read");
  const roleMode = isExecutive ? "executive" : isLd ? "ld" : isHrBp ? "hrbp" : isManager ? "manager" : isTrainer ? "trainer" : "standard";
  const specializedView = roleMode !== "standard";
  const executiveView = roleMode === "executive" && canReport && canSeeCapability;
  const [enrollments,compliance,summary,engagement,intelligence,trends,risk,effectiveness,organization,audit,team,queue,sessions] = await Promise.all([
    apiJsonResult<Enrollment[]>("/api/v1/courses/my/enrollments").then((result) => result.ok ? result.data : null),
    apiJsonResult<Compliance[]>("/api/v1/compliance/my").then((result) => result.ok ? result.data : null),
    canReport ? apiJsonResult<Summary>("/api/v1/reports/summary").then((result) => result.ok ? result.data : null) : Promise.resolve(null),
    canReport ? apiJsonResult<Engagement>("/api/v1/reports/engagement").then((result) => result.ok ? result.data : null) : Promise.resolve(null),
    canSeeCapability ? apiJsonResult<Intelligence>("/api/v1/intelligence/capability").then((result) => result.ok ? result.data : null) : Promise.resolve(null),
    executiveView || isLd ? apiJsonResult<Trends>("/api/v1/reports/learning-trends?days=30").then((result) => result.ok ? result.data : null) : Promise.resolve(null),
    canReport ? apiJsonResult<Risk>("/api/v1/reports/compliance-risk").then((result) => result.ok ? result.data : null) : Promise.resolve(null),
    canReport ? apiJsonResult<Effectiveness>("/api/v1/reports/learning-effectiveness").then((result) => result.ok ? result.data : null) : Promise.resolve(null),
    canReport ? apiJsonResult<{organization_units:OrgUnit[]}>("/api/v1/reports/organization-performance").then((result) => result.ok ? result.data : null) : Promise.resolve(null),
    canAudit ? apiJsonResult<Audit[]>("/api/v1/admin/audit?limit=5").then((result) => result.ok ? result.data : null) : Promise.resolve(null),
    (isManager || isHrBp) && canSeeCapability ? apiJsonResult<TeamMember[]>("/api/v1/people/team").then((result) => result.ok ? result.data : null) : Promise.resolve(null),
    isLd && permissions.includes("courses.manage") ? apiJsonResult<QueueSummary>("/api/v1/courses/operations/enrollment-queue?page=1&page_size=1&status=all&q=").then((result) => result.ok ? result.data : null) : Promise.resolve(null),
    isTrainer ? apiJsonResult<LiveSession[]>("/api/v1/sessions").then((result) => result.ok ? result.data : null) : Promise.resolve(null),
  ]);
  const assigned = enrollments?.length ?? 0;
  const completed = enrollments?.filter(row => row.status === "completed").length ?? 0;
  const openCompliance = compliance?.filter(row => !["completed","excepted"].includes(row.status)).length ?? 0;
  // Request-time clock is used for server-rendered due dates.
  // eslint-disable-next-line react-hooks/purity
  const now = Date.now();
  const upcoming = (enrollments ?? []).filter(row => row.due_at && row.status !== "completed" && new Date(row.due_at).getTime() >= now)
    .sort((a,b) => new Date(a.due_at!).getTime() - new Date(b.due_at!).getTime()).slice(0,4);
  const courseParams = new URLSearchParams({ page: "1", page_size: String(Math.max(1, upcoming.length)) });
  upcoming.forEach(row => courseParams.append("course_ids", row.course_id));
  const [courseLookup,catalogCount] = await Promise.all([
    upcoming.length
      ? apiJsonResult<CoursePage>(`/api/v1/courses/page?${courseParams}`)
      : Promise.resolve({ ok: true, data: { items: [], total: 0, page: 1, page_size: 1 }, status: 200, error: null }),
    apiJsonResult<CoursePage>("/api/v1/courses/page?page=1&page_size=1"),
  ]);
  const courseNames = new Map((courseLookup.data?.items ?? []).map(row => [row.id,row.title]));
  const quickActions = [
    {label:"Explore learning",href:"/dashboard/catalog",icon:BookOpenCheck,permission:"learning.access"},
    {label:"Create learning",href:"/dashboard/catalog/new",icon:BookOpenCheck,permission:"courses.manage"},
    {label:"Open L&D operations",href:"/dashboard/ld-operations",icon:Activity,permission:"courses.manage"},
    {label:"Open team workspace",href:"/dashboard/team",icon:UsersRound,permission:"users.read"},
    {label:"Add user",href:"/dashboard/people/admin",icon:UsersRound,permission:"users.manage"},
    {label:"Review compliance",href:"/dashboard/compliance/admin",icon:ShieldCheck,permission:"compliance.manage"},
    {label:"Open analytics",href:"/dashboard/analytics",icon:Activity,permission:"reports.read"},
    {label:"Open commercial CRM",href:"/dashboard/saas",icon:Target,permission:"saas.crm.read"},
  ].filter(action => permissions.includes(action.permission));
  const coreUnavailable = !courseLookup.ok || !catalogCount.ok || enrollments === null || compliance === null;
  const metric = (label:string,value:string | number,detail:string,Icon:typeof Activity) =>
    <div className="stat-card stat-card-enhanced" key={label}><div className="metric-card-top"><span>{label}</span><Icon size={16} aria-hidden="true"/></div><strong>{value}</strong><small>{detail}</small></div>;
  const learnerActivation = engagement?.learner_activation_rate ?? null;
  const capabilityExposure = intelligence && intelligence.population > 0 ? pct(intelligence.people_with_skill_gaps, intelligence.population) : null;
  const complianceExposure = risk && risk.open > 0 ? pct(risk.overdue, risk.open) : null;
  const trendPoints = trends?.points ?? [];
  const currentWeek = trendPoints.slice(-7);
  const previousWeek = trendPoints.slice(-14,-7);
  const currentEnrollments = currentWeek.reduce((total,point) => total + point.enrollments,0);
  const previousEnrollments = previousWeek.reduce((total,point) => total + point.enrollments,0);
  const currentCompletions = currentWeek.reduce((total,point) => total + point.completions,0);
  const previousCompletions = previousWeek.reduce((total,point) => total + point.completions,0);
  const delta = (current:number,previous:number) => previous > 0 ? Math.round(((current-previous)/previous)*100) : null;
  const enrollmentMomentum = delta(currentEnrollments,previousEnrollments);
  const completionMomentum = delta(currentCompletions,previousCompletions);
  const actionSignals = intelligence?.recommended_actions ? Array.from(new Map(intelligence.recommended_actions.map(item => [`${item.course_title}|${item.skill}`, item])).values()).slice(0,3) : [];
  const orgUnits = organization?.organization_units?.slice(0,6) ?? [];
  const leadingGaps = intelligence?.top_skill_gaps?.slice(0,5) ?? [];
  const teamMembers = team ?? [];
  const teamLearningTotal = teamMembers.reduce((total,member) => total + member.completed_learning + member.open_learning,0);
  const teamLearningCompleted = teamMembers.reduce((total,member) => total + member.completed_learning,0);
  const teamCompletionRate = teamLearningTotal ? Math.round(teamLearningCompleted / teamLearningTotal * 100) : null;
  const teamAttention = teamMembers.filter(member => member.overdue_learning > 0 || member.overdue_compliance > 0 || member.active_plans === 0).sort((a,b) => (b.overdue_learning+b.overdue_compliance) - (a.overdue_learning+a.overdue_compliance)).slice(0,5);
  const teamOverdueLearning = teamMembers.reduce((total,member) => total + member.overdue_learning,0);
  const teamOverdueCompliance = teamMembers.reduce((total,member) => total + member.overdue_compliance,0);
  const trainerSessions = (sessions ?? []).filter(session => session.instructor_id === user.id).sort((a,b) => new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime());
  const trainerUpcoming = trainerSessions.filter(session => new Date(session.ends_at).getTime() >= now).slice(0,5);
  const trainerRecent = trainerSessions.filter(session => new Date(session.ends_at).getTime() < now).slice(-4);
  const trainerSessionAnalytics = isTrainer ? await Promise.all(trainerRecent.map(session => apiJsonResult<SessionAnalytics>(`/api/v1/sessions/${session.id}/analytics`).then((result) => result.ok ? result.data : null))) : [];
  const trainerMarked = trainerSessionAnalytics.reduce((total,item) => total + (item?.attendance.total_marked ?? 0),0);
  const trainerPresent = trainerSessionAnalytics.reduce((total,item) => total + (item?.attendance.present ?? 0) + (item?.attendance.late ?? 0),0);
  const trainerAttendance = trainerMarked ? Math.round(trainerPresent / trainerMarked * 100) : null;
  const roleCopy = {
    executive:{eyebrow:"Workforce intelligence",title:"Lead Workforce Capability.",description:"See where capability, learning, and compliance require leadership attention—at a glance.",primary:"Open workforce analytics",href:"/dashboard/analytics"},
    ld:{eyebrow:"Learning & capability leadership",title:"Build Capability at Scale.",description:"Connect learning performance, capability gaps and delivery operations into one view of L&D effectiveness.",primary:"Open L&D analytics",href:"/dashboard/analytics"},
    hrbp:{eyebrow:"Workforce partnership",title:"Strengthen Your Workforce.",description:"Understand the people, capability and compliance signals across the workforce you support.",primary:"Open workforce analytics",href:"/dashboard/analytics"},
    manager:{eyebrow:"Team leadership",title:"Lead Your Team.",description:"Focus on the people, learning, compliance and development signals that need your attention.",primary:"Open team workspace",href:"/dashboard/team"},
    trainer:{eyebrow:"Learning delivery",title:"Deliver Learning.",description:"See what you are delivering, who is attending, and where learner follow-up is needed.",primary:"Open sessions",href:"/dashboard/sessions"},
    standard:{eyebrow:"Learning, capability and evidence",title:"Your workforce at a glance",description:"Review recorded learning and compliance work. Organization measures appear when your role has reporting access.",primary:"Explore learning",href:"/dashboard/catalog"},
  }[roleMode];

  return <DashboardShell title={roleMode === "executive" ? "Executive Overview" : roleMode === "manager" ? "Team Overview" : roleMode === "ld" ? "L&D Overview" : roleMode === "hrbp" ? "Workforce Overview" : roleMode === "trainer" ? "Delivery Overview" : "Overview"} eyebrow={roleCopy.eyebrow}>
    <section className="dashboard-command-hero" aria-labelledby="dashboard-command-title">
      <div className="dashboard-command-copy">
        <h2 id="dashboard-command-title">{roleCopy.title}</h2>
        <p>{roleCopy.description}</p>
        <div className="dashboard-command-actions"><Link className="ds-button ds-button-primary" href={roleCopy.href}>{roleCopy.primary}</Link>
          {canReport && <Link className="ds-button ds-button-secondary" href="/dashboard/reports">Open reports</Link>}</div>
      </div>
    </section>
    {coreUnavailable && <section className="data-panel" role="alert"><strong>Some workspace data is unavailable.</strong><p>Learning or compliance records could not be loaded. Refresh or try again later; unavailable values are shown as a dash.</p></section>}
    {executiveView && <section className="executive-panel" aria-labelledby="executive-snapshot-title">
      <div className="executive-head"><div><span className="eyebrow">Executive pulse</span><h2 id="executive-snapshot-title">The signals that matter.</h2></div></div>
      <div className="executive-kpi-grid">
        <div className="executive-kpi"><div><span>Learner activation</span><TrendingUp size={17}/></div><strong>{learnerActivation === null ? "—" : `${learnerActivation}%`}</strong><small>{engagement?.active_learners ?? "—"} active of {engagement?.enrolled_learners ?? "—"} enrolled learners</small></div>
        <div className="executive-kpi"><div><span>Capability exposure</span><Target size={17}/></div><strong>{capabilityExposure === null ? "—" : `${capabilityExposure}%`}</strong><small>{intelligence?.people_with_skill_gaps ?? "—"} people with recorded skill gaps</small></div>
        <div className="executive-kpi executive-kpi-risk"><div><span>Compliance exposure</span><AlertTriangle size={17}/></div><strong>{complianceExposure === null ? "—" : `${complianceExposure}%`}</strong><small>{risk?.overdue ?? "—"} overdue of {risk?.open ?? "—"} open obligations</small></div>
        <div className="executive-kpi"><div><span>Learning effectiveness</span><CheckCircle2 size={17}/></div><strong>{effectiveness ? `${effectiveness.completion_rate}%` : "—"}</strong><small>{effectiveness?.average_days_to_complete ?? "—"} average days to complete</small></div>
      </div>
      <div className="executive-insight-grid">
        <div className="executive-insight-card"><div className="executive-insight-heading"><span>Capability signal</span><b>{intelligence?.risk_band || "—"} risk band</b></div><p>{intelligence ? `${intelligence.skill_gaps} mapped skill gaps affecting ${intelligence.people_with_skill_gaps} people in the current intelligence population.` : "Capability intelligence is unavailable."}</p><Link href="/dashboard/skills">Review capability signals <Target size={14}/></Link></div>
        <div className="executive-insight-card"><div className="executive-insight-heading"><span>Learning momentum</span><b>{enrollmentMomentum === null && completionMomentum === null ? "30-day view" : "vs prior 7 days"}</b></div><div className="executive-momentum"><span><b>{enrollmentMomentum === null ? "—" : `${enrollmentMomentum > 0 ? "+" : ""}${enrollmentMomentum}%`}</b><small>enrollment movement</small></span><span><b>{completionMomentum === null ? "—" : `${completionMomentum > 0 ? "+" : ""}${completionMomentum}%`}</b><small>completion movement</small></span></div><Link href="/dashboard/analytics">Open learning trends <ArrowRight size={14}/></Link></div>
      </div>
    </section>}
    {executiveView && <>
      <section className="executive-attention-grid" aria-label="Leadership attention">
        <div className="executive-attention-card executive-attention-risk">
          <div className="executive-attention-icon"><AlertTriangle size={17}/></div>
          <div><span>Compliance exposure</span><strong>{risk?.overdue ?? "—"} overdue</strong><small>{risk ? `${risk.open} open obligations · ${risk.risk_band} recorded risk band` : "Risk data unavailable"}</small></div>
          <Link href="/dashboard/compliance" aria-label="Review compliance exposure"><ArrowRight size={14} aria-hidden="true"/></Link>
        </div>
        <div className="executive-attention-card">
          <div className="executive-attention-icon"><Target size={17}/></div>
          <div><span>Capability exposure</span><strong>{intelligence?.people_with_skill_gaps ?? "—"} people</strong><small>{intelligence ? `${intelligence.skill_gaps} mapped skill gaps in the current population` : "Capability data unavailable"}</small></div>
          <Link href="/dashboard/skills" aria-label="Review capability exposure"><ArrowRight size={14} aria-hidden="true"/></Link>
        </div>
        <div className="executive-attention-card">
          <div className="executive-attention-icon"><BookOpenCheck size={17}/></div>
          <div><span>Action signals</span><strong>{actionSignals.length || "—"} surfaced</strong><small>{actionSignals.length ? "Learning interventions already connected to recorded capability gaps" : "No connected intervention signals are currently recorded"}</small></div>
          <Link href="/dashboard/analytics" aria-label="Review learning action signals"><ArrowRight size={14} aria-hidden="true"/></Link>
        </div>
      </section>
      <div className="executive-dashboard-grid">
        <section className="executive-data-panel">
          <div className="executive-section-head"><div><span className="eyebrow">Workforce movement</span><h2>Recent learning momentum</h2></div><Link href="/dashboard/analytics">30-day analytics <ArrowRight size={14}/></Link></div>
          <LearningMomentumChart points={trendPoints} />
        </section>
        <section className="executive-data-panel">
          <div className="executive-section-head"><div><span className="eyebrow">Organizational view</span><h2>Performance by workforce unit</h2></div><Link href="/dashboard/analytics">View full analysis <ArrowRight size={14}/></Link></div>
          <WorkforceUnitChart units={orgUnits} />
        </section>
      </div>
      <div className="executive-dashboard-grid">
        <section className="executive-data-panel">
          <div className="executive-section-head"><div><span className="eyebrow">Capability priorities</span><h2>Leading recorded gaps</h2></div><Link href="/dashboard/skills">Open capability intelligence <ArrowRight size={14}/></Link></div>
          {leadingGaps.length ? <div className="executive-gap-list">{leadingGaps.map((gap,index) => <div className="executive-gap-row" key={gap.user_name+gap.skill+index}><span className="executive-gap-rank">{String(index+1).padStart(2,"0")}</span><div><strong>{gap.skill}</strong><small>{gap.user_name} · recorded gap {gap.gap}</small></div><Target size={14}/></div>)}</div> : <div className="executive-empty">No capability gaps are currently surfaced.</div>}
        </section>
        <section className="executive-data-panel">
          <div className="executive-section-head"><div><span className="eyebrow">Intervention pipeline</span><h2>Connected learning actions</h2></div><Link href="/dashboard/analytics">View action pipeline <ArrowRight size={14}/></Link></div>
          {actionSignals.length ? <div className="executive-gap-list">{actionSignals.map((action,index) => <div className="executive-gap-row" key={action.course_title+action.skill+index}><span className="executive-gap-rank"><BookOpenCheck size={13}/></span><div><strong>{action.course_title}</strong><small>{action.skill} · {action.user_name} · gap {action.gap}</small></div><ArrowRight size={14}/></div>)}</div> : <div className="executive-empty">No capability-linked learning actions are currently recorded.</div>}
        </section>
      </div>
      <section className="executive-leadership-footer">
        <div><span className="eyebrow">Leadership next step</span><h2>Move from signal to evidence.</h2><p>Use the executive snapshot for orientation, then open analytics, capability or compliance evidence to investigate the population behind each signal.</p></div>
        <div className="executive-leadership-actions"><Link href="/dashboard/analytics">Workforce analytics <ArrowRight size={15}/></Link><Link href="/dashboard/skills">Capability intelligence <ArrowRight size={15}/></Link><Link href="/dashboard/compliance">Compliance posture <ArrowRight size={15}/></Link></div>
      </section>
    </>}
    {roleMode === "ld" && <section className="role-dashboard" aria-label="L&D leadership dashboard"><div className="role-kpi-grid"><div className="role-kpi"><span>Approval queue</span><strong>{queue?.pending_approval ?? "—"}</strong><small>Enrollment decisions awaiting action</small></div><div className="role-kpi"><span>Waitlisted</span><strong>{queue?.waitlisted ?? "—"}</strong><small>Learners waiting for capacity</small></div><div className="role-kpi"><span>Capability gaps</span><strong>{intelligence?.skill_gaps ?? "—"}</strong><small>{intelligence?.people_with_skill_gaps ?? "—"} people affected</small></div><div className="role-kpi"><span>Learning effectiveness</span><strong>{effectiveness ? effectiveness.completion_rate + "%" : "—"}</strong><small>{effectiveness?.average_days_to_complete ?? "—"} average days to complete</small></div></div><div className="role-grid-two"><section className="role-panel"><div className="role-panel-head"><div><span className="eyebrow">Capability priorities</span><h2>Where L&D should focus</h2></div><Link href="/dashboard/skills">Open capability intelligence <ArrowRight size={14}/></Link></div>{leadingGaps.length ? <div className="role-list">{leadingGaps.map((gap,index) => <div className="role-list-row" key={gap.user_name+gap.skill+index}><span className="role-rank">{String(index+1).padStart(2,"0")}</span><div><strong>{gap.skill}</strong><small>{gap.user_name} · gap {gap.gap}</small></div><Target size={14}/></div>)}</div> : <div className="role-empty">No recorded capability gaps.</div>}</section><section className="role-panel"><div className="role-panel-head"><div><span className="eyebrow">Learning delivery</span><h2>Movement and intervention</h2></div><Link href="/dashboard/ld-operations">Open L&D operations <ArrowRight size={14}/></Link></div><LearningMomentumChart points={trendPoints}/><div className="role-metric-strip"><span><b>{enrollmentMomentum === null ? "—" : (enrollmentMomentum > 0 ? "+" : "") + enrollmentMomentum + "%"}</b> enrollments</span><span><b>{completionMomentum === null ? "—" : (completionMomentum > 0 ? "+" : "") + completionMomentum + "%"}</b> completions</span><span><b>{actionSignals.length || "—"}</b> linked actions</span></div>{actionSignals.length ? <div className="role-list">{actionSignals.map((action,index) => <div className="role-list-row" key={action.course_title+action.skill+index}><span className="role-rank"><BookOpenCheck size={13}/></span><div><strong>{action.course_title}</strong><small>{action.skill} · {action.user_name}</small></div><ArrowRight size={14}/></div>)}</div> : <div className="role-empty">No capability-linked interventions are currently recorded.</div>}</section></div></section>}
    {roleMode === "hrbp" && <section className="role-dashboard" aria-label="HR business partner dashboard"><div className="role-kpi-grid"><div className="role-kpi"><span>Workforce</span><strong>{summary?.users ?? "—"}</strong><small>People in the current workforce view</small></div><div className="role-kpi"><span>Capability exposure</span><strong>{capabilityExposure === null ? "—" : capabilityExposure + "%"}</strong><small>{intelligence?.people_with_skill_gaps ?? "—"} people with recorded gaps</small></div><div className="role-kpi role-kpi-risk"><span>Compliance exposure</span><strong>{complianceExposure === null ? "—" : complianceExposure + "%"}</strong><small>{risk?.overdue ?? "—"} overdue obligations</small></div><div className="role-kpi"><span>Learning completion</span><strong>{summary ? pct(summary.completed_enrollments,summary.enrollments) + "%" : "—"}</strong><small>Current enrollment completion</small></div></div><div className="role-grid-two"><section className="role-panel"><div className="role-panel-head"><div><span className="eyebrow">Organization</span><h2>Performance across the workforce</h2></div><Link href="/dashboard/analytics">Open workforce analytics <ArrowRight size={14}/></Link></div><WorkforceUnitChart units={orgUnits} /></section><section className="role-panel"><div className="role-panel-head"><div><span className="eyebrow">People signals</span><h2>Capability areas needing attention</h2></div><Link href="/dashboard/skills">Review capability signals <ArrowRight size={14}/></Link></div>{leadingGaps.length ? <div className="role-list">{leadingGaps.slice(0,5).map((gap,index) => <div className="role-list-row" key={gap.user_name+gap.skill+index}><span className="role-rank">{String(index+1).padStart(2,"0")}</span><div><strong>{gap.skill}</strong><small>{gap.user_name} · gap {gap.gap}</small></div><Target size={14}/></div>)}</div> : <div className="role-empty">No capability gaps are currently surfaced.</div>}</section></div></section>}
    {roleMode === "manager" && <section className="role-dashboard" aria-label="Manager dashboard"><div className="role-kpi-grid"><div className="role-kpi"><span>Team</span><strong>{teamMembers.length}</strong><small>Direct reports in your team</small></div><div className="role-kpi"><span>Learning completion</span><strong>{teamCompletionRate === null ? "—" : teamCompletionRate + "%"}</strong><small>Across tracked team learning</small></div><div className="role-kpi role-kpi-risk"><span>Overdue learning</span><strong>{teamOverdueLearning}</strong><small>Items requiring follow-up</small></div><div className="role-kpi role-kpi-risk"><span>Overdue compliance</span><strong>{teamOverdueCompliance}</strong><small>Team obligations past due</small></div></div><section className="role-panel"><div className="role-panel-head"><div><span className="eyebrow">Manager attention</span><h2>People who need follow-up</h2></div><Link href="/dashboard/team">Open team workspace <ArrowRight size={14}/></Link></div>{teamAttention.length ? <div className="role-list">{teamAttention.map(member => <div className="role-list-row" key={member.id}><span className="role-rank"><UsersRound size={13}/></span><div><strong>{member.first_name} {member.last_name}</strong><small>{member.job_title || "Team member"} · {member.overdue_learning} overdue learning · {member.overdue_compliance} overdue compliance</small></div><ArrowRight size={14}/></div>)}</div> : <div className="role-empty">No immediate team follow-up signals are recorded.</div>}</section></section>}
    {roleMode === "trainer" && <section className="role-dashboard" aria-label="Trainer dashboard"><div className="role-kpi-grid"><div className="role-kpi"><span>Upcoming sessions</span><strong>{trainerUpcoming.length}</strong><small>Your next scheduled deliveries</small></div><div className="role-kpi"><span>Sessions delivered</span><strong>{trainerSessions.filter(session => new Date(session.ends_at).getTime() < now).length}</strong><small>Completed schedule records</small></div><div className="role-kpi"><span>Attendance</span><strong>{trainerAttendance === null ? "—" : trainerAttendance + "%"}</strong><small>Across recent marked sessions</small></div><div className="role-kpi"><span>Assigned learners</span><strong>{assigned}</strong><small>Your current learning assignments</small></div></div><section className="role-panel"><div className="role-panel-head"><div><span className="eyebrow">Your delivery</span><h2>Upcoming sessions</h2></div><Link href="/dashboard/sessions">Open sessions <ArrowRight size={14}/></Link></div>{trainerUpcoming.length ? <div className="role-list">{trainerUpcoming.map(session => <div className="role-list-row" key={session.id}><span className="role-rank"><CalendarDays size={13}/></span><div><strong>{session.title}</strong><small>{new Date(session.starts_at).toLocaleString()} · {session.location || "Location not set"}</small></div><ArrowRight size={14}/></div>)}</div> : <div className="role-empty">No upcoming sessions are assigned to you.</div>}</section></section>}
    {!specializedView && <section className="stat-grid enterprise-kpis" aria-label="Workspace measures">
      {metric("My enrollments",enrollments ? assigned : "—","Assigned learning records",BookOpenCheck)}
      {metric("My completions",enrollments ? completed : "—","Completed enrollments",CheckCircle2)}
      {metric("Open obligations",compliance ? openCompliance : "—","Assigned compliance actions",ShieldCheck)}
      {metric("Course catalog",catalogCount.ok ? catalogCount.data?.total ?? "—" : "—","Courses visible to this role",BookOpenCheck)}
      {canReport && metric("Workforce people",summary?.users ?? "—","Workforce records",UsersRound)}
      {canReport && metric("Active learners",engagement?.active_learners ?? "—","Distinct active learners",Activity)}
      {canReport && metric("Enrollment completion",summary ? `${pct(summary.completed_enrollments,summary.enrollments)}%` : "—","Workforce enrollment ratio",CheckCircle2)}
      {canReport && metric("Issued credentials",summary?.certificates ?? "—","Workforce certificate records",Award)}
    </section>}
    {!specializedView && <>
    <div className="dashboard-grid-two">
      <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Learning priorities</span><h2>Upcoming due dates</h2></div><Link className="text-link" href="/dashboard/catalog">Open learning</Link></div>
        {upcoming.length ? <div className="compact-list">{upcoming.map(row => <div className="compact-row" key={row.id}><div><strong>{courseNames.get(row.course_id) ?? "Assigned course"}</strong><small>Due {new Date(row.due_at!).toLocaleDateString()} · {row.status.replaceAll("_"," ")}</small></div><Clock3 size={16} aria-hidden="true"/></div>)}</div>
        : <div className="empty-state"><Clock3 size={22} aria-hidden="true"/><p>{enrollments === null ? "Due dates are unavailable." : "No upcoming course due dates are recorded."}</p></div>}
      </section>
      <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Capability evidence</span><h2>Recorded skill gaps</h2></div><Link className="text-link" href="/dashboard/skills">View capabilities</Link></div>
        {canSeeCapability ? intelligence ? <><div className="metric-strip"><span><b>{intelligence.skill_gaps}</b> mapped gaps</span><span><b>{intelligence.people_with_skill_gaps}</b> people affected</span><span><b>{intelligence.risk_band}</b> risk band</span></div>
          <div className="compact-list">{intelligence.top_skill_gaps.slice(0,3).map((gap,index) => <div className="compact-row" key={gap.user_name+gap.skill+index}><div><strong>{gap.skill}</strong><small>{gap.user_name} · gap {gap.gap}</small></div><Target size={16} aria-hidden="true"/></div>)}</div></>
          : <p role="alert">Capability measures are unavailable right now.</p> : <p>Capability measures are available to authorized workforce administrators.</p>}
      </section>
    </div>
    <div className="dashboard-grid-two">
      {canAudit && <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Audit evidence</span><h2>Recent recorded activity</h2></div><Link className="text-link" href="/dashboard/audit">View audit trail</Link></div>
        {audit === null ? <p role="alert">Audit activity is unavailable.</p> : audit.length ? <div className="timeline-list">{audit.map((event,index) => <div className="timeline-item" key={event.id}><span className="timeline-number">{index+1}</span><div><strong>{event.summary || event.action.replaceAll("."," ")}</strong><small>{new Date(event.created_at).toLocaleString()}</small></div><FileText size={14} aria-hidden="true"/></div>)}</div>
        : <div className="empty-state"><p>No audited actions are recorded yet.</p></div>}
      </section>}
      <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Workspace actions</span><h2>Continue your work</h2></div></div>
        <div className="quick-actions">{quickActions.map(({label,href,icon:Icon}) => <Link href={href} key={href}><Icon size={16} aria-hidden="true"/><span>{label}</span></Link>)}</div>
        {!quickActions.length && <p>Open the navigation to review the workspaces available to your role.</p>}
      </section>
    </div>
    <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Source clarity</span><h2>How to interpret this view</h2></div></div>
      <p>Personal counts come from your enrollments and compliance assignments. Tenant totals and the audit trail are shown only for authorized roles. A dash indicates unavailable data; no activity is simulated.</p>
    </section>
    </>}
  </DashboardShell>;
}
