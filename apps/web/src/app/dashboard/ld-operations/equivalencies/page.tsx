import Link from "next/link";
import { DashboardShell } from "@/components/dashboard-shell";
import { CourseEquivalencyAdmin } from "@/components/course-equivalency-admin";
import { StateMessage } from "@/components/ui";
import { apiJsonResult, requireUser } from "@/lib/server-api";
type Course = { id: string; title: string };
type CoursePage = { items: Course[]; total: number };
type Equivalency = { id: string; course_id: string; course_title: string; equivalent_course_id: string; equivalent_course_title: string; equivalency_type: string; notes?: string | null; active: boolean };

export default async function EquivalenciesPage() {
  const user = await requireUser<{ permissions?: string[] }>();
  if (!user.permissions?.includes("courses.manage")) {
    return <DashboardShell title="Course equivalencies" eyebrow="L&D operations"><section className="data-panel" role="alert"><h2>Access restricted</h2><p>Course equivalency management requires course management permission.</p></section></DashboardShell>;
  }
  const [courseResult, relationshipResult] = await Promise.all([
    apiJsonResult<CoursePage>("/api/v1/courses/page?page=1&page_size=100&manage=true"),
    apiJsonResult<Equivalency[]>("/api/v1/courses/equivalencies"),
  ]);
  const failed=[courseResult,relationshipResult].filter(result=>!result.ok);
  if(failed.length)return <DashboardShell title="Course equivalencies" eyebrow="L&D operations"><StateMessage tone="danger" title="Equivalency data unavailable">{failed.map(result=>`HTTP ${result.status}: ${result.error||"request failed"}`).join(" · ")}</StateMessage></DashboardShell>;
  const coursePage=courseResult.data!,relationships=relationshipResult.data!;
  if(coursePage.total>coursePage.items.length)return <DashboardShell title="Course equivalencies" eyebrow="L&D operations"><StateMessage tone="danger" title="Course catalog exceeds the equivalency editor limit">The catalog has more than 100 courses. Searchable course selection is required before this editor can safely offer the full set of relationships.</StateMessage></DashboardShell>;
  return <DashboardShell title="Course equivalencies" eyebrow="L&D operations" breadcrumbs={[{ label: "L&D operations", href: "/dashboard/ld-operations" }, { label: "Equivalencies" }]}>
    <section className="data-panel"><Link href="/dashboard/ld-operations" className="text-link">← Back to operations</Link>
      <p>Document reviewed course relationships for planning and governance. This register does not automatically award completion or compliance credit.</p></section>
    <CourseEquivalencyAdmin courses={coursePage.items} initial={relationships} />
  </DashboardShell>;
}
