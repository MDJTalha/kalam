import Link from "next/link";
import { DashboardShell } from "@/components/dashboard-shell";
import { CourseEquivalencyAdmin } from "@/components/course-equivalency-admin";
import { apiJson, requireUser } from "@/lib/server-api";
type Course = { id: string; title: string };
type Equivalency = { id: string; course_id: string; course_title: string; equivalent_course_id: string; equivalent_course_title: string; equivalency_type: string; notes?: string | null; active: boolean };

export default async function EquivalenciesPage() {
  const user = await requireUser<{ permissions?: string[] }>();
  if (!user.permissions?.includes("courses.manage")) {
    return <DashboardShell title="Course equivalencies" eyebrow="L&D operations"><section className="data-panel" role="alert"><h2>Access restricted</h2><p>Course equivalency management requires course management permission.</p></section></DashboardShell>;
  }
  const [courses, relationships] = await Promise.all([
    apiJson<Course[]>("/api/v1/courses?manage=true"),
    apiJson<Equivalency[]>("/api/v1/courses/equivalencies"),
  ]);
  return <DashboardShell title="Course equivalencies" eyebrow="L&D operations" breadcrumbs={[{ label: "L&D operations", href: "/dashboard/ld-operations" }, { label: "Equivalencies" }]}>
    <section className="data-panel"><Link href="/dashboard/ld-operations" className="text-link">← Back to operations</Link>
      <p>Document reviewed course relationships for planning and governance. This register does not automatically award completion or compliance credit.</p></section>
    {courses && relationships ? <CourseEquivalencyAdmin courses={courses} initial={relationships} /> : <section className="data-panel" role="alert"><h2>Equivalencies unavailable</h2><p>Check the service and try again.</p></section>}
  </DashboardShell>;
}
