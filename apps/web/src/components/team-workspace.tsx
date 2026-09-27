"use client";
import Link from "next/link";
import { useMemo, useState } from "react";
type Member = { id: string; email: string; first_name: string; last_name: string; employee_number?: string | null; job_title?: string | null; completed_learning: number; open_learning: number; overdue_learning: number; open_compliance: number; overdue_compliance: number; active_plans: number };
const PAGE_SIZE = 20;
export function TeamWorkspace({ team }: { team: Member[] }) {
  const [query, setQuery] = useState("");
  const [scope, setScope] = useState("all");
  const [page, setPage] = useState(1);
  const overdueLearning = team.reduce((total, person) => total + person.overdue_learning, 0);
  const overdueCompliance = team.reduce((total, person) => total + person.overdue_compliance, 0);
  const activePlans = team.reduce((total, person) => total + person.active_plans, 0);
  const filtered = useMemo(() => team.filter(person => {
    const name = `${person.first_name} ${person.last_name}`.toLowerCase();
    const matches = [name, person.email.toLowerCase(), (person.job_title ?? "").toLowerCase()].some(value => value.includes(query.trim().toLowerCase()));
    const attention = person.overdue_learning + person.overdue_compliance > 0;
    return matches && (scope === "all" || (scope === "attention" ? attention : !attention));
  }).sort((a, b) => (b.overdue_learning + b.overdue_compliance) - (a.overdue_learning + a.overdue_compliance) || a.last_name.localeCompare(b.last_name)), [team, query, scope]);
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const visible = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  return <>
    <section className="stat-grid" aria-label="Direct report indicators">
      <div className="stat-card"><span>Direct reports</span><strong>{team.length}</strong><small>Active people you manage</small></div>
      <div className="stat-card"><span>Overdue learning</span><strong>{overdueLearning}</strong><small>Assignments past due</small></div>
      <div className="stat-card"><span>Overdue compliance</span><strong>{overdueCompliance}</strong><small>Requirements past due</small></div>
      <div className="stat-card"><span>Active development plans</span><strong>{activePlans}</strong><small>Across direct reports</small></div>
    </section>
    <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Manager scope</span><h2>Direct reports</h2></div><span className="section-meta">{filtered.length} shown</span></div>
      <p>People needing attention appear first. Open a learner to assign a course or review their development plans.</p>
      <div className="form-grid"><label className="form-field"><span>Search direct reports</span><input type="search" value={query} onChange={event => { setQuery(event.target.value); setPage(1); }} placeholder="Name, email or job title" /></label>
        <label className="form-field"><span>Attention</span><select value={scope} onChange={event => { setScope(event.target.value); setPage(1); }}><option value="all">All direct reports</option><option value="attention">Overdue items</option><option value="clear">No overdue items</option></select></label></div>
      {visible.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th scope="col">Person</th><th scope="col">Learning</th><th scope="col">Compliance</th><th scope="col">Development</th><th scope="col">Action</th></tr></thead><tbody>{visible.map(person =>
        <tr key={person.id}><td><strong>{person.first_name} {person.last_name}</strong><small>{person.job_title || "Title not set"} · {person.email}</small></td>
          <td>{person.open_learning} open · {person.completed_learning} completed{person.overdue_learning > 0 && <small className="form-error">{person.overdue_learning} overdue</small>}</td>
          <td>{person.open_compliance} open{person.overdue_compliance > 0 && <small className="form-error">{person.overdue_compliance} overdue</small>}</td>
          <td>{person.active_plans} active plans</td>
          <td><Link className="text-link" href={`/dashboard/manager/${person.id}`}>Review learner</Link></td>
        </tr>)}</tbody></table></div> : <div className="empty-state"><p>{team.length ? "No direct reports match these filters." : "No direct reports are assigned to you. An administrator can set a person's manager in User Administration."}</p></div>}
      {pages > 1 && <nav className="form-actions" aria-label="Team pages"><button className="button button-secondary" type="button" disabled={page === 1} onClick={() => setPage(current => current - 1)}>Previous</button><span>Page {page} of {pages}</span><button className="button button-secondary" type="button" disabled={page === pages} onClick={() => setPage(current => current + 1)}>Next</button></nav>}
    </section>
  </>;
}
