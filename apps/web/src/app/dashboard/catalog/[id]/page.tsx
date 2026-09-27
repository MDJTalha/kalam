import Link from "next/link";
import { notFound } from "next/navigation";
import { DashboardShell } from "@/components/dashboard-shell";
import { CoursePlayer } from "@/components/course-player";
import { apiJson, requireUser } from "@/lib/server-api";

type CourseDetail = {
  id: string;
  title: string;
  description?: string | null;
  estimated_minutes?: number | null;
  modules: Array<{
    id: string;
    title: string;
    description?: string | null;
    lessons: Array<{ id: string; title: string; content_type: string; content: Record<string, unknown>; position: number }>;
  }>;
  enrollment?: { id: string; status: string } | null;
};

export default async function CoursePage({ params }: { params: Promise<{ id: string }> }) {
  const user = await requireUser<{ permissions?: string[] }>();
  const canManage = user.permissions?.includes("courses.manage") ?? false;
  const { id } = await params;
  const course = await apiJson<CourseDetail>(`/api/v1/courses/${id}`);
  if (!course) notFound();
  return (
    <DashboardShell title={course.title} eyebrow="Course workspace">
      <div className="data-panel">
        <div className="course-header">
          <div><span className="tag">{course.enrollment?.status ?? "NOT ENROLLED"}</span><h2>{course.title}</h2><p>{course.description || "Course content and learning objectives."}</p></div>
          <div className="hero-status-card light"><strong>Duration</strong><span>{course.estimated_minutes ?? "—"} minutes</span><small>{course.modules.length} learning modules</small>{canManage && <Link className="text-link" href={`/dashboard/catalog/${course.id}/studio`}>Open course studio →</Link>}</div>
        </div>
      </div>
      <CoursePlayer course={course} />
    </DashboardShell>
  );
}
