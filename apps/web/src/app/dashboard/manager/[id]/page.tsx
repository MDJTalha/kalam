import Link from "next/link";
import { ArrowLeft, BookOpenCheck, Target, UserRound } from "lucide-react";
import { notFound } from "next/navigation";
import { DashboardShell } from "@/components/dashboard-shell";
import { ManagerDevelopmentWorkflow } from "@/components/manager-development-workflow";
import { ManagerCourseAssignment } from "@/components/manager-course-assignment";
import { apiJson, apiJsonResult, requireUser } from "@/lib/server-api";
import { SectionCard, StateMessage, StatusBadge } from "@/components/ui";

type Plan={id:string;title:string;status:string;goals:{title:string;target_date?:string|null;status:string;notes?:string|null}[]};
type Person={id:string;email:string;first_name:string;last_name:string;job_title?:string|null};
type Course={id:string;title:string;status:string};
type CoursePage={items:Course[];total:number};

export default async function ManagerPerson({params}:{params:Promise<{id:string}>}){
  await requireUser();
  const {id}=await params;
  const [people,plans,coursesResult]=await Promise.all([apiJson<Person[]>("/api/v1/people/team"),apiJson<Plan[]>("/api/v1/development/users/"+id),apiJsonResult<CoursePage>("/api/v1/courses/page?page=1&page_size=100&status=published")]);
  const person=people?.find(x=>x.id===id);
  if(!person)notFound();
  if(plans === null || !coursesResult.ok || !coursesResult.data) return <DashboardShell title={person.first_name+" "+person.last_name} eyebrow="Manager development view"><StateMessage tone="danger" title="Team member data unavailable">{!coursesResult.ok?`Course lookup HTTP ${coursesResult.status}: ${coursesResult.error||"request failed"}`:"Development plan data could not be loaded."}</StateMessage></DashboardShell>;
  if(coursesResult.data.total>coursesResult.data.items.length)return <DashboardShell title={person.first_name+" "+person.last_name} eyebrow="Manager development view"><StateMessage tone="danger" title="Published course catalog exceeds assignment limit">More than 100 published courses are available. Searchable course assignment is required before offering a complete selection.</StateMessage></DashboardShell>;
  const courses=coursesResult.data.items;
  const goalCount=(plans??[]).reduce((sum,plan)=>sum+plan.goals.length,0);
  const activePlans=(plans??[]).filter(plan=>plan.status!=="completed").length;
  return <DashboardShell title={person.first_name+" "+person.last_name} eyebrow="Manager development view" breadcrumbs={[{label:"Team",href:"/dashboard/team"},{label:person.first_name+" "+person.last_name}]}>
    <section className="manager-profile-hero" aria-labelledby="manager-profile-title">
      <div className="manager-profile-identity">
        <div className="manager-profile-avatar"><UserRound size={22}/></div>
        <div><span className="eyebrow">Direct report</span><h2 id="manager-profile-title">{person.first_name+" "+person.last_name}</h2><p>{person.job_title||"Employee"} · {person.email}</p></div>
      </div>
      <div className="manager-profile-meta"><span>{activePlans} active plans</span><span>{goalCount} goals</span></div>
    </section>

    <section className="stat-grid manager-detail-stats" aria-label="Learner development indicators">
      <div className="stat-card"><span>Development plans</span><strong>{plans?.length??0}</strong><small>Visible in manager scope</small></div>
      <div className="stat-card"><span>Goals</span><strong>{goalCount}</strong><small>Across visible plans</small></div>
      <div className="stat-card"><span>Active plans</span><strong>{activePlans}</strong><small>Not marked completed</small></div>
      <div className="stat-card"><span>Manager action</span><strong>Next</strong><small>Assign, coach or review</small></div>
    </section>

    <SectionCard eyebrow="Learner profile" title="Profile context" actions={<Link href="/dashboard/team" className="button button-secondary"><ArrowLeft size={14}/> Back to team</Link>}>
      <div className="detail-grid manager-profile-grid"><span><b>Email</b>{person.email}</span><span><b>Job title</b>{person.job_title||"—"}</span><span><b>Plans</b>{plans?.length??0}</span><span><b>Goals</b>{goalCount}</span></div>
    </SectionCard>

    <SectionCard eyebrow="Manager action" title="Assign a course">
      <div className="manager-action-intro"><BookOpenCheck size={17}/><p>Assign learning with an explicit due date. The learner keeps the assignment in the same learning workflow used by the catalog.</p></div>
      <ManagerCourseAssignment learnerId={person.id} courses={courses??[]} />
    </SectionCard>

    <SectionCard eyebrow="Development" title="Development plans" meta={(plans?.length??0)+" plans"}>{plans?.length?<div className="compact-list manager-plan-list">{plans.map(plan=><div className="compact-row" key={plan.id}><div><strong>{plan.title}</strong><small>{plan.goals.length} goals · {plan.goals.filter(goal=>goal.status==="completed").length} completed</small></div><StatusBadge status={plan.status}/></div>)}</div>:<div className="empty-state"><Target size={25}/><h3>No development plans</h3><p>No plan is currently visible within your manager scope.</p></div>}</SectionCard>
    <ManagerDevelopmentWorkflow plans={plans??[]} />
  </DashboardShell>;
}
