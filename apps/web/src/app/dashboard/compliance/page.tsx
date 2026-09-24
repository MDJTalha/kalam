import { ShieldCheck } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJson, requireUser } from "@/lib/server-api";

type Assignment = { id: string; requirement: string; status: string; due_at?: string | null };
type Requirement = { id: string; name: string; description?: string | null; recurrence_days?: number | null; due_days?: number | null; active: boolean };

export default async function CompliancePage() {
  await requireUser();
  const [mine, requirements] = await Promise.all([
    apiJson<Assignment[]>("/api/v1/compliance/my"),
    apiJson<Requirement[]>("/api/v1/compliance"),
  ]);
  return (
    <DashboardShell title="Compliance learning" eyebrow="Mandatory training & evidence">
      <div className="stat-grid">
        <div className="stat-card"><span>My assignments</span><strong>{mine?.length ?? 0}</strong><small>Current learner scope</small></div>
        <div className="stat-card"><span>Open items</span><strong>{mine?.filter((x)=>x.status!=="completed").length ?? 0}</strong><small>Completion required</small></div>
        <div className="stat-card"><span>Requirements</span><strong>{requirements?.length ?? 0}</strong><small>Tenant rules</small></div>
        <div className="stat-card"><span>Active rules</span><strong>{requirements?.filter((x)=>x.active).length ?? 0}</strong><small>Currently enabled</small></div>
      </div>
      <div className="data-panel">
        <div className="section-heading compact"><div><span className="eyebrow">Learner view</span><h2>My compliance</h2></div></div>
        {mine?.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Requirement</th><th>Status</th><th>Due</th></tr></thead><tbody>{mine.map((item)=><tr key={item.id}><td><strong>{item.requirement}</strong></td><td><span className={`status-badge ${item.status==="completed" ? "success" : "warning"}`}>{item.status}</span></td><td>{item.due_at ? new Date(item.due_at).toLocaleDateString() : "—"}</td></tr>)}</tbody></table></div> : <div className="empty-state"><ShieldCheck size={24}/><p>No compliance assignments are currently visible.</p></div>}
      </div>
      <div className="data-panel">
        <div className="section-heading compact"><div><span className="eyebrow">Tenant policy</span><h2>Compliance requirements</h2></div></div>
        {requirements?.length ? <div className="compact-list">{requirements.map((item)=><div className="compact-row" key={item.id}><div><strong>{item.name}</strong><small>{item.description || "Configured organizational requirement"} · {item.active ? "Active" : "Inactive"}</small></div><ShieldCheck size={17}/></div>)}</div> : <div className="empty-state"><p>No requirements configured.</p></div>}
      </div>
    </DashboardShell>
  );
}
