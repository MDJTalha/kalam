import { DashboardShell } from "@/components/dashboard-shell";
import { LearnerCatalogBrowser } from "@/components/learner-catalog-browser";
import { apiJson, requireUser } from "@/lib/server-api";

type Course = {
  id: string;
  title: string;
  slug: string;
  description?: string | null;
  status: string;
  estimated_minutes?: number | null;
  enrollment_policy?: string;
  visibility?: string;
  tags?: string[];
};
type Enrollment = { id: string; course_id: string; status: string };

export default async function CatalogPage() {
  await requireUser();
  const [courses, enrollments] = await Promise.all([
    apiJson<Course[]>("/api/v1/courses"),
    apiJson<Enrollment[]>("/api/v1/courses/my/enrollments"),
  ]);
  if (!courses || !enrollments) {
    return <DashboardShell title="Learning catalog" eyebrow="Learning operations">
      <section className="data-panel" role="alert"><h2>Catalog unavailable</h2><p>Course information could not be loaded. Please try again.</p></section>
    </DashboardShell>;
  }

  const enrollmentStatus = Object.fromEntries(enrollments.map(item => [item.course_id, item.status]));
  return <DashboardShell title="Learning catalog" eyebrow="Learning operations">
    <LearnerCatalogBrowser courses={courses} enrollmentStatus={enrollmentStatus} />
  </DashboardShell>;
}
