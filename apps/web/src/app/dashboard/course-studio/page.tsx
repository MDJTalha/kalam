import Link from "next/link";
import { DashboardShell } from "@/components/dashboard-shell";
import { StudioCourseList } from "@/components/studio-course-list";
import { StateMessage } from "@/components/ui";
import { apiJsonResult, requireUser } from "@/lib/server-api";
type Course = { id: string; title: string; description?: string | null; status: string; slug: string; estimated_minutes?: number | null; visibility?: string };
type CoursePage = { items: Course[]; total: number };
export default async function CourseStudioPage() {
  const user = await requireUser<{ permissions?: string[] }>();
  if (!user.permissions?.includes("courses.manage")) {
    return <DashboardShell title="Course studio" eyebrow="Learning administration"><section className="data-panel" role="alert"><h2>Access restricted</h2><p>Course authoring requires course management permission.</p></section></DashboardShell>;
  }
  const result = await apiJsonResult<CoursePage>("/api/v1/courses/page?page=1&page_size=25&manage=true");
  if (!result.ok || !result.data) return <DashboardShell title="Course studio" eyebrow="Learning administration"><StateMessage tone="danger" title="Course catalog unavailable">HTTP {result.status}: {result.error || "Course records could not be loaded."}</StateMessage></DashboardShell>;
  return <DashboardShell title="Course studio" eyebrow="Learning administration">
    <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Course authoring</span><h2>Build and publish courses</h2></div><Link className="button button-primary" href="/dashboard/catalog/new">Create course</Link></div>
      <p>Manage course details, audience, enrollment rules, modules, lessons, content history, and learner assignments.</p>
    </section>
    <StudioCourseList courses={result.data.items} total={result.data.total} />
  </DashboardShell>;
}
