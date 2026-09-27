import { DashboardShell } from "@/components/dashboard-shell";
import { EmptyState, Section } from "@/components/ui";
import { apiJson, requireUser } from "@/lib/server-api";

type Audit={id:string;action:string;entity_type:string;entity_id?:string|null;actor_id?:string|null;request_id?:string|null;summary?:string|null;created_at:string};

export default async function AuditPage(){
  await requireUser();
  const rows=await apiJson<Audit[]>("/api/v1/admin/audit?limit=200");
  return <DashboardShell title="Audit trail" eyebrow="Governance & evidence">
    <Section eyebrow="Tenant evidence" title="Recent audited activity">
      {rows?.length?<div className="table-wrap"><table className="data-table">
        <thead><tr><th>Time</th><th>Action</th><th>Entity</th><th>Summary</th><th>Request</th></tr></thead>
        <tbody>{rows.map(x=><tr key={x.id}><td>{new Date(x.created_at).toLocaleString()}</td><td><strong>{x.action}</strong></td><td>{x.entity_type}{x.entity_id?" · "+x.entity_id:""}</td><td>{x.summary||"—"}</td><td><code>{x.request_id||"—"}</code></td></tr>)}</tbody>
      </table></div>:<EmptyState title="No audit evidence" description="Audited tenant actions will appear here."/>}
    </Section>
  </DashboardShell>;
}
