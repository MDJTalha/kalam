import { DashboardShell } from "@/components/dashboard-shell";
import { requireUser } from "@/lib/server-api";

export async function RecoveredWorkspace({ title = "Workspace", eyebrow = "Kognivon Learning Intelligence", description = "This workspace is available and ready for tenant-scoped operations." }: { title?: string; eyebrow?: string; description?: string }) {
  await requireUser();
  return <DashboardShell title={title} eyebrow={eyebrow}><section className="data-panel"><div className="empty-state"><h2>{title}</h2><p>{description}</p></div></section></DashboardShell>;
}
