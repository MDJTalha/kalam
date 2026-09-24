import { UsersRound } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJson, requireUser } from "@/lib/server-api";

type Person = { id: string; email: string; first_name: string; last_name: string; employee_number?: string | null; job_title?: string | null; is_active: boolean };

export default async function PeoplePage() {
  await requireUser();
  const people = await apiJson<Person[]>("/api/v1/people");
  return (
    <DashboardShell title="People & teams" eyebrow="Workforce administration">
      <div className="data-panel">
        <div className="section-heading compact"><div><span className="eyebrow">Tenant workforce</span><h2>People</h2></div><span className="section-meta">{people?.length ?? 0} records</span></div>
        {people?.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Person</th><th>Employee #</th><th>Role / title</th><th>Status</th></tr></thead><tbody>{people.map((person)=><tr key={person.id}><td><strong>{person.first_name} {person.last_name}</strong><small>{person.email}</small></td><td>{person.employee_number || "—"}</td><td>{person.job_title || "—"}</td><td><span className={`status-badge ${person.is_active ? "success" : "muted"}`}>{person.is_active ? "Active" : "Inactive"}</span></td></tr>)}</tbody></table></div> : <div className="empty-state"><UsersRound size={24}/><p>No people records are available.</p></div>}
      </div>
    </DashboardShell>
  );
}
