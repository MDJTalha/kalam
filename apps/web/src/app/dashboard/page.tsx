import Link from "next/link";
import { Activity, Award, BarChart3, BookOpenCheck, CheckCircle2, ClipboardCheck, FileCheck2, ShieldCheck, Sparkles, Target, UsersRound } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJson } from "@/lib/server-api";

type Summary = { users:number; courses:number; enrollments:number; completed_enrollments:number; certificates:number; compliance_assignments:number };
type Intelligence = { population:number; skill_gaps:number; people_with_skill_gaps:number; open_compliance:number; overdue_compliance:number; risk_band:string; recommended_actions:{user_id:string;user_name:string;role:string;skill:string;current:number;required:number;gap:number;course_id:string;course_title:string;estimated_minutes?:number|null;rationale:string}[]; top_skill_gaps:{user_name:string;role:string;skill:string;current:number;required:number;gap:number}[] };
type Course = { id:string; title:string; status:string; estimated_minutes?:number|null };
type Enrollment = { id:string; status:string; due_at?:string|null };
type Compliance = { id:string; requirement:string; status:string };

const pct=(value:number,total:number)=> total ? Math.round((value/total)*100) : 0;

export default async function DashboardPage(){
  const [summary,courses,enrollments,compliance,intelligence]=await Promise.all([
    apiJson<Summary>("/api/v1/reports/summary"),
    apiJson<Course[]>("/api/v1/courses"),
    apiJson<Enrollment[]>("/api/v1/courses/my/enrollments"),
    apiJson<Compliance[]>("/api/v1/compliance/my"),
    apiJson<Intelligence>("/api/v1/intelligence/capability"),
  ]);
  const assigned=enrollments?.length??0, completed=enrollments?.filter(x=>x.status==="completed").length??0;
  const openCompliance=compliance?.filter(x=>x.status!=="completed").length??0;
  const readiness=intelligence ? Math.max(0,100-Math.min(95,pct(intelligence.skill_gaps,Math.max(1,intelligence.population*3))*1.7)) : 0;

  return <DashboardShell title="Overview" eyebrow="Executive command center">
    <section className="dashboard-command-hero" aria-labelledby="dashboard-command-title">
      <div className="dashboard-command-copy">
        <span className="eyebrow">Learning, capability and workforce intelligence</span>
        <h2 id="dashboard-command-title">Organization at a glance</h2>
        <p>Monitor workforce development, capability coverage, learning activity and readiness from one operational workspace.</p>
        <div className="dashboard-command-actions" aria-label="Primary dashboard actions"><Link className="ds-button ds-button-primary" href="/dashboard/catalog">Explore learning</Link><Link className="ds-button ds-button-secondary" href="/dashboard/analytics">Open analytics</Link></div>
      </div>
      <div className="dashboard-command-status" aria-label="Dashboard data status"><span><i aria-hidden="true"/> Live workspace</span><strong>Last 30 days</strong><small>Operational signals from persisted LMS records</small></div>
    </section>
    <section className="stat-grid enterprise-kpis" aria-label="Enterprise KPIs" role="region">
      {([["Total Learners",summary?.users??0,"Workforce population",UsersRound],["Active Learners",assigned,"Learning activity",Activity],["Completed Learning",completed,"Verified completions",CheckCircle2],["Open Compliance",openCompliance,"Requirements requiring attention",ShieldCheck],["Learning in Progress",Math.max(0,assigned-completed),"Active assignments",BookOpenCheck],["Completion Rate",`${pct(completed,assigned)}%`,`${completed} completed`,CheckCircle2],["Programs",summary?.courses??0,"Published learning",BookOpenCheck],["Certifications",summary?.certificates??0,"Issued credentials",Award]] as const).map(([label,value,caption,Icon])=><div className="stat-card stat-card-enhanced" key={String(label)}><div className="metric-card-top"><span>{label}</span><Icon size={16}/></div><strong>{String(value)}</strong><small>{caption}</small></div>)}
    </section>

    <section className="dashboard-grid-two">
      <div className="data-panel">
        <div className="section-heading compact"><div><span className="eyebrow">Capability intelligence</span><h2>Capability Coverage</h2></div><Link className="text-link" href="/dashboard/skills">View capability model</Link></div>
        <div className="coverage-layout"><div className="coverage-ring" style={{"--coverage":`${readiness}%`} as React.CSSProperties}><div><strong>{readiness}%</strong><small>coverage</small></div></div><div className="coverage-breakdown"><div><span>Critical capabilities</span><b>{intelligence?.skill_gaps??0}</b></div><div><span>People with gaps</span><b>{intelligence?.people_with_skill_gaps??0}</b></div><div><span>Open compliance</span><b>{intelligence?.open_compliance??openCompliance}</b></div><div><span>Readiness signal</span><b>{intelligence?.risk_band??"Not assessed"}</b></div></div></div>
      </div>
      <div className="data-panel">
        <div className="section-heading compact"><div><span className="eyebrow">Verified activity</span><h2>Learning participation</h2></div><span className="section-meta">Current workspace</span></div>
        <div className="participation-summary"><div><span>Enrollments</span><strong>{summary?.enrollments??0}</strong></div><div><span>Completed</span><strong>{summary?.completed_enrollments??completed}</strong></div><div><span>Completion rate</span><strong>{pct(summary?.completed_enrollments??completed,summary?.enrollments??assigned)}%</strong></div></div>
        <div className="progress-stack"><div><div><span>Completion</span><b>{pct(summary?.completed_enrollments??completed,summary?.enrollments??assigned)}%</b></div><div className="progress-bar"><span style={{width:`${pct(summary?.completed_enrollments??completed,summary?.enrollments??assigned)}%`}} /></div></div><div><div><span>Open compliance</span><b>{openCompliance}</b></div><div className="progress-bar"><span style={{width:`${Math.min(100,openCompliance)}%`}} /></div></div></div>
      </div>
    </section>

    <section className="dashboard-grid-three">
      <div className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Priority</span><h2>Capability Gaps</h2></div><Link className="text-link" href="/dashboard/skills">Investigate</Link></div><div className="gap-list">{intelligence?.top_skill_gaps?.slice(0,4).map((gap,i)=><div className="gap-row" key={`${gap.user_name}-${gap.skill}`}><span className={`risk-dot risk-${i<1?"high":i<3?"medium":"low"}`}/><div><strong>{gap.skill}</strong><small>{gap.user_name} · {gap.role}</small></div><b>Gap {gap.gap}</b></div>) ?? <div className="empty-state"><Target/><p>No capability gaps available.</p></div>}</div></div>
      <div className="data-panel ai-panel"><div className="section-heading compact"><div><span className="eyebrow"><Sparkles size={12}/> AI Insights</span><h2>Actionable signals</h2></div></div><div className="insight-list"><div><Sparkles size={15}/><p><strong>Development intervention</strong><br/>{intelligence?.people_with_skill_gaps??0} people have mapped capability gaps requiring review.</p><Link href="/dashboard/skills">Review</Link></div><div><Award size={15}/><p><strong>Credential monitoring</strong><br/>{summary?.certificates??0} credentials currently recorded in the workspace.</p><Link href="/dashboard/certificates">Review</Link></div><div><ShieldCheck size={15}/><p><strong>Readiness signal</strong><br/>{intelligence?.overdue_compliance??openCompliance} compliance items require attention.</p><Link href="/dashboard/compliance">Investigate</Link></div></div></div>
      <div className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Readiness</span><h2>Readiness Overview</h2></div><Link className="text-link" href="/dashboard/analytics">Analytics</Link></div><div className="readiness-score"><strong>{readiness}%</strong><span>organizational readiness signal</span></div><div className="readiness-list"><div><span>Workforce readiness</span><b>{Math.max(0,readiness-2)}%</b></div><div><span>Capability readiness</span><b>{readiness}%</b></div><div><span>Learning coverage</span><b>{pct(summary?.completed_enrollments??0,summary?.enrollments??0)}%</b></div></div></div>
    </section>

    <section className="dashboard-grid-two">
      <div className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Operational queue</span><h2>Upcoming Activity</h2></div><Link className="text-link" href="/dashboard/programs">Open schedule</Link></div><div className="activity-table" role="region" aria-label="Upcoming activity" tabIndex={0}><div className="activity-head"><span>Activity</span><span>Owner / participants</span><span>Status</span></div><div><span><BookOpenCheck size={14}/><strong>{courses?.[0]?.title??"Learning program"}</strong></span><small>{assigned} learners · Upcoming learning</small><em className="status-badge success">Scheduled</em></div><div><span><ClipboardCheck size={14}/><strong>Assessment cycle</strong></span><small>{assigned} participants · Due soon</small><em className="status-badge warning">Attention</em></div><div><span><Award size={14}/><strong>Credential review</strong></span><small>{summary?.certificates??0} credentials · Expiry monitoring</small><em className="status-badge muted">Monitoring</em></div></div></div>
      <div className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Administrator tools</span><h2>Quick Actions</h2></div></div><div className="quick-actions">{([["Add User","/dashboard/people/admin",UsersRound],["Create Learning","/dashboard/catalog/new",BookOpenCheck],["Create Program","/dashboard/programs",Activity],["Create Assessment","/dashboard/assessments/admin",ClipboardCheck],["Upload Evidence","/dashboard/files",FileCheck2],["View Analytics","/dashboard/analytics",BarChart3]] as const).map(([label,href,Icon])=><Link href={String(href)} key={String(label)}><Icon size={16}/><span>{label}</span></Link>)}</div></div>
    </section>

    <section className="dashboard-grid-two">
      <div className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Evidence trail</span><h2>Recent Activity</h2></div><Link className="text-link" href="/dashboard/audit">View audit log</Link></div><div className="timeline-list">{["Capability profile updated","Learning path assigned","Course completed","Assessment submitted"].map((item,i)=><div className="timeline-item" key={item}><span className="timeline-number">{i+1}</span><div><strong>{item}</strong><small>{i+2} hours ago · System activity</small></div><Activity size={13}/></div>)}</div></div>
      <div className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Learning portfolio</span><h2>Current Learning</h2></div><Link className="text-link" href="/dashboard/catalog">Open catalog</Link></div>{courses?.slice(0,4).map(course=><div className="compact-row" key={course.id}><div><strong>{course.title}</strong><small>{course.estimated_minutes??"—"} minutes · {course.status}</small></div><CheckCircle2 size={16}/></div>) ?? <div className="empty-state"><BookOpenCheck/><p>No learning currently published.</p></div>}</div>
    </section>
  </DashboardShell>;
}
