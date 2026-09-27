import Link from "next/link";
import { GitBranch, Plus } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJson, requireUser } from "@/lib/server-api";

type Path = { id: string; title: string; description?: string | null; status: string; slug: string };
export default async function LearningPathsPage() {
  const user = await requireUser<{ permissions?: string[] }>();
  const canManage = user.permissions?.includes("courses.manage") ?? false;
  const paths = await apiJson<Path[]>("/api/v1/programs/paths/all");
  return <DashboardShell title="Learning paths" eyebrow="Structured learning">
    <section className="data-panel">
      <div className="section-heading compact">
        <div><span className="eyebrow">Guided journeys</span><h2>Learning paths</h2></div>
        {canManage && <Link className="button button-primary" href="/dashboard/learning-paths/new"><Plus size={16} /> Create path</Link>}
      </div>
      <p>Follow courses in a planned order to build a capability. Path prerequisites indicate the intended course order.</p>
      {paths === null ? <div className="empty-state" role="alert"><h3>Paths unavailable</h3><p>Try again when the service is available.</p></div>
        : paths.length ? <div className="catalog-grid">{paths.map(path => <Link key={path.id} href={`/dashboard/learning-paths/${path.id}`} className="catalog-card">
          <div className="module-icon"><GitBranch size={20} aria-hidden="true" /></div>
          <div className="catalog-copy"><div className="catalog-top"><span className="tag">{path.status}</span></div><h3>{path.title}</h3>
            <p>{path.description || "Explore the courses and learning sequence in this path."}</p>
            <small>View learning path →</small></div>
        </Link>)}</div>
        : <div className="empty-state"><GitBranch size={24} /><h3>No learning paths yet</h3><p>{canManage ? "Create a path, add courses, then publish it for learners." : "Published paths will appear here when your learning team makes them available."}</p></div>}
    </section>
  </DashboardShell>;
}
