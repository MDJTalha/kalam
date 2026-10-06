"use client";
import Link from "next/link";
import { FormEvent, useMemo, useRef, useState } from "react";

type Unit = { id: string; name: string; unit_type: string; code?: string | null; parent_id?: string | null; member_count: number };
const LABELS: Record<string, string> = { business_unit: "Business unit", department: "Department", location: "Location", team: "Team" };
export function OrganizationWorkspace({ initialUnits, activePeople, assignedPeople, unassignedPeople, canManage }: { initialUnits: Unit[]; activePeople: number; assignedPeople: number; unassignedPeople: number; canManage: boolean }) {
  const editorRef = useRef<HTMLElement>(null);
  const nameRef = useRef<HTMLInputElement>(null);
  const parentRef = useRef<HTMLSelectElement>(null);
  const [units, setUnits] = useState(initialUnits);
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [name, setName] = useState("");
  const [type, setType] = useState("department");
  const [code, setCode] = useState("");
  const [parentId, setParentId] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const counts = new Map(units.map(unit => [unit.id, unit.member_count]));
  const ordered = useMemo(() => {
    const children = new Map<string, Unit[]>();
    for (const unit of units) {
      const parent = unit.parent_id && units.some(item => item.id === unit.parent_id) ? unit.parent_id : "";
      children.set(parent, [...(children.get(parent) ?? []), unit]);
    }
    const rows: Array<{ unit: Unit; depth: number }> = [];
    const seen = new Set<string>();
    function walk(parent: string, depth: number) {
      for (const unit of (children.get(parent) ?? []).sort((a, b) => a.name.localeCompare(b.name))) {
        if (seen.has(unit.id)) continue;
        seen.add(unit.id); rows.push({ unit, depth }); walk(unit.id, depth + 1);
      }
    }
    walk("", 0);
    for (const unit of units) if (!seen.has(unit.id)) rows.push({ unit, depth: 0 });
    return rows;
  }, [units]);
  const filtered = ordered.filter(({ unit }) => {
    const term = query.trim().toLowerCase();
    return !term || [unit.name, unit.unit_type, unit.code ?? ""].some(value => value.toLowerCase().includes(term));
  });
  function reset() { setSelectedId(""); setName(""); setType("department"); setCode(""); setParentId(""); setMessage(""); setError(""); }
  function edit(unit: Unit, reparent = false) {
    setSelectedId(unit.id); setName(unit.name); setType(unit.unit_type); setCode(unit.code ?? ""); setParentId(unit.parent_id ?? "");
    setMessage(""); setError("");
    editorRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    window.setTimeout(() => (reparent ? parentRef.current : nameRef.current)?.focus(), 150);
  }
  function validParent(unit: Unit) {
    if (!selectedId) return true;
    let cursor: Unit | undefined = unit;
    const seen = new Set<string>();
    while (cursor && !seen.has(cursor.id)) {
      if (cursor.id === selectedId) return false;
      seen.add(cursor.id); cursor = units.find(item => item.id === cursor?.parent_id);
    }
    return true;
  }
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      const endpoint = selectedId ? `/api/lms/organization/units/${selectedId}` : "/api/lms/organization/units";
      const response = await fetch(endpoint, { method: selectedId ? "PATCH" : "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: name.trim(), unit_type: type, code: code.trim() || null, parent_id: parentId || null }) });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Unable to save the unit.");
      setUnits(current => selectedId ? current.map(item => item.id === data.id ? { ...data, member_count: item.member_count } : item) : [...current, { ...data, member_count: 0 }]);
      const action = selectedId ? "updated" : "created";
      reset(); setMessage(`Organization unit ${action}.`);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to save the unit."); }
    finally { setBusy(false); }
  }
  async function remove(unitId: string) {
    if (!unitId || busy || !window.confirm("Delete this empty organization unit? This action cannot be undone.")) return;
    setBusy(true); setError(""); setMessage("");
    try {
      const response = await fetch(`/api/lms/organization/units/${unitId}`, { method: "DELETE" });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Unable to delete the unit.");
      setUnits(current => current.filter(item => item.id !== unitId));
      reset(); setMessage("Organization unit deleted.");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to delete the unit."); editorRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }); }
    finally { setBusy(false); }
  }
  return <>
    <section className="stat-grid" aria-label="Organization overview">
      <div className="stat-card"><span>Organization units</span><strong>{units.length}</strong><small>Across the tenant</small></div>
      <div className="stat-card"><span>People placed</span><strong>{assignedPeople}</strong><small>Of {activePeople} active people</small></div>
      <div className="stat-card"><span>Unassigned people</span><strong>{unassignedPeople}</strong><small>Need an organization unit</small></div>
      <div className="stat-card"><span>Teams</span><strong>{units.filter(unit => unit.unit_type === "team").length}</strong><small>Defined team units</small></div>
    </section>
    <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Structure</span><h2>Organization hierarchy</h2></div><span className="section-meta">{filtered.length} of {units.length} units</span></div>
      <label className="form-field"><span>Find a unit</span><input type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Name, type or code" /></label>
      {filtered.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th scope="col">Unit</th><th scope="col">Type</th><th scope="col">Parent</th><th scope="col">Active people</th><th scope="col">Code</th>{canManage && <th scope="col">Action</th>}</tr></thead><tbody>
        {filtered.map(({ unit, depth }) => <tr key={unit.id}><td><strong style={{ paddingLeft: Math.min(depth, 6) * 16 }}>{unit.name}</strong></td><td>{LABELS[unit.unit_type] ?? unit.unit_type}</td><td>{units.find(parent => parent.id === unit.parent_id)?.name ?? "Top level"}</td><td>{counts.get(unit.id) ?? 0}</td><td>{unit.code || "—"}</td>{canManage && <td><div className="form-actions"><button type="button" className="text-link" onClick={() => edit(unit)}>Edit</button><button type="button" className="text-link" onClick={() => edit(unit, true)}>Reparent</button><button type="button" className="text-link" disabled={busy || units.some(child => child.parent_id === unit.id) || (counts.get(unit.id) ?? 0) > 0} title="Only empty units without child units can be deleted" onClick={() => void remove(unit.id)}>Delete</button></div></td>}</tr>)}
      </tbody></table></div> : <div className="empty-state"><p>{units.length ? "No units match this search." : "No organization units have been set up yet."}</p></div>}
      <p className="form-help">{canManage ? <>Place people in a unit through <Link href="/dashboard/people/admin">User Administration</Link>.</> : "Organization placement is managed by an administrator."} Counts show direct active members.</p>
    </section>
    {canManage && <section className="data-panel" ref={editorRef}><div className="section-heading compact"><div><span className="eyebrow">Organization administration</span><h2>{selectedId ? "Edit organization unit" : "Add organization unit"}</h2></div>{selectedId && <button type="button" className="button button-secondary" onClick={reset}>Cancel edit</button>}</div>
      <form className="studio-form" onSubmit={save}><div className="form-grid">
        <label>Name<input ref={nameRef} value={name} onChange={event => setName(event.target.value)} required minLength={2} maxLength={160} /></label>
        <label>Type<select value={type} onChange={event => setType(event.target.value)}><option value="business_unit">Business unit</option><option value="department">Department</option><option value="location">Location</option><option value="team">Team</option></select></label>
        <label>Parent unit (reparent)<select ref={parentRef} value={parentId} onChange={event => setParentId(event.target.value)}><option value="">Top level</option>{units.filter(validParent).map(unit => <option key={unit.id} value={unit.id}>{unit.name} · {LABELS[unit.unit_type] ?? unit.unit_type}</option>)}</select></label>
        <label>Code (optional)<input value={code} onChange={event => setCode(event.target.value)} maxLength={80} placeholder="e.g. HR-LHR" /></label>
      </div><button className="button button-primary" type="submit" disabled={busy || name.trim().length < 2}>{busy ? "Saving…" : selectedId ? "Save changes" : "Create unit"}</button></form>
      {selectedId && <div className="form-actions"><button className="button button-secondary" type="button" disabled={busy || units.some(unit => unit.parent_id === selectedId) || (counts.get(selectedId) ?? 0) > 0} onClick={() => void remove(selectedId)}>Delete empty unit</button><span className="form-help">Move child units and all people before deletion.</span></div>}
      {message && <p className="form-success" role="status">{message}</p>}{error && <p className="form-error" role="alert">{error}</p>}
    </section>}
    {!canManage && <div className="callout">Organization changes require the users.manage permission.</div>}
  </>;
}
