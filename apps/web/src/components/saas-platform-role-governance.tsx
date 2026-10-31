"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { Save, ShieldCheck, Trash2 } from "lucide-react";

type SaaSPermission = { id: string; key: string; description?: string | null };
type CustomRole = { id: string; name: string; description?: string | null; role_kind: string; permission_keys: string[] };

async function requestJson(path: string, method = "GET", body?: Record<string, unknown>) {
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

export function SaaSPlatformRoleGovernance({ enabled }: { enabled: boolean }) {
  const [roles, setRoles] = useState<CustomRole[]>([]);
  const [permissions, setPermissions] = useState<SaaSPermission[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [keys, setKeys] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const selected = roles.find(role => role.id === selectedId);

  const load = useCallback(async () => {
    if (!enabled) return;
    setLoading(true);
    setError("");
    try {
      const [roleRows, permissionRows] = await Promise.all([
        requestJson("/api/lms/saas/crm/team/roles") as Promise<CustomRole[]>,
        requestJson("/api/lms/saas/crm/team/role-permissions") as Promise<SaaSPermission[]>,
      ]);
      setRoles(roleRows);
      setPermissions(permissionRows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Custom platform roles could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => { void load(); }, [load]);

  function selectRole(role: CustomRole) {
    setSelectedId(role.id);
    setName(role.name);
    setDescription(role.description ?? "");
    setKeys(role.permission_keys ?? []);
    setMessage("");
    setError("");
  }

  function clear() {
    setSelectedId("");
    setName("");
    setDescription("");
    setKeys([]);
    setMessage("");
    setError("");
  }

  function toggle(key: string, checked: boolean) {
    setKeys(current => checked ? [...new Set([...current, key])] : current.filter(item => item !== key));
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || !name.trim()) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      if (!selectedId) {
        await requestJson("/api/lms/saas/crm/team/roles", "POST", {
          name: name.trim(), description: description.trim() || null, permission_keys: keys,
        });
        setMessage("Custom SaaS role created. Reloading the team role selector…");
        window.location.reload();
      } else {
        await requestJson(`/api/lms/saas/crm/team/roles/${selectedId}`, "PATCH", {
          name: name.trim(), description: description.trim() || null,
        });
        await requestJson(`/api/lms/saas/crm/team/roles/${selectedId}/permissions`, "PUT", {
          permission_keys: keys,
        });
        setMessage("Custom SaaS role updated.");
        await load();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Custom SaaS role could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!selected || busy) return;
    if (!window.confirm(`Delete the custom SaaS role "${selected.name}"? It must be unassigned from every user first.`)) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await requestJson(`/api/lms/saas/crm/team/roles/${selected.id}`, "DELETE");
      clear();
      await load();
      setMessage("Custom SaaS role deleted.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Role could not be deleted.");
    } finally {
      setBusy(false);
    }
  }

  if (!enabled) return null;

  return (
    <section className="soft-panel saas-platform-role-governance">
      <div className="section-heading compact">
        <div><span className="eyebrow">Super Admin governance</span><h3>Custom SaaS team roles</h3><p className="muted">Define internal job roles with a constrained set of SaaS permissions. Root Super Admin and Platform Developer privileges cannot be delegated through custom roles.</p></div>
        <ShieldCheck size={18}/>
      </div>
      {loading ? <p className="muted">Loading custom platform roles…</p> : (
        <div className="two-column">
          <div>
            <h4>Custom role register</h4>
            {roles.length ? <div className="compact-list">{roles.map(role=><button key={role.id} type="button" className={selectedId===role.id?"button button-secondary":"button button-quiet"} onClick={()=>selectRole(role)}>{role.name} · {role.permission_keys.length} permissions</button>)}</div> : <p className="muted">No custom SaaS roles have been created.</p>}
            <button type="button" className="button button-secondary" onClick={clear} disabled={busy}>Create new custom role</button>
          </div>
          <form className="studio-form" onSubmit={save}>
            <label className="form-field"><span>Role name</span><input value={name} onChange={event=>setName(event.target.value)} required minLength={2} maxLength={100} disabled={busy}/></label>
            <label className="form-field"><span>Job purpose / description</span><textarea rows={3} value={description} onChange={event=>setDescription(event.target.value)} maxLength={500} disabled={busy}/></label>
            <div className="section-heading compact"><div><h4>Permission set</h4><p className="muted">Only approved operational permissions are available. Roles and billing permissions are separated.</p></div></div>
            <div className="role-permission-groups">
              {permissions.map(permission=><label className="compact-row" key={permission.key}><span><strong>{permission.key}</strong><small>{permission.description||""}</small></span><input type="checkbox" checked={keys.includes(permission.key)} onChange={event=>toggle(permission.key,event.target.checked)} disabled={busy}/></label>)}
            </div>
            <div className="form-actions">
              <button className="button button-primary" type="submit" disabled={busy||name.trim().length<2}><Save size={15}/>{selectedId?"Save role":"Create role"}</button>
              {selectedId&&<button className="button button-secondary" type="button" onClick={()=>void remove()} disabled={busy}><Trash2 size={15}/>Delete role</button>}
              <button className="button button-secondary" type="button" onClick={clear} disabled={busy}>Clear</button>
            </div>
          </form>
        </div>
      )}
      {error&&<p className="form-error" role="alert">{error}</p>}
      {message&&<p className="form-success" role="status">{message}</p>}
    </section>
  );
}
