"use client";

import { useEffect, useMemo, useState } from "react";
import { Pencil, Plus, Save, ShieldCheck, Trash2, X } from "lucide-react";

type TenantOption = { id: string; name: string; slug: string; status: string };
type PermissionOption = { id: string; key: string; description?: string | null };
type RoleRow = {
  id: string;
  name: string;
  description?: string | null;
  role_kind: string;
  permission_keys: string[];
};

async function requestJson(path: string, method = "GET", body?: Record<string, unknown>) {
  const response = await fetch(path, {
    method,
    headers: body ? { "content-type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload && typeof payload.detail === "string" ? payload.detail : null;
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return payload;
}

export function SaaSRoleManagement({
  tenants,
  permissions,
}: {
  tenants: TenantOption[];
  permissions: PermissionOption[];
}) {
  const [tenantId, setTenantId] = useState(tenants[0]?.id ?? "");
  const [roles, setRoles] = useState<RoleRow[]>([]);
  const [selectedRoleId, setSelectedRoleId] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const selectedRole = roles.find((role) => role.id === selectedRoleId);
  const editable = !selectedRole || selectedRole.role_kind === "custom";
  const permissionGroups = useMemo(() => {
    const groups = new Map<string, PermissionOption[]>();
    for (const permission of permissions) {
      const prefix = permission.key.split(".")[0] || "other";
      groups.set(prefix, [...(groups.get(prefix) ?? []), permission]);
    }
    return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [permissions]);

  async function loadRoles(nextTenantId = tenantId) {
    if (!nextTenantId) {
      setRoles([]);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const rows = await requestJson(`/api/lms/saas/crm/tenants/${nextTenantId}/roles`) as RoleRow[];
      setRoles(Array.isArray(rows) ? rows : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load tenant roles.");
      setRoles([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadRoles(tenantId);
    // loadRoles is intentionally driven by the selected tenant only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantId]);

  function selectRole(role: RoleRow) {
    setSelectedRoleId(role.id);
    setName(role.name);
    setDescription(role.description ?? "");
    setSelectedPermissions(role.permission_keys ?? []);
    setMessage("");
    setError("");
  }

  function startNewRole() {
    setSelectedRoleId("");
    setName("");
    setDescription("");
    setSelectedPermissions([]);
    setMessage("");
    setError("");
  }

  function togglePermission(key: string, checked: boolean) {
    setSelectedPermissions((current) =>
      checked ? [...new Set([...current, key])] : current.filter((item) => item !== key)
    );
  }

  async function saveRole(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tenantId || !name.trim() || busy || !editable) return;
    setBusy(true);
    setMessage("");
    setError("");
    try {
      let roleId = selectedRoleId;
      if (!roleId) {
        const created = await requestJson(
          `/api/lms/saas/crm/tenants/${tenantId}/roles`,
          "POST",
          { name: name.trim(), description: description.trim() || null, permission_keys: selectedPermissions },
        );
        roleId = String(created.id);
      } else {
        await requestJson(
          `/api/lms/saas/crm/tenants/${tenantId}/roles/${roleId}`,
          "PATCH",
          { name: name.trim(), description: description.trim() || null },
        );
        await requestJson(
          `/api/lms/saas/crm/tenants/${tenantId}/roles/${roleId}/permissions`,
          "PUT",
          { permission_keys: selectedPermissions },
        );
      }
      await loadRoles(tenantId);
      setSelectedRoleId(roleId);
      setMessage("Role saved successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save role.");
    } finally {
      setBusy(false);
    }
  }

  async function deleteRole() {
    if (!selectedRole || selectedRole.role_kind !== "custom" || busy) return;
    if (!window.confirm(`Delete the custom role "${selectedRole.name}"? This is allowed only when no users are assigned to it.`)) return;
    setBusy(true);
    setMessage("");
    setError("");
    try {
      await requestJson(
        `/api/lms/saas/crm/tenants/${tenantId}/roles/${selectedRole.id}`,
        "DELETE",
      );
      startNewRole();
      await loadRoles(tenantId);
      setMessage("Custom role deleted.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete role.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="saas-role-management">
      <section className="data-panel">
        <div className="section-heading">
          <div>
            <span className="eyebrow">Platform governance</span>
            <h2>Customer tenant roles</h2>
            <p className="muted">Create and govern custom roles within a selected customer tenant. Built-in roles remain protected from accidental changes.</p>
          </div>
          <ShieldCheck size={22} aria-hidden="true" />
        </div>
        <div className="form-grid">
          <label className="form-field full">
            <span>Customer tenant</span>
            <select value={tenantId} onChange={(event) => { setTenantId(event.target.value); startNewRole(); }}>
              {tenants.map((tenant) => (
                <option key={tenant.id} value={tenant.id}>{tenant.name} · {tenant.slug} · {tenant.status}</option>
              ))}
            </select>
          </label>
        </div>
      </section>

      <div className="two-column">
        <section className="soft-panel">
          <div className="section-heading compact">
            <div><span className="eyebrow">Role catalogue</span><h3>Available roles</h3></div>
            <button className="button button-secondary" type="button" onClick={startNewRole} disabled={!tenantId || busy}>
              <Plus size={15} /> New custom role
            </button>
          </div>
          {loading ? <p className="muted">Loading roles…</p> : roles.length === 0 ? <p className="muted">No role definitions found for this tenant.</p> : (
            <div className="table-wrap">
              <table className="data-table">
                <thead><tr><th>Role</th><th>Type</th><th>Permissions</th><th>Action</th></tr></thead>
                <tbody>
                  {roles.map((role) => (
                    <tr key={role.id}>
                      <td><strong>{role.name}</strong><small>{role.description || "No description"}</small></td>
                      <td>{role.role_kind}</td>
                      <td>{role.permission_keys?.length ?? 0}</td>
                      <td>
                        <button className="button button-quiet" type="button" onClick={() => selectRole(role)}>
                          <Pencil size={14} /> {role.role_kind === "custom" ? "Edit" : "View"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="soft-panel">
          <div className="section-heading compact">
            <div><span className="eyebrow">{selectedRole ? selectedRole.role_kind : "Custom role"}</span><h3>{selectedRole ? "Role details" : "Create role"}</h3></div>
          </div>
          <form className="studio-form" onSubmit={saveRole}>
            <label className="form-field"><span>Role name</span><input value={name} onChange={(event) => setName(event.target.value)} minLength={2} maxLength={100} required disabled={!editable || busy} /></label>
            <label className="form-field"><span>Description</span><textarea value={description} onChange={(event) => setDescription(event.target.value)} maxLength={500} rows={3} disabled={!editable || busy} /></label>
            <div className="section-heading compact"><div><h4>Permissions</h4><p className="muted">Only tenant permissions are available here. SaaS platform privileges cannot be granted to customer roles.</p></div></div>
            <div className="role-permission-groups">
              {permissionGroups.map(([group, items]) => (
                <fieldset className="soft-panel" key={group}>
                  <legend>{group}</legend>
                  {items.map((permission) => (
                    <label className="compact-row" key={permission.key}>
                      <span><strong>{permission.key}</strong><small>{permission.description || ""}</small></span>
                      <input
                        type="checkbox"
                        checked={selectedPermissions.includes(permission.key)}
                        onChange={(event) => togglePermission(permission.key, event.target.checked)}
                        disabled={!editable || busy}
                      />
                    </label>
                  ))}
                </fieldset>
              ))}
            </div>
            {editable && (
              <div className="form-actions">
                <button className="button button-primary" type="submit" disabled={busy || !tenantId || name.trim().length < 2}>
                  <Save size={15} /> {busy ? "Saving…" : selectedRole ? "Save role" : "Create role"}
                </button>
                {selectedRole && <button className="button button-danger" type="button" onClick={deleteRole} disabled={busy}><Trash2 size={15}/> Delete role</button>}
                <button className="button button-secondary" type="button" onClick={startNewRole} disabled={busy}><X size={15}/> Clear</button>
              </div>
            )}
            {!editable && <p className="form-help">Built-in roles are protected. Create a custom role to define a different permission set.</p>}
            {message && <p className="form-success" role="status">{message}</p>}
            {error && <p className="form-error" role="alert">{error}</p>}
          </form>
        </section>
      </div>
    </div>
  );
}
