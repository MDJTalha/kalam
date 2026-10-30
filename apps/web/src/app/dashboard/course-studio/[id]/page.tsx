import Link from "next/link";
import { notFound } from "next/navigation";
import { DashboardShell } from "@/components/dashboard-shell";
import { CourseAuthoring } from "@/components/course-authoring";
import { apiJsonResult, requireUser } from "@/lib/server-api";
import { StateMessage } from "@/components/ui";

type Course = { id: string; title: string; slug: string; description?: string | null; estimated_minutes?: number | null; status: string; category_id?: string | null; owner_id?: string | null; visibility?: "tenant" | "private"; enrollment_policy?: "open" | "approval" | "assignment_only"; capacity?: number | null; audience_org_units?: string[]; tags?: string[]; prerequisites?: string[] };
export default async function CourseStudioDetail({ params }: { params: Promise<{ id: string }> }) {
  const user = await requireUser<{ permissions?: string[] }>();
  if (!user.permissions?.includes("courses.manage")) {
    return <DashboardShell title="Course studio" eyebrow="Learning administration"><section className="data-panel" role="alert"><h2>Access restricted</h2><p>Course authoring requires course management permission.</p></section></DashboardShell>;
  }
  const { id } = await params;
  const result = await apiJsonResult<Course>(`/api/v1/courses/${encodeURIComponent(id)}`);
  if (result.status === 404) notFound();
  if (!result.ok || !result.data) {
    return <DashboardShell title="Course studio" eyebrow="Learning administration" breadcrumbs={[{ label: "Course studio", href: "/dashboard/course-studio" }]}>
      <StateMessage tone="danger" title={result.status === 403 ? "Course access restricted" : result.status === 0 || result.status >= 500 ? "Course service unavailable" : "Course could not be loaded"}>
        {result.error || `The course request failed with HTTP ${result.status}.`} No course data has been assumed. Refresh or contact an administrator if this continues.
      </StateMessage>
      <Link className="text-link" href="/dashboard/course-studio">← All courses</Link>
    </DashboardShell>;
  }
  const course = result.data;
  return <DashboardShell title={course.title} eyebrow="Course authoring" breadcrumbs={[{ label: "Course studio", href: "/dashboard/course-studio" }, { label: course.title }]}>
    <div className="data-panel"><Link href="/dashboard/course-studio" className="text-link">← All courses</Link><p>Save course settings, edit the curriculum, review lesson history, and assign learners from this workspace.</p></div>
    <CourseAuthoring initial={course} mode="build" />
  </DashboardShell>;
}
