import { DashboardShell } from "@/components/dashboard-shell";
import { ResourceForm } from "@/components/resource-form";
import { EmptyState, Section, StateMessage, StatusBadge } from "@/components/ui";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type LiveSession={id:string;course_id:string;instructor_id?:string|null;title:string;starts_at:string;ends_at:string;location?:string|null;status:string};
type Course={id:string;title:string};
type CoursePage={items:Course[];total:number};
type SessionAnalytics={attendance:{total_marked:number;attendance_rate:number};roster:Array<{user_id:string;learner:string;email:string;status:string|null}>};

export default async function SessionsPage(){
  const user=await requireUser<{id:string;permissions?:string[]}>();
  const [sessionsResult,coursesResult]=await Promise.all([
    apiJsonResult<LiveSession[]>("/api/v1/sessions"),
    apiJsonResult<CoursePage>("/api/v1/courses/page?page=1&page_size=100&manage=true"),
  ]);
  const failed=[sessionsResult,...(user.permissions?.includes("courses.manage")?[coursesResult]:[])].filter(result=>!result.ok);
  if(failed.length)return <DashboardShell title="Live sessions" eyebrow="Instructor-led learning"><StateMessage tone="danger" title="Session data unavailable">{failed.map(result=>`HTTP ${result.status}: ${result.error||"request failed"}`).join(" · ")}</StateMessage></DashboardShell>;
  const sessions=sessionsResult.data!,courses=coursesResult.data?.items??[];
  const canManage=user.permissions?.includes("courses.manage")??false;
  const instructorSessions=sessions.filter(session=>session.instructor_id===user.id);
  const instructorAnalytics=await Promise.all(instructorSessions.slice(0,30).map(async session=>({
    session,
    result:await apiJsonResult<SessionAnalytics>(`/api/v1/sessions/${session.id}/analytics`),
  })));
  if(canManage&&(coursesResult.data?.total??0)>courses.length)return <DashboardShell title="Live sessions" eyebrow="Instructor-led learning"><StateMessage tone="danger" title="Course catalog exceeds the session editor limit">The catalog has more than 100 courses. Searchable course selection is required before scheduling can safely use the full catalog.</StateMessage></DashboardShell>;
  return <DashboardShell title="Live sessions" eyebrow="Instructor-led learning">
    {canManage?<Section eyebrow="Schedule" title="Create live session"><ResourceForm title="Schedule instructor-led learning" endpoint="/api/lms/sessions" fields={[
      {name:"course_id",label:"Course",type:"select",required:true,options:(courses||[]).map(x=>({value:x.id,label:x.title}))},
      {name:"title",label:"Session title",required:true},
      {name:"starts_at",label:"Starts at (ISO date/time)",required:true,placeholder:"2026-10-01T09:00:00+05:00"},
      {name:"ends_at",label:"Ends at (ISO date/time)",required:true,placeholder:"2026-10-01T10:30:00+05:00"},
      {name:"location",label:"Location / meeting URL",placeholder:"Boardroom or https://..."},
    ]}/></Section>:null}
    <Section eyebrow="Schedule" title={canManage?"Tenant session calendar":"Your learning sessions"}>{sessions.length?<div className="table-wrap" tabIndex={0} aria-label={canManage?"Tenant live sessions table":"Your live sessions table"}><table className="data-table">
      <thead><tr><th scope="col">Session</th><th scope="col">Starts</th><th scope="col">Ends</th><th scope="col">Location</th><th scope="col">Status</th></tr></thead>
      <tbody>{sessions.map(x=><tr key={x.id}><td><strong>{x.title}</strong></td><td>{new Date(x.starts_at).toLocaleString()}</td><td>{new Date(x.ends_at).toLocaleString()}</td><td>{x.location||"—"}</td><td><StatusBadge status={x.status}/></td></tr>)}</tbody>
    </table></div>:<EmptyState title="No live sessions" description="Schedule instructor-led learning to populate the session calendar."/>}</Section>
    {instructorSessions.length?<Section eyebrow="Delivery operations" title="Your instructor sessions">
      {instructorAnalytics.map(({session,result})=><div key={session.id} className="panel-stack">
        <div className="section-heading compact"><div><h3>{session.title}</h3><p>{new Date(session.starts_at).toLocaleString()}</p></div></div>
        {!result.ok || !result.data?<StateMessage tone="danger" title="Learner roster unavailable">HTTP {result.status}: {result.error||"request failed"}</StateMessage>:<>
          <p>{result.data.attendance.total_marked} attendance records · {result.data.attendance.attendance_rate}% present or late</p>
          {result.data.roster.length?<div className="table-wrap" tabIndex={0} aria-label={session.title+" learner attendance"}><table className="data-table"><thead><tr><th scope="col">Learner</th><th scope="col">Email</th><th scope="col">Current status</th><th scope="col">Update record</th></tr></thead><tbody>
            {result.data.roster.map(person=><tr key={person.user_id}><td>{person.learner||"Learner"}</td><td>{person.email}</td><td>{person.status||"Not recorded"}</td><td><ResourceForm title="Record attendance" endpoint={`/api/lms/sessions/${session.id}/attendance`} fields={[
              {name:"user_id",label:"Learner ID",required:true,defaultValue:person.user_id},
              {name:"status",label:"Attendance",type:"select",required:true,defaultValue:person.status||"present",options:[
                {value:"present",label:"Present"},{value:"late",label:"Late"},{value:"absent",label:"Absent"},{value:"excused",label:"Excused"},
              ]},
            ]} submitLabel="Save"/></td></tr>)}
          </tbody></table></div>:<EmptyState title="No enrolled learners" description="Learners enrolled in this course will appear here."/>}
        </>}
      </div>)}
    </Section>:null}
  </DashboardShell>;
}
