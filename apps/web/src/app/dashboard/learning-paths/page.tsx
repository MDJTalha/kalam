import Link from "next/link";
import { GitBranch, Plus } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type Path = { id: string; title: string; description?: string | null; status: string; slug: string };
export default async function LearningPathsPage() {
  const user = await requireUser<{ permissions?: string[] }>();
  const canManage = user.permissions?.includes("courses.manage") ?? false;
  const result = await apiJsonResult<Path[]>("/api/v1/programs/paths/all");
  if (!result.ok || result.data === null) return <DashboardShell title="Learning paths" eyebrow="Structured learning"><section className="data-panel" role="alert"><h2>{result.status===403?"Learning paths access restricted":"Learning paths unavailable"}</h2><p>{result.status===403?"Your role does not have permission to view these learning paths.":result.status===0?"The API service could not be reached. Check that it is running and try again.":`Learning paths could not be loaded (HTTP ${result.status}). Refresh and try again.`}</p></section></DashboardShell>;
  const paths = result.data;
  return <DashboardShell title="Learning paths" eyebrow="Structured learning">
    <section className="data-panel">
      <div className="section-heading compact">
        <div><span className="eyebrow">Guided journeys</span><h2>Learning paths</h2></div>
        {canManage && <Link className="button button-primary" href="/dashboard/learning-paths/new"><Plus size={16} /> Create path</Link>}
      </div>
      <p>Follow courses in a planned order to build a capability. Path prerequisites indicate the intended course order.</p>
      {paths.length ? <div className="catalog-grid">{paths.map(path => <Link key={path.id} href={`/dashboard/learning-paths/${path.id}`} className="catalog-card">
          <div className="module-icon"><GitBranch size={20} aria-hidden="true" /></div>
          <div className="catalog-copy"><div className="catalog-top"><span className="tag">{path.status}</span></div><h3>{path.title}</h3>
            <p>{path.description || "Explore the courses and learning sequence in this path."}</p>
            <small>View learning path →</small></div>
        </Link>)}</div>
        : <div className="empty-state"><GitBranch size={24} /><h3>No learning paths yet</h3><p>{canManage ? "Create a path, add courses, then publish it for learners." : "Published paths will appear here when your learning team makes them available."}</p></div>}
    </section>
  </DashboardShell>;
}
