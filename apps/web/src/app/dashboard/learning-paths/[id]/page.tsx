import Link from "next/link";
import { notFound } from "next/navigation";
import { GitBranch } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { LearningPathEditor } from "@/components/learning-path-editor";
import { apiJsonResult, requireUser } from "@/lib/server-api";
import { StateMessage } from "@/components/ui";

type Item = { course_id: string; title: string; position: number; prerequisite_item_id?: string | null };
type Path = { id: string; title: string; slug: string; description?: string | null; status: string; items: Item[] };
type Course = { id: string; title: string; status: string };
type CoursePage = { items: Course[]; total: number };
type Enrollment = { course_id: string; status: string };

export default async function LearningPathDetail({ params }: { params: Promise<{ id: string }> }) {
  const user = await requireUser<{ permissions?: string[] }>();
  const canManage = user.permissions?.includes("courses.manage") ?? false;
  const { id } = await params;
  const [pathResult, enrollmentResult, courses] = await Promise.all([
    apiJsonResult<Path>(`/api/v1/programs/paths/${encodeURIComponent(id)}`),
    apiJsonResult<Enrollment[]>("/api/v1/courses/my/enrollments"),
    canManage ? apiJsonResult<CoursePage>("/api/v1/courses/page?page=1&page_size=100&manage=true") : Promise.resolve(null),
  ]);

  if (pathResult.status === 404) notFound();
  if (!pathResult.ok || !pathResult.data) {
    return <DashboardShell title="Learning path" eyebrow="Learning & development">
      <StateMessage tone="danger" title={pathResult.status === 403 ? "Learning path access restricted" : pathResult.status === 0 || pathResult.status >= 500 ? "Learning path service unavailable" : "Learning path could not be loaded"}>
        {pathResult.error || `The learning path request failed with HTTP ${pathResult.status}.`} Try again later or contact your administrator if the issue persists.
      </StateMessage>
    </DashboardShell>;
  }

  const path = pathResult.data;
  if (!enrollmentResult.ok || !enrollmentResult.data) {
    return <DashboardShell title={path.title} eyebrow="Learning path" breadcrumbs={[{ label: "Learning paths", href: "/dashboard/learning-paths" }, { label: path.title }]}>
      <section className="data-panel">
        <h2>Your learning progress is unavailable</h2>
        <p>{enrollmentResult.status === 403 ? "Your account cannot view enrollment progress." : enrollmentResult.status === 0 || enrollmentResult.status >= 500 ? "The enrollment service could not be reached. Your progress has not been assumed to be empty." : enrollmentResult.error || `Enrollment request failed with HTTP ${enrollmentResult.status}.`}</p>
        <Link className="text-link" href="/dashboard/learning-paths">← All learning paths</Link>
      </section>
    </DashboardShell>;
  }

  const status = new Map(enrollmentResult.data.map(item => [item.course_id, item.status]));
  const completed = path.items.filter(item => status.get(item.course_id) === "completed").length;
  const names = new Map(path.items.map(item => [item.course_id, item.title]));

  return <DashboardShell title={path.title} eyebrow="Learning path" breadcrumbs={[{ label: "Learning paths", href: "/dashboard/learning-paths" }, { label: path.title }]}>
    <section className="data-panel">
      <div className="section-heading compact"><div><span className="eyebrow">{path.status}</span><h2>{path.title}</h2></div><Link className="text-link" href="/dashboard/learning-paths">← All paths</Link></div>
      <p>{path.description || "Complete these courses in order to build the skills covered by this path."}</p>
      <div className="metric-strip"><span><b>{path.items.length}</b> courses</span><span><b>{completed}</b> completed</span></div>
    </section>
    <section className="data-panel">
      <div className="section-heading compact"><div><span className="eyebrow">Sequence</span><h2>Your learning journey</h2></div></div>
      {path.items.length ? <div className="curriculum-list">{path.items.map(item => {
        const prerequisite = item.prerequisite_item_id ? names.get(item.prerequisite_item_id) : null;
        const state = status.get(item.course_id);
        return <div className="curriculum-module" key={item.course_id}>
          <div className="curriculum-heading"><span>{String(item.position).padStart(2, "0")}</span><div><strong>{item.title}</strong><small>{prerequisite ? `Path prerequisite: “${prerequisite}” first` : "Start here"}</small></div></div>
          <div className="compact-row"><span className="status-badge">{state?.replaceAll("_", " ") ?? "Not started"}</span>
            <Link className="text-link" href={`/dashboard/catalog/${encodeURIComponent(item.course_id)}`}>{state === "completed" ? "Review course" : state ? "Continue course" : "View course"} →</Link></div>
        </div>;
      })}</div> : <div className="empty-state"><GitBranch size={24} /><h3>No courses yet</h3><p>{canManage ? "Add the first course below." : "Your learning team is preparing this path."}</p></div>}
    </section>
    {canManage && courses?.ok && courses.data && courses.data.total === courses.data.items.length && <LearningPathEditor initialPath={path} courses={courses.data.items} />}
    {canManage && courses && !courses.ok && <StateMessage tone="danger" title="Learning path course catalog unavailable">HTTP {courses.status}: {courses.error || "Courses could not be loaded."}</StateMessage>}
    {canManage && courses?.ok && courses.data && courses.data.total > courses.data.items.length && <StateMessage tone="danger" title="Course catalog exceeds the learning-path editor limit">More than 100 courses are available. Searchable course selection is required before this editor can safely offer the full catalog.</StateMessage>}
  </DashboardShell>;
}
