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
    lessons: Array<{ id: string; title: string; content_type: string; content: Record<string, unknown> }>;
  }>;
  enrollment?: { id: string; status: string } | null;
};

export default async function CoursePage({ params }: { params: Promise<{ id: string }> }) {
  await requireUser();
  const { id } = await params;
  const course = await apiJson<CourseDetail>(`/api/v1/courses/${id}`);
  if (!course) notFound();
  return (
    <DashboardShell title={course.title} eyebrow="Course workspace">
      <div className="data-panel">
        <div className="course-header">
          <div><span className="tag">{course.enrollment?.status ?? "NOT ENROLLED"}</span><h2>{course.title}</h2><p>{course.description || "Course content and learning objectives."}</p></div>
          <div className="hero-status-card light"><strong>Duration</strong><span>{course.estimated_minutes ?? "—"} minutes</span><small>{course.modules.length} learning modules</small></div>
        </div>
      </div>
      <CoursePlayer course={course} />
    </DashboardShell>
  );
}
