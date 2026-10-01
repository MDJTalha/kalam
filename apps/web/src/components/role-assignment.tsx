"use client";
import { useEffect, useState } from "react";

type Person = { id: string; first_name: string; last_name: string };
type Role = { id: string; name: string };
type Props = { people: Person[]; roles: Role[]; accessPermissions: string[]; initialSelectedId?: string };

export function RoleAssignment({ people, roles, accessPermissions, initialSelectedId }: Props) {
  const canManage = accessPermissions.includes("users.manage");
  const [userId, setUserId] = useState(people.find(p => p.id === initialSelectedId)?.id ?? people[0]?.id ?? "");
  const [roleId, setRoleId] = useState(roles[0]?.id ?? "");
  const [assigned, setAssigned] = useState<Role[]>([]);
  const [loading, setLoading] = useState(!!people.length);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!userId) return;
    const controller = new AbortController();
    fetch(`/api/lms/organization/users/${userId}/roles`, { signal: controller.signal })
      .then(async response => {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Could not load assigned roles.");
        setAssigned(data);
      })
      .catch(err => { if (err.name !== "AbortError") setError(err.message || "Could not load assigned roles."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [userId]);

  function selectUser(id: string) {
    setUserId(id); setAssigned([]); setLoading(true); setMessage(""); setError("");
  }
  async function changeRole(method: "POST" | "DELETE", id: string) {
    if (busy || !userId || !id) return;
    if (method === "DELETE" && !window.confirm("Remove this role from the selected user?")) return;
    setBusy(true); setError(""); setMessage("");
    try {
      const response = await fetch(`/api/lms/organization/users/${userId}/roles/${id}`, { method });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Role change failed.");
      const role = roles.find(item => item.id === id);
      setAssigned(current => method === "DELETE" ? current.filter(item => item.id !== id) :
        role && !current.some(item => item.id === id) ? [...current, role].sort((a, b) => a.name.localeCompare(b.name)) : current);
      setMessage(method === "DELETE" ? "Role removed." : data.status === "already_assigned" ? "Role already assigned." : "Role assigned.");
    } catch (err) { setError(err instanceof Error ? err.message : "Role change failed."); }
    finally { setBusy(false); }
  }
  return <div className="soft-panel">
    <div className="form-grid">
      <label className="form-field"><span>Employee</span><select value={userId} onChange={e => selectUser(e.target.value)}>{people.map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>)}</select></label>
      <label className="form-field"><span>Role to assign</span><select value={roleId} onChange={e => setRoleId(e.target.value)} disabled={!canManage || busy}>{roles.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}</select></label>
    </div>
    <div className="form-actions">{canManage ? <button className="button button-primary" onClick={() => void changeRole("POST", roleId)} disabled={busy || loading || !userId || !roleId || assigned.some(role => role.id === roleId)}>Assign role</button> : <span className="form-help">Role changes require users.manage permission.</span>}</div>
    <strong>Current roles</strong>
    {loading ? <p role="status">Loading roles…</p> : error ? <p>Role assignments could not be loaded.</p> : assigned.length ? <div className="compact-list">{assigned.map(role => <div className="compact-row" key={role.id}><span>{role.name}</span>{canManage && <button type="button" className="button button-secondary" disabled={busy} onClick={() => void changeRole("DELETE", role.id)}>Remove</button>}</div>)}</div> : <p>No roles assigned.</p>}
    {error && <div className="form-error" role="alert">{error}</div>}
    {message && <div className="form-success" role="status">{message}</div>}
  </div>;
}
