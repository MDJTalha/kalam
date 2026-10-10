import { DashboardShell } from "@/components/dashboard-shell";
import { LearnerCatalogBrowser } from "@/components/learner-catalog-browser";
import { apiJsonResult, requireUser } from "@/lib/server-api";

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
  enrollment_status?: string | null;
};
type CoursePage = { items: Course[]; total: number; page: number; page_size: number };

export default async function CatalogPage() {
  await requireUser();
  const catalog = await apiJsonResult<CoursePage>("/api/v1/courses/page?page=1&page_size=24&scope=all");
  if (!catalog.ok || !catalog.data) {
    return <DashboardShell title="Learning catalog" eyebrow="Learning operations">
      <section className="data-panel" role="alert"><h2>Catalog unavailable</h2><p>HTTP {catalog.status}: {catalog.error || "Course information could not be loaded. Please try again."}</p></section>
    </DashboardShell>;
  }

  return <DashboardShell title="Learning catalog" eyebrow="Learning operations">
    <LearnerCatalogBrowser courses={catalog.data.items} total={catalog.data.total} />
  </DashboardShell>;
}
