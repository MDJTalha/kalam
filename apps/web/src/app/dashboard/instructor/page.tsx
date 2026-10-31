import Link from "next/link";
import { Activity, CalendarDays, ClipboardCheck, UsersRound } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { DataTable, EmptyState, MetricCard, SectionCard, StatusBadge } from "@/components/ui";
import { apiJson, requireUser } from "@/lib/server-api";

type LiveSession = {
  id:string;course_id:string;instructor_id?:string|null;title:string;
  starts_at:string;ends_at:string;status:string;location?:string|null;
};
type SessionAnalytics = {
  session:{id:string;title:string;starts_at:string;ends_at:string};
  attendance:{total_marked:number;present:number;late:number;absent:number;excused:number;attendance_rate:number};
};

export default async function InstructorWorkspacePage() {
  const user=await requireUser<{permissions?:string[]}>();
  if(!user.permissions?.includes("learning.access")) {
    return <DashboardShell title="Instructor workspace" eyebrow="Learning delivery"><EmptyState title="Instructor access is restricted" description="This workspace requires assigned learning access."/></DashboardShell>;
  }
  const sessions=await apiJson<LiveSession[]>("/api/v1/sessions");
  if(!sessions)return <DashboardShell title="Instructor workspace" eyebrow="Learning delivery"><EmptyState title="Session data unavailable" description="Your assigned session schedule could not be loaded."/></DashboardShell>;
  // Session filtering is request-time logic in this Server Component.
  // eslint-disable-next-line react-hooks/purity
  const now=Date.now();
  const ordered=[...sessions].sort((a,b)=>new Date(a.starts_at).getTime()-new Date(b.starts_at).getTime());
  const upcoming=ordered.filter(session=>new Date(session.ends_at).getTime()>=now).slice(0,6);
  const completed=ordered.filter(session=>new Date(session.ends_at).getTime()<now);
  const recent=completed.slice(-4);
  const analytics=await Promise.all(recent.map(session=>apiJson<SessionAnalytics>("/api/v1/sessions/"+session.id+"/analytics")));
  const attendanceTotal=analytics.reduce((sum,item)=>sum+(item?.attendance.total_marked??0),0);
  const attendancePresent=analytics.reduce((sum,item)=>sum+(item?.attendance.present??0)+(item?.attendance.late??0),0);
  const attendance=attendanceTotal?Math.round(attendancePresent/attendanceTotal*100):null;
  return <DashboardShell title="Instructor workspace" eyebrow="Learning delivery" breadcrumbs={[{label:"Overview",href:"/dashboard"},{label:"Instructor workspace"}]}>
    <div className="page-heading">
      <div><span className="eyebrow">My assigned sessions</span><h2>Prepare, deliver and follow up.</h2><p>Your schedule is limited to sessions assigned to your instructor account.</p></div>
      <div className="page-heading-actions"><Link className="button button-secondary" href="/dashboard/sessions">Open session calendar</Link><Link className="button button-primary" href="/dashboard/assessments">Assessments</Link></div>
    </div>
    <div className="stat-grid">
      <MetricCard label="Upcoming sessions" value={upcoming.length} detail="Your next scheduled deliveries" icon={CalendarDays}/>
      <MetricCard label="Sessions delivered" value={completed.length} detail="Past sessions assigned to you" icon={Activity}/>
      <MetricCard label="Attendance" value={attendance===null?"—":attendance+"%"} detail="Present and late among marked records" icon={UsersRound}/>
      <MetricCard label="Assessment access" value={user.permissions?.includes("assessments.grade_assigned")?"Assigned grading":user.permissions?.includes("assessments.manage")?"Administration":"View only"} detail="Review submissions for your assigned sessions" icon={ClipboardCheck}/>
    </div>
    <SectionCard eyebrow="Delivery schedule" title="Upcoming sessions" meta={upcoming.length+" sessions"}>
      <DataTable columns={["Session","Start","End","Location","Status","Actions"]} empty={<EmptyState title="No upcoming sessions" description="No future sessions are currently assigned to your instructor account."/>} rows={upcoming.map(session=>[
        <strong key="a">{session.title}</strong>,
        <span key="b">{new Date(session.starts_at).toLocaleString()}</span>,
        <span key="c">{new Date(session.ends_at).toLocaleString()}</span>,
        <span key="d">{session.location||"Not specified"}</span>,
        <StatusBadge key="e" status={session.status}/>,
        <Link key="f" className="text-link" href={"/dashboard/sessions/"+session.id}>Open register</Link>
      ])}/>
    </SectionCard>
    <div className="two-column">
      <SectionCard eyebrow="Recent delivery" title="Attendance and follow-up">
        {analytics.length? <div className="compact-list">{analytics.map(item=>item&&<div className="compact-row" key={item.session.id}><div><strong>{item.session.title}</strong><small>{new Date(item.session.starts_at).toLocaleDateString()} · {item.attendance.present+item.attendance.late} present/late of {item.attendance.total_marked} marked</small></div><StatusBadge status={item.attendance.attendance_rate>=80?"on_track":"needs_review"}/></div>)}</div>:<EmptyState title="No recent attendance analytics" description="Attendance appears here after a session has ended and records have been marked."/>}
      </SectionCard>
      <SectionCard eyebrow="Instructor tools" title="Your delivery responsibilities">
        <div className="role-actions"><Link href="/dashboard/sessions">Schedule and session records</Link><Link href="/dashboard/assessments">Assessments and grading</Link><Link href="/dashboard/catalog">Learning material</Link><Link href="/dashboard/notifications">Learner notifications</Link></div>
        <p className="form-help">You can access assigned sessions and assessments; organization-wide learner profiles and unrelated class rosters remain restricted.</p>
      </SectionCard>
    </div>
  </DashboardShell>;
}
