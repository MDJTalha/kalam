import Link from "next/link";
import { DashboardShell } from "@/components/dashboard-shell";
import { StudioCourseList } from "@/components/studio-course-list";
import { apiJson, requireUser } from "@/lib/server-api";
type Course = { id: string; title: string; description?: string | null; status: string; slug: string; estimated_minutes?: number | null; visibility?: string };
export default async function CourseStudioPage() {
  const user = await requireUser<{ permissions?: string[] }>();
  if (!user.permissions?.includes("courses.manage")) {
    return <DashboardShell title="Course studio" eyebrow="Learning administration"><section className="data-panel" role="alert"><h2>Access restricted</h2><p>Course authoring requires course management permission.</p></section></DashboardShell>;
  }
  const courses = await apiJson<Course[]>("/api/v1/courses?manage=true");
  return <DashboardShell title="Course studio" eyebrow="Learning administration">
    <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Course authoring</span><h2>Build and publish courses</h2></div><Link className="button button-primary" href="/dashboard/catalog/new">Create course</Link></div>
      <p>Manage course details, audience, enrollment rules, modules, lessons, content history, and learner assignments.</p>
    </section>
    {courses ? <StudioCourseList courses={courses} /> : <section className="data-panel" role="alert"><h2>Courses unavailable</h2><p>Try again when the service is available.</p></section>}
  </DashboardShell>;
}
