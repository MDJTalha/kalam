import Link from "next/link";
import { notFound } from "next/navigation";
import { DashboardShell } from "@/components/dashboard-shell";
import { CourseAuthoring } from "@/components/course-authoring";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type Course = { id: string; title: string; slug: string; description?: string | null; estimated_minutes?: number | null; status: string; category_id?: string | null; owner_id?: string | null; visibility?: "tenant" | "private"; enrollment_policy?: "open" | "approval" | "assignment_only"; capacity?: number | null; audience_org_units?: string[]; tags?: string[]; prerequisites?: string[] };
export default async function CourseStudioDetail({ params }: { params: Promise<{ id: string }> }) {
  const user = await requireUser<{ permissions?: string[] }>();
  if (!user.permissions?.includes("courses.manage")) {
    return <DashboardShell title="Course studio" eyebrow="Learning administration"><section className="data-panel" role="alert"><h2>Access restricted</h2><p>Course authoring requires course management permission.</p></section></DashboardShell>;
  }
  const { id } = await params;
  const course = await apiJsonResult<Course>(`/api/v1/courses/${id}`).then((result) => result.ok ? result.data : null);
  if (!course) notFound();
  return <DashboardShell title={course.title} eyebrow="Course authoring" breadcrumbs={[{ label: "Course studio", href: "/dashboard/course-studio" }, { label: course.title }]}>
    <div className="data-panel"><Link href="/dashboard/course-studio" className="text-link">← All courses</Link><p>Save course settings, edit the curriculum, review lesson history, and assign learners from this workspace.</p></div>
    <CourseAuthoring initial={course} mode="build" />
  </DashboardShell>;
}
