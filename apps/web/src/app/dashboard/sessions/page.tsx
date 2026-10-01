import { DashboardShell } from "@/components/dashboard-shell";
import { ResourceForm } from "@/components/resource-form";
import { EmptyState, Section, StatusBadge } from "@/components/ui";
import { apiJson, requireUser } from "@/lib/server-api";

type LiveSession={id:string;course_id:string;instructor_id?:string|null;title:string;starts_at:string;ends_at:string;location?:string|null;status:string};
type Course={id:string;title:string};

export default async function SessionsPage(){
  const user=await requireUser<{permissions?:string[]}>();
  const [sessions,courses]=await Promise.all([
    apiJson<LiveSession[]>("/api/v1/sessions"),
    apiJson<Course[]>("/api/v1/courses?manage=true"),
  ]);
  const canManage=user.permissions?.includes("courses.manage")??false;
  return <DashboardShell title="Live sessions" eyebrow="Instructor-led learning">
    {canManage?<Section eyebrow="Schedule" title="Create live session"><ResourceForm title="Schedule instructor-led learning" endpoint="/api/lms/sessions" fields={[
      {name:"course_id",label:"Course",type:"select",required:true,options:(courses||[]).map(x=>({value:x.id,label:x.title}))},
      {name:"title",label:"Session title",required:true},
      {name:"starts_at",label:"Starts at (ISO date/time)",required:true,placeholder:"2026-10-01T09:00:00+05:00"},
      {name:"ends_at",label:"Ends at (ISO date/time)",required:true,placeholder:"2026-10-01T10:30:00+05:00"},
      {name:"location",label:"Location / meeting URL",placeholder:"Boardroom or https://..."},
    ]}/></Section>:null}
    <Section eyebrow="Schedule" title="Tenant sessions">{sessions === null ? <div role="alert" className="empty-state"><h3>Sessions unavailable</h3><p>Schedule data could not be loaded. Try again later.</p></div> : sessions.length?<div className="table-wrap"><table className="data-table">
      <thead><tr><th scope="col">Session</th><th scope="col">Starts</th><th scope="col">Ends</th><th scope="col">Location</th><th scope="col">Status</th></tr></thead>
      <tbody>{sessions.map(x=><tr key={x.id}><td><strong>{x.title}</strong></td><td>{new Date(x.starts_at).toLocaleString()}</td><td>{new Date(x.ends_at).toLocaleString()}</td><td>{x.location||"—"}</td><td><StatusBadge status={x.status}/></td></tr>)}</tbody>
    </table></div>:<EmptyState title="No live sessions" description="Schedule instructor-led learning to populate the session calendar."/>}</Section>
  </DashboardShell>;
}
