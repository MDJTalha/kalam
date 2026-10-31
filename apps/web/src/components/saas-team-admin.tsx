"use client";

import { FormEvent, useMemo, useState } from "react";
import { RefreshCw, ShieldCheck, UserPlus, UserRoundX } from "lucide-react";

type Assignment = { id: string; name: string; role_kind: string };
type Member = {
  id: string;
  name: string;
  email: string;
  job_title?: string | null;
  is_active: boolean;
  roles: string[];
  role_assignments: Assignment[];
};
type Role = { id: string; name: string; role_kind: string; description?: string | null };

async function request(path: string, method = "GET", body?: Record<string, unknown>) {
  const response = await fetch(path, {
    method,
    headers: body ? { "content-type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(typeof payload.detail === "string" ? payload.detail : `Request failed (${response.status})`);
  }
  return payload;
}

export function SaaSTeamAdmin({
  initialMembers,
  roles,
}: {
  initialMembers: Member[];
  roles: Role[];
}) {
  const [members, setMembers] = useState(initialMembers);
  const [email, setEmail] = useState("");
  const [roleId, setRoleId] = useState(roles[0]?.id ?? "");
  const [busyKey, setBusyKey] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const visibleMembers = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return members;
    return members.filter(member =>
      [member.name, member.email, member.job_title ?? "", ...member.roles].join(" ").toLowerCase().includes(term)
    );
  }, [members, query]);

  async function invite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!email.trim() || !roleId || busyKey) return;
    setBusyKey("invite");
    setError("");
    setMessage("");
    try {
      await request("/api/lms/admin/invitations", "POST", {
        email: email.trim(),
        role_id: roleId,
        expiry_days: 7,
      });
      setEmail("");
      setMessage("Invitation created. The selected role will be assigned when the invite is accepted.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invitation could not be created.");
    } finally {
      setBusyKey("");
    }
  }

  async function changeRole(member: Member, nextRoleId: string, method: "POST" | "DELETE") {
    const role = roles.find(item => item.id === nextRoleId);
    if (!role || !member.id || busyKey) return;
    setBusyKey(member.id + role.id);
    setError("");
    setMessage("");
    try {
      await request(`/api/lms/organization/users/${member.id}/roles/${role.id}`, method);
      setMembers(current => current.map(item => {
        if (item.id !== member.id) return item;
        const currentAssignments = item.role_assignments ?? [];
        const nextAssignments = method === "POST"
          ? [...currentAssignments.filter(assignment => assignment.id !== role.id), { id: role.id, name: role.name, role_kind: role.role_kind }]
          : currentAssignments.filter(assignment => assignment.id !== role.id);
        return {
          ...item,
          role_assignments: nextAssignments,
          roles: nextAssignments.map(assignment => assignment.name),
        };
      }));
      setMessage(method === "POST" ? `${role.name} assigned to ${member.name}.` : `${role.name} removed from ${member.name}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Role assignment could not be changed.");
    } finally {
      setBusyKey("");
    }
  }

  async function toggleAccount(member: Member) {
    if (busyKey) return;
    const action = member.is_active ? "deactivate and revoke all active sessions for" : "reactivate";
    if (!window.confirm(`Are you sure you want to ${action} ${member.name}?`)) return;
    setBusyKey(member.id);
    setError("");
    setMessage("");
    try {
      const payload = await request(`/api/lms/admin/users/${member.id}`, "PATCH", { is_active: !member.is_active });
      setMembers(current => current.map(item => item.id === member.id ? { ...item, is_active: payload.is_active } : item));
      setMessage(member.is_active ? "Account deactivated and sessions revoked." : "Account reactivated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Account status could not be changed.");
    } finally {
      setBusyKey("");
    }
  }


  return (
    <div className="saas-team-admin">
      <section className="soft-panel">
        <div className="section-heading compact">
          <div><span className="eyebrow">Secure onboarding</span><h3>Invite SaaS team member</h3></div>
          <UserPlus size={18}/>
        </div>
        <form className="form-grid" onSubmit={invite}>
          <label className="form-field"><span>Work email</span><input type="email" value={email} onChange={event => setEmail(event.target.value)} required maxLength={320} placeholder="colleague@company.com"/></label>
          <label className="form-field"><span>Initial role</span><select value={roleId} onChange={event => setRoleId(event.target.value)} required><option value="">Select a role</option>{roles.map(role=><option key={role.id} value={role.id}>{role.name}</option>)}</select></label>
          <div className="form-actions"><button className="button button-primary" type="submit" disabled={busyKey==="invite"||!email.trim()||!roleId}>{busyKey==="invite"?"Creating invitation…":"Create invitation"}</button></div>
        </form>
        <p className="form-help">The invitation is single-use and expires after seven days. The role becomes effective only after the recipient accepts the invitation and sets a password.</p>
      </section>

      <section className="soft-panel">
        <div className="section-heading compact">
          <div><span className="eyebrow">Least-privilege administration</span><h3>Current SaaS operators</h3></div>
          <ShieldCheck size={18}/>
        </div>
        <label className="form-field"><span>Search team</span><input value={query} onChange={event=>setQuery(event.target.value)} placeholder="Name, email, job title or role"/></label>
        <div className="table-wrap">
          <table className="data-table">
            <thead><tr><th>Team member</th><th>Current roles</th><th>Access status</th><th>Actions</th></tr></thead>
            <tbody>
              {visibleMembers.map(member=>(
                <tr key={member.id}>
                  <td><strong>{member.name}</strong><small>{member.email}</small><small>{member.job_title||"No job title"}</small></td>
                  <td>
                    <div className="compact-list">
                      {member.role_assignments.map(assignment=>(
                        <div className="compact-row" key={assignment.id}>
                          <span>{assignment.name}</span>
                          {busyKey!==member.id+assignment.id&&<button className="button button-quiet" type="button" disabled={!!busyKey} onClick={()=>void changeRole(member,assignment.id,"DELETE")}>Remove</button>}
                          {busyKey===member.id+assignment.id&&<span className="muted">Updating…</span>}
                        </div>
                      ))}
                      {!member.role_assignments.length&&<span className="muted">No assigned roles</span>}
                    </div>
                    <label className="form-field"><span>Assign another role</span><select defaultValue="" disabled={!!busyKey} onChange={event=>{const id=event.target.value;event.target.value="";if(id)void changeRole(member,id,"POST");}}><option value="">Choose role…</option>{roles.filter(role=>!member.role_assignments.some(assignment=>assignment.id===role.id)).map(role=><option key={role.id} value={role.id}>{role.name}</option>)}</select></label>
                  </td>
                  <td><span className={member.is_active?"status-badge status-active":"status-badge status-inactive"}>{member.is_active?"Active":"Inactive"}</span></td>
                  <td><button className="button button-secondary" type="button" disabled={!!busyKey} onClick={()=>void toggleAccount(member)}><UserRoundX size={14}/>{member.is_active?"Deactivate & revoke":"Reactivate"}</button></td>
                </tr>
              ))}
              {!visibleMembers.length&&<tr><td colSpan={4}>No matching team members.</td></tr>}
            </tbody>
          </table>
        </div>
        <p className="form-help">Platform Developer and Super Admin assignments have additional server-side restrictions. The last active Super Admin cannot be removed or deactivated.</p>
      </section>
      {(error||message)&&<div className={error?"form-error":"form-success"} role={error?"alert":"status"}>{error||message}</div>}
    </div>
  );
}
