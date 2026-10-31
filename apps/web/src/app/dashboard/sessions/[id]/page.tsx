import Link from "next/link";
import { ArrowLeft, CalendarDays, ClipboardCheck, MapPin, UsersRound } from "lucide-react";
import { notFound } from "next/navigation";
import { DashboardShell } from "@/components/dashboard-shell";
import { SessionAttendanceRoster } from "@/components/session-attendance-roster";
import { apiJsonResult, requireUser } from "@/lib/server-api";
import { EmptyState, MetricCard, SectionCard, StateMessage, StatusBadge } from "@/components/ui";

type Session = {
  id:string;course_id:string;instructor_id?:string|null;title:string;
  starts_at:string;ends_at:string;status:string;location?:string|null;
};
type RosterRow = {
  user_id:string;learner:string;email:string;enrollment_status:string;
  attendance_status:"present"|"absent"|"late"|"excused"|null;
};
type Analytics = {
  session:{id:string;title:string;starts_at:string;ends_at:string;status:string};
  attendance:{total_marked:number;present:number;late:number;absent:number;excused:number;attendance_rate:number};
};

export default async function InstructorSessionPage({params}:{params:Promise<{id:string}>}) {
  const user=await requireUser<{permissions?:string[]}>();
  const permissions=user.permissions??[];
  if(!permissions.includes("assessments.grade_assigned")&&!permissions.includes("courses.manage")) {
    return <DashboardShell title="Session details" eyebrow="Instructor delivery"><EmptyState title="Session access is restricted" description="Only the assigned instructor or a learning administrator can open this session register."/></DashboardShell>;
  }
  const {id}=await params;
  const [sessionResult,rosterResult,analyticsResult]=await Promise.all([
    apiJsonResult<Session[]>("/api/v1/sessions"),
    apiJsonResult<RosterRow[]>(`/api/v1/sessions/${id}/roster`),
    apiJsonResult<Analytics>(`/api/v1/sessions/${id}/analytics`),
  ]);
  if(!sessionResult.ok||!rosterResult.ok||!analyticsResult.ok) {
    const status=rosterResult.status||analyticsResult.status||sessionResult.status;
    if(status===404)notFound();
    return <DashboardShell title="Session details" eyebrow="Instructor delivery"><StateMessage tone="danger" title="Session data is unavailable">{rosterResult.error||analyticsResult.error||sessionResult.error||"The session could not be loaded."}</StateMessage></DashboardShell>;
  }
  const session=sessionResult.data?.find(item=>item.id===id);
  if(!session)notFound();
  const analytics=analyticsResult.data!;
  const roster=rosterResult.data??[];
  return <DashboardShell title={session.title} eyebrow="Assigned instructor session" breadcrumbs={[{label:"Instructor workspace",href:"/dashboard/instructor"},{label:"Live sessions",href:"/dashboard/sessions"},{label:session.title}]}>
    <div className="page-heading">
      <div><span className="eyebrow">Session details</span><h2>{session.title}</h2><p>Attendance and learner records for this course session. Only enrolled learners are included.</p></div>
      <div className="page-heading-actions"><Link className="button button-secondary" href="/dashboard/sessions"><ArrowLeft size={14}/> Back to sessions</Link></div>
    </div>
    <div className="stat-grid">
      <MetricCard label="Scheduled start" value={new Date(session.starts_at).toLocaleString()} detail="Session start time" icon={CalendarDays}/>
      <MetricCard label="Enrolled learners" value={roster.length} detail="Active or completed course enrollments" icon={UsersRound}/>
      <MetricCard label="Attendance marked" value={analytics.attendance.total_marked} detail={analytics.attendance.present+" present · "+analytics.attendance.late+" late"} icon={ClipboardCheck}/>
      <MetricCard label="Attendance rate" value={analytics.attendance.total_marked?analytics.attendance.attendance_rate+"%":"—"} detail="Present and late among marked records" icon={ClipboardCheck}/>
    </div>
    <SectionCard eyebrow="Delivery information" title="Session record">
      <div className="detail-grid">
        <span><b>Starts</b>{new Date(session.starts_at).toLocaleString()}</span>
        <span><b>Ends</b>{new Date(session.ends_at).toLocaleString()}</span>
        <span><b>Location / meeting</b>{session.location||"Not specified"}</span>
        <span><b>Status</b><StatusBadge status={session.status}/></span>
      </div>
    </SectionCard>
    <SessionAttendanceRoster sessionId={session.id} initialRows={roster}/>
  </DashboardShell>;
}
