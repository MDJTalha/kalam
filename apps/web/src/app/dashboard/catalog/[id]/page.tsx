import Link from "next/link";
import { notFound } from "next/navigation";
import { DashboardShell } from "@/components/dashboard-shell";
import { CoursePlayer } from "@/components/course-player";
import { apiFetch, requireUser } from "@/lib/server-api";

type CourseDetail = {
  id: string;
  title: string;
  description?: string | null;
  estimated_minutes?: number | null;
  enrollment_policy?: string;
  visibility?: string;
  completed_lesson_ids?: string[];
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
  if (!/^[0-9a-fA-F-]{36}$/.test(id)) notFound();
  const response = await apiFetch(`/api/v1/courses/${id}`);
  if (response.status === 404) notFound();
  if (!response.ok) return <DashboardShell title="Course unavailable" eyebrow="Learning catalog"><section className="data-panel" role="alert"><h2>{response.status === 403 ? "Course access restricted" : "Course could not be loaded"}</h2><p>{response.status === 403 ? "Your role cannot open this course." : "Please try again later."}</p><Link className="text-link" href="/dashboard/catalog">Return to catalog</Link></section></DashboardShell>;
  const course = await response.json() as CourseDetail;
  return (
    <DashboardShell title={course.title} eyebrow="Course workspace">
      <div className="data-panel">
        <div className="course-header">
          <div><span className="tag">COURSE OVERVIEW</span><h2>{course.title}</h2><p>{course.description || "Course content and learning objectives."}</p></div>
          <div className="hero-status-card light"><strong>Duration</strong><span>{course.estimated_minutes ?? "—"} minutes</span><small>{course.modules.length} learning modules</small>{canManage && <Link className="text-link" href={`/dashboard/catalog/${course.id}/studio`}>Open course studio →</Link>}</div>
        </div>
      </div>
      <CoursePlayer course={course} canManage={canManage} />
    </DashboardShell>
  );
}
