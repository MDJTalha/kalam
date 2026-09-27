"use client";
import Link from "next/link";
import { useMemo, useState } from "react";
import { UsersRound } from "lucide-react";
type Unit = { id: string; name: string };
type Person = { id: string; email: string; first_name: string; last_name: string; employee_number?: string | null; job_title?: string | null; org_unit_id?: string | null; is_active: boolean };
const PAGE_SIZE = 20;
export function PeopleDirectory({ people, units, canManage }: { people: Person[]; units: Unit[]; canManage: boolean }) {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [unit, setUnit] = useState("all");
  const [page, setPage] = useState(1);
  const unitNames = new Map(units.map(item => [item.id, item.name]));
  const filtered = useMemo(() => people.filter(person => {
    const name = `${person.first_name} ${person.last_name}`.toLowerCase();
    const term = search.trim().toLowerCase();
    return (!term || [name, person.email, person.employee_number ?? "", person.job_title ?? ""].some(value => value.toLowerCase().includes(term)))
      && (status === "all" || person.is_active === (status === "active"))
      && (unit === "all" || (unit === "unassigned" ? !person.org_unit_id : person.org_unit_id === unit));
  }), [people, search, status, unit]);
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const visible = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  return <section className="data-panel">
    <div className="section-heading compact"><div><span className="eyebrow">Tenant workforce</span><h2>People directory</h2></div>{canManage && <Link className="button button-primary" href="/dashboard/people/admin">Manage people</Link>}</div>
    <div className="form-grid">
      <label className="form-field"><span>Search people</span><input type="search" value={search} onChange={event => { setSearch(event.target.value); setPage(1); }} placeholder="Name, email, employee number or title" /></label>
      <label className="form-field"><span>Status</span><select value={status} onChange={event => { setStatus(event.target.value); setPage(1); }}><option value="all">All statuses</option><option value="active">Active</option><option value="inactive">Inactive</option></select></label>
      <label className="form-field"><span>Organization unit</span><select value={unit} onChange={event => { setUnit(event.target.value); setPage(1); }}><option value="all">All units</option><option value="unassigned">Unassigned</option>{units.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
    </div>
    <p className="section-meta" role="status">{filtered.length} of {people.length} people</p>
    {visible.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th scope="col">Person</th><th scope="col">Employee #</th><th scope="col">Job title</th><th scope="col">Organization unit</th><th scope="col">Status</th></tr></thead><tbody>{visible.map(person =>
      <tr key={person.id}><td><Link className="text-link" href={`/dashboard/people/${person.id}`}>{person.first_name} {person.last_name}</Link><small>{person.email}</small></td><td>{person.employee_number || "—"}</td><td>{person.job_title || "—"}</td><td>{unitNames.get(person.org_unit_id ?? "") || "Unassigned"}</td><td><span className={`status-badge ${person.is_active ? "success" : "muted"}`}>{person.is_active ? "Active" : "Inactive"}</span></td></tr>
    )}</tbody></table></div> : <div className="empty-state"><UsersRound size={24}/><p>{people.length ? "No people match these filters." : "No people have been added yet."}</p></div>}
    {pages > 1 && <nav className="form-actions" aria-label="People pages"><button type="button" className="button button-secondary" disabled={page === 1} onClick={() => setPage(current => current - 1)}>Previous</button><span>Page {page} of {pages}</span><button type="button" className="button button-secondary" disabled={page === pages} onClick={() => setPage(current => current + 1)}>Next</button></nav>}
  </section>;
}
