import Link from "next/link";
import { DashboardShell } from "@/components/dashboard-shell";
import { LearningPathForm } from "@/components/learning-path-form";
import { requireUser } from "@/lib/server-api";

export default async function NewLearningPathPage() {
  const user = await requireUser<{ permissions?: string[] }>();
  if (!user.permissions?.includes("courses.manage")) {
    return <DashboardShell title="Create learning path" eyebrow="Learning paths"><section className="data-panel" role="alert"><h2>Access restricted</h2><p>Creating paths requires course management permission.</p></section></DashboardShell>;
  }
  return <DashboardShell title="Create learning path" eyebrow="Learning paths" breadcrumbs={[{ label: "Learning paths", href: "/dashboard/learning-paths" }, { label: "Create path" }]}>
    <section className="data-panel"><p>Give the path a clear outcome. After creating it, add courses in order and publish it for learners.</p><Link className="text-link" href="/dashboard/learning-paths">← Back to paths</Link></section>
    <LearningPathForm />
  </DashboardShell>;
}
