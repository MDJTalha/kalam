import { Layers3 } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJson, requireUser } from "@/lib/server-api";

type Skill = { id: string; skill: string; proficiency: number; evidence_source?: string | null };
type CatalogSkill = { id: string; name: string; description?: string | null; category?: string | null };

export default async function SkillsPage() {
  await requireUser();
  const [mine, catalog] = await Promise.all([
    apiJson<Skill[]>("/api/v1/skills/my"),
    apiJson<CatalogSkill[]>("/api/v1/skills"),
  ]);
  return (
    <DashboardShell title="Skills & development" eyebrow="Capability management">
      <div className="stat-grid">
        <div className="stat-card"><span>My skills</span><strong>{mine?.length ?? 0}</strong><small>Recorded evidence</small></div>
        <div className="stat-card"><span>Catalog</span><strong>{catalog?.length ?? 0}</strong><small>Tenant skill taxonomy</small></div>
        <div className="stat-card"><span>Average proficiency</span><strong>{mine?.length ? (mine.reduce((sum,x)=>sum+x.proficiency,0)/mine.length).toFixed(1) : "—"}</strong><small>1 to 5 scale</small></div>
        <div className="stat-card"><span>Evidence</span><strong>{mine?.filter(x=>x.evidence_source).length ?? 0}</strong><small>Attributed records</small></div>
      </div>
      <div className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">My capability profile</span><h2>Skills</h2></div></div>
        {mine?.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Skill</th><th>Proficiency</th><th>Evidence</th></tr></thead><tbody>{mine.map((item)=><tr key={item.id}><td><strong>{item.skill}</strong></td><td><span className="proficiency">{item.proficiency}/5</span></td><td>{item.evidence_source || "Not specified"}</td></tr>)}</tbody></table></div> : <div className="empty-state"><Layers3 size={24}/><p>No skills have been recorded for this learner yet.</p></div>}
      </div>
      <div className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Taxonomy</span><h2>Skill catalog</h2></div></div>
        {catalog?.length ? <div className="compact-list">{catalog.map((item)=><div className="compact-row" key={item.id}><div><strong>{item.name}</strong><small>{item.category || "General capability"} · {item.description || "No description"}</small></div></div>)}</div> : <div className="empty-state"><p>No skills configured.</p></div>}
      </div>
    </DashboardShell>
  );
}
