import Link from "next/link";
import { ArrowLeft, Layers3, UsersRound } from "lucide-react";
import { notFound } from "next/navigation";
import { DashboardShell } from "@/components/dashboard-shell";
import { ProgramEditor } from "@/components/program-editor";
import { apiJsonResult, requireUser } from "@/lib/server-api";
import { StateMessage } from "@/components/ui";

type Course = { course_id: string; title: string; position: number; is_required: boolean };
type CatalogCourse = { id: string; title: string; status: string };
type CatalogCoursePage = { items: CatalogCourse[]; total: number };
type Cohort = { id: string; program_id: string; name: string; status: string };
type Program = { id: string; title: string; slug: string; description?: string | null; status: string; is_required: boolean; courses: Course[] };

export default async function ProgramDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const user = await requireUser<{ permissions?: string[] }>();
  const canManage = user.permissions?.includes("courses.manage") ?? false;
  const { id } = await params;
  const [program, cohorts, catalog] = await Promise.all([
    apiJsonResult<Program>("/api/v1/programs/" + id).then((result) => result.ok ? result.data : null),
    apiJsonResult<Cohort[]>("/api/v1/programs/cohorts").then((result) => result.ok ? result.data : null),
    canManage ? apiJsonResult<CatalogCoursePage>("/api/v1/courses/page?page=1&page_size=100&manage=true") : Promise.resolve(null),
  ]);
  if (!program) notFound();

  return (
    <DashboardShell title={program.title} eyebrow="Program detail">
      <div className="data-panel">
        <Link href="/dashboard/programs" className="text-link"><ArrowLeft size={15}/> Back to programs</Link>
        <div className="section-heading">
          <span className="eyebrow">{program.status} · {program.slug}</span>
          <h2>{program.title}</h2>
          <p>{program.description || "No description has been published."}</p>
        </div>
        <div className="metric-strip">
          <span><b>{program.courses?.length ?? 0}</b> courses</span>
          <span><b>{program.courses?.filter((course) => course.is_required).length ?? 0}</b> required</span>
        </div>
      </div>

      <div className="data-panel">
        <div className="section-heading compact"><div><span className="eyebrow">Curriculum</span><h2>Program courses</h2></div><Layers3 size={20}/></div>
        {program.courses?.length ? (
          <div className="compact-list">
            {program.courses.map((course) => (
              <div className="compact-row" key={course.course_id}>
                <div><Link href={"/dashboard/catalog/" + course.course_id} className="text-link"><strong>{course.position}. {course.title}</strong></Link><small>{course.is_required ? "Required component" : "Elective component"}</small></div>
              </div>
            ))}
          </div>
        ) : <div className="empty-state"><p>No courses have been added to this program.</p></div>}
      </div>

      <div className="data-panel">
        <div className="section-heading compact"><div><span className="eyebrow">Delivery</span><h2>Cohort management</h2></div><UsersRound size={20}/></div>
        <p>Group learners into cohorts and launch delivery after publishing the program.</p>
        <div className="compact-list">{cohorts?.filter(item => item.program_id === id).map(item => <div className="compact-row" key={item.id}><Link className="text-link" href={"/dashboard/programs/cohorts/" + item.id}>{item.name}</Link><span className="status-badge">{item.status}</span></div>)}</div>
      </div>
      {canManage && catalog?.ok && catalog.data && catalog.data.total === catalog.data.items.length && <ProgramEditor initialProgram={program} catalog={catalog.data.items} />}
      {canManage && catalog && !catalog.ok && <StateMessage tone="danger" title="Program course catalog unavailable">HTTP {catalog.status}: {catalog.error || "Courses could not be loaded."}</StateMessage>}
      {canManage && catalog?.ok && catalog.data && catalog.data.total > catalog.data.items.length && <StateMessage tone="danger" title="Course catalog exceeds the program editor limit">More than 100 courses are available. Searchable course selection is required before this editor can safely offer the full catalog.</StateMessage>}
    </DashboardShell>
  );
}
