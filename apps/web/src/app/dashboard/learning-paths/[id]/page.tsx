import Link from "next/link";
import { notFound } from "next/navigation";
import { GitBranch } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { LearningPathEditor } from "@/components/learning-path-editor";
import { apiJson, requireUser } from "@/lib/server-api";

type Item = { course_id: string; title: string; position: number; prerequisite_item_id?: string | null };
type Path = { id: string; title: string; slug: string; description?: string | null; status: string; items: Item[] };
type Course = { id: string; title: string; status: string };
type Enrollment = { course_id: string; status: string };

export default async function LearningPathDetail({ params }: { params: Promise<{ id: string }> }) {
  const user = await requireUser<{ permissions?: string[] }>();
  const canManage = user.permissions?.includes("courses.manage") ?? false;
  const { id } = await params;
  const [path, enrollments, courses] = await Promise.all([
    apiJson<Path>(`/api/v1/programs/paths/${id}`),
    apiJson<Enrollment[]>("/api/v1/courses/my/enrollments"),
    canManage ? apiJson<Course[]>("/api/v1/courses?manage=true") : Promise.resolve(null),
  ]);
  if (!path) notFound();
  const status = new Map((enrollments ?? []).map(item => [item.course_id, item.status]));
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
            <Link className="text-link" href={`/dashboard/catalog/${item.course_id}`}>{state === "completed" ? "Review course" : state ? "Continue course" : "View course"} →</Link></div>
        </div>;
      })}</div> : <div className="empty-state"><GitBranch size={24} /><h3>No courses yet</h3><p>{canManage ? "Add the first course below." : "Your learning team is preparing this path."}</p></div>}
    </section>
    {canManage && <LearningPathEditor initialPath={path} courses={courses ?? []} />}
  </DashboardShell>;
}
