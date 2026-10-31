"use client";

import { useState } from "react";
import { Save, ShieldCheck, UserRoundX } from "lucide-react";

type CustomerRole = { id: string; name: string; role_kind: string };
type CustomerUser = {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  job_title?: string | null;
  is_active: boolean;
  locked: boolean;
  last_login_at?: string | null;
  roles: CustomerRole[];
};

async function send(path: string, method: string, body?: Record<string, unknown>) {
  const response = await fetch(path, {
    method,
    headers: body ? { "content-type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : `Request failed (${response.status})`);
  return payload;
}

export function ManagedTenantUsersPanel({
  tenantId,
  initialUsers,
  roles,
  canManage,
  canManageRoles,
}: {
  tenantId: string;
  initialUsers: CustomerUser[];
  roles: CustomerRole[];
  canManage: boolean;
  canManageRoles: boolean;
}) {
  const [users, setUsers] = useState(initialUsers);
  const [edits, setEdits] = useState<Record<string, { first_name: string; last_name: string; job_title: string }>>({});
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  function edit(user: CustomerUser) {
    return edits[user.id] ?? {
      first_name: user.first_name,
      last_name: user.last_name,
      job_title: user.job_title ?? "",
    };
  }

  function updateEdit(id: string, field: "first_name" | "last_name" | "job_title", value: string) {
    setEdits(current => ({
      ...current,
      [id]: { ...edit(users.find(user => user.id === id)!), [field]: value },
    }));
  }

  async function saveProfile(user: CustomerUser) {
    if (!canManage || busy) return;
    const values = edit(user);
    if (!values.first_name.trim() || !values.last_name.trim()) {
      setError("First and last name are required.");
      return;
    }
    setBusy(user.id);
    setError("");
    setMessage("");
    try {
      await send(`/api/lms/saas/crm/tenants/${tenantId}/users/${user.id}`, "PATCH", {
        first_name: values.first_name.trim(),
        last_name: values.last_name.trim(),
        job_title: values.job_title.trim() || null,
      });
      setUsers(current => current.map(item => item.id === user.id ? {
        ...item, first_name: values.first_name.trim(), last_name: values.last_name.trim(), job_title: values.job_title.trim() || null,
      } : item));
      setEdits(current => { const next = { ...current }; delete next[user.id]; return next; });
      setMessage("Customer user profile updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Customer user could not be updated.");
    } finally {
      setBusy("");
    }
  }

  async function toggleActive(user: CustomerUser) {
    if (!canManage || busy) return;
    const action = user.is_active ? "deactivate and revoke active sessions for" : "reactivate";
    if (!window.confirm(`Are you sure you want to ${action} ${user.email}?`)) return;
    setBusy(user.id);
    setError("");
    setMessage("");
    try {
      await send(`/api/lms/saas/crm/tenants/${tenantId}/users/${user.id}`, "PATCH", { is_active: !user.is_active });
      setUsers(current => current.map(item => item.id === user.id ? { ...item, is_active: !user.is_active, locked: false } : item));
      setMessage(user.is_active ? "Customer account deactivated and sessions revoked." : "Customer account reactivated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Customer account status could not be changed.");
    } finally {
      setBusy("");
    }
  }

  async function unlock(user: CustomerUser) {
    if (!canManage || busy) return;
    setBusy(user.id);
    setError("");
    setMessage("");
    try {
      await send(`/api/lms/saas/crm/tenants/${tenantId}/users/${user.id}`, "PATCH", { unlock_now: true });
      setUsers(current => current.map(item => item.id === user.id ? { ...item, locked: false } : item));
      setMessage("Customer account unlocked.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Customer account could not be unlocked.");
    } finally {
      setBusy("");
    }
  }

  async function changeRole(user: CustomerUser, role: CustomerRole, add: boolean) {
    if (!canManageRoles || busy) return;
    setBusy(user.id + role.id);
    setError("");
    setMessage("");
    try {
      const method = add ? "POST" : "DELETE";
      await send(`/api/lms/saas/crm/tenants/${tenantId}/users/${user.id}/roles/${role.id}`, method);
      setUsers(current => current.map(item => {
        if (item.id !== user.id) return item;
        const currentRoles = item.roles ?? [];
        const nextRoles = add
          ? [...currentRoles.filter(existing => existing.id !== role.id), role]
          : currentRoles.filter(existing => existing.id !== role.id);
        return { ...item, roles: nextRoles };
      }));
      setMessage(add ? `${role.name} assigned.` : `${role.name} removed.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Customer role assignment could not be changed.");
    } finally {
      setBusy("");
    }
  }

  return (
    <section className="soft-panel">
      <div className="section-heading compact">
        <div><span className="eyebrow">Customer access governance</span><h3>Tenant users</h3><p className="muted">Customer employee information is restricted to authorized Customer Success and SaaS Super Admin roles. Changes are logged in the SaaS audit trail.</p></div>
        <ShieldCheck size={18}/>
      </div>
      <div className="table-wrap">
        <table className="data-table">
          <thead><tr><th>Customer user</th><th>Account</th><th>Tenant role(s)</th><th>Last login</th><th>Actions</th></tr></thead>
          <tbody>
            {users.map(user => {
              const values=edit(user);
              return <tr key={user.id}>
                <td>
                  <div className="form-grid">
                    <label className="form-field"><span>First name</span><input value={values.first_name} maxLength={80} disabled={!canManage||!!busy} onChange={event=>updateEdit(user.id,"first_name",event.target.value)}/></label>
                    <label className="form-field"><span>Last name</span><input value={values.last_name} maxLength={80} disabled={!canManage||!!busy} onChange={event=>updateEdit(user.id,"last_name",event.target.value)}/></label>
                    <label className="form-field"><span>Job title</span><input value={values.job_title} maxLength={160} disabled={!canManage||!!busy} onChange={event=>updateEdit(user.id,"job_title",event.target.value)}/></label>
                  </div>
                  <small>{user.email}</small>
                </td>
                <td><span className={user.is_active?"status-badge status-active":"status-badge status-inactive"}>{user.is_active?"Active":"Inactive"}</span>{user.locked&&<small>Locked</small>}</td>
                <td>
                  <div className="compact-list">{user.roles.map(role=><div className="compact-row" key={role.id}><span>{role.name}</span>{canManageRoles&&<button className="button button-quiet" type="button" disabled={!!busy} onClick={()=>void changeRole(user,role,false)}>Remove</button>}</div>)}</div>
                  {canManageRoles&&<label className="form-field"><span>Assign role</span><select defaultValue="" disabled={!!busy} onChange={event=>{const selected=roles.find(role=>role.id===event.target.value);event.target.value="";if(selected)void changeRole(user,selected,true);}}><option value="">Choose role…</option>{roles.filter(role=>!user.roles.some(existing=>existing.id===role.id)).map(role=><option key={role.id} value={role.id}>{role.name}</option>)}</select></label>}
                  {!user.roles.length&&<span className="muted">No role assigned</span>}
                </td>
                <td>{user.last_login_at?new Date(user.last_login_at).toLocaleString():"Never"}</td>
                <td>
                  <div className="section-actions">
                    {canManage&&<button className="button button-secondary" type="button" disabled={!!busy} onClick={()=>void saveProfile(user)}><Save size={14}/>Save</button>}
                    {canManage&&user.locked&&<button className="button button-secondary" type="button" disabled={!!busy} onClick={()=>void unlock(user)}>Unlock</button>}
                    {canManage&&<button className="button button-secondary" type="button" disabled={!!busy} onClick={()=>void toggleActive(user)}><UserRoundX size={14}/>{user.is_active?"Deactivate & revoke":"Reactivate"}</button>}
                  </div>
                </td>
              </tr>;
            })}
            {!users.length&&<tr><td colSpan={5}>No customer users have been provisioned.</td></tr>}
          </tbody>
        </table>
      </div>
      {!canManage&&<p className="form-help">Customer access changes require the Customer Success management permission.</p>}
      {!canManageRoles&&<p className="form-help">Customer role assignment and permission governance are reserved for SaaS Super Admin.</p>}
      {error&&<p className="form-error" role="alert">{error}</p>}
      {message&&<p className="form-success" role="status">{message}</p>}
    </section>
  );
}
