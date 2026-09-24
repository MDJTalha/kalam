import Link from "next/link";
import { BookOpenCheck, Clock3 } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJson, requireUser } from "@/lib/server-api";

type Course = {
  id: string;
  title: string;
  slug: string;
  description?: string | null;
  status: string;
  estimated_minutes?: number | null;
};

type Enrollment = {
  id: string;
  course_id: string;
  status: string;
};

export default async function CatalogPage() {
  await requireUser();
  const [courses, enrollments] = await Promise.all([
    apiJson<Course[]>("/api/v1/courses"),
    apiJson<Enrollment[]>("/api/v1/courses/my/enrollments"),
  ]);
  const enrolled = new Map((enrollments ?? []).map((item) => [item.course_id, item.status]));

  return (
    <DashboardShell title="Learning catalog" eyebrow="Learning operations">
      <div className="data-panel">
        <div className="section-heading compact">
          <div><span className="eyebrow">Published learning</span><h2>Courses</h2></div>
          <span className="section-meta">{courses?.length ?? 0} available</span>
        </div>
        {courses?.length ? (
          <div className="catalog-grid">
            {courses.map((course) => (
              <Link className="catalog-card" href={`/dashboard/catalog/${course.id}`} key={course.id}>
                <div className="module-icon"><BookOpenCheck size={19} /></div>
                <div className="catalog-copy">
                  <div className="catalog-top"><span className="tag">{enrolled.get(course.id) ?? "AVAILABLE"}</span><span>{course.status}</span></div>
                  <h3>{course.title}</h3>
                  <p>{course.description || "No course description has been published yet."}</p>
                  <small><Clock3 size={13} /> {course.estimated_minutes ?? "—"} minutes</small>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="empty-state"><BookOpenCheck size={24} /><p>No published courses are available to this tenant.</p></div>
        )}
      </div>
    </DashboardShell>
  );
}
