import Link from "next/link";
import { Settings2, ShieldCheck } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJson, requireUser } from "@/lib/server-api";

type User = { id: string; tenant_id: string; email: string; first_name: string; last_name: string; employee_number?: string | null; job_title?: string | null };

export default async function SettingsPage() {
  const user = await requireUser<User>();
  const health = await apiJson<{ status: string; service?: string }>("/api/v1/health");
  return (
    <DashboardShell title="Settings" eyebrow="Account & platform configuration">
      <div className="settings-grid">
        <Link className="data-panel" href="/dashboard/settings/sessions"><div className="section-heading compact"><div><span className="eyebrow">Security</span><h2>Session security</h2><p>Review and revoke active sign-in sessions.</p></div><ShieldCheck size={20}/></div></Link>
        <div className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Profile</span><h2>Your identity</h2></div><Settings2 size={20}/></div><div className="detail-grid"><span><b>Name</b>{user.first_name} {user.last_name}</span><span><b>Email</b>{user.email}</span><span><b>Employee number</b>{user.employee_number || "—"}</span><span><b>Job title</b>{user.job_title || "—"}</span><span><b>Tenant</b>{user.tenant_id}</span></div></div>
        <div className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Platform health</span><h2>Service status</h2></div></div><div className="detail-grid"><span><b>API</b>{health?.status || "Unavailable"}</span><span><b>Environment</b>Local development</span><span><b>Security</b>Tenant-scoped sessions</span><span><b>Data</b>PostgreSQL system of record</span></div></div>
      </div>
    </DashboardShell>
  );
}
