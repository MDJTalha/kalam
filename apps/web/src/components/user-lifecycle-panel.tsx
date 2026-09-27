"use client";

import { useState } from "react";
import { RefreshCw, UserPlus } from "lucide-react";

type Person = { id: string; email: string; first_name: string; last_name: string; employee_number?: string | null; job_title?: string | null; manager_id?: string | null; org_unit_id?: string | null; is_active: boolean };
type Role = { id: string; name: string };

type Unit = { id: string; name: string; unit_type: string };
type Props = { people: Person[]; roles: Role[]; units: Unit[]; accessPermissions: string[]; initialSelectedId?: string };

export function UserLifecyclePanel({ people, roles, units, accessPermissions, initialSelectedId }: Props) {
  const canManage = accessPermissions.includes("users.manage");
  const [peopleState, setPeopleState] = useState(people);
  const [selectedId, setSelectedId] = useState(people.find(person => person.id === initialSelectedId)?.id ?? people[0]?.id ?? "");
  const selected = peopleState.find((item) => item.id === selectedId);
  const [firstName, setFirstName] = useState(selected?.first_name ?? "");
  const [lastName, setLastName] = useState(selected?.last_name ?? "");
  const [employeeNumber, setEmployeeNumber] = useState(selected?.employee_number ?? "");
  const [jobTitle, setJobTitle] = useState(selected?.job_title ?? "");
  const [active, setActive] = useState(selected?.is_active ?? true);
  const [managerId, setManagerId] = useState(selected?.manager_id ?? "");
  const [orgUnitId, setOrgUnitId] = useState(selected?.org_unit_id ?? "");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState(roles[0]?.id ?? "");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function selectPerson(id: string) {
    const person = peopleState.find((item) => item.id === id);
    setSelectedId(id); setFirstName(person?.first_name ?? ""); setLastName(person?.last_name ?? "");
    setEmployeeNumber(person?.employee_number ?? ""); setJobTitle(person?.job_title ?? ""); setActive(person?.is_active ?? true);
    setManagerId(person?.manager_id ?? ""); setOrgUnitId(person?.org_unit_id ?? "");
    setMessage(""); setError("");
  }

  async function updateUser(unlockNow = false) {
    if (!unlockNow && selected?.is_active && !active && !window.confirm("Deactivate this account and revoke its active sessions?")) return;
    setMessage(""); setError("");
    if (!selectedId || busy) return;
    setBusy(true);
    try {
      const payload = unlockNow ? { unlock_now: true } : { first_name: firstName.trim(), last_name: lastName.trim(), employee_number: employeeNumber.trim() || null, job_title: jobTitle.trim() || null, manager_id: managerId || null, org_unit_id: orgUnitId || null, is_active: active };
      const response = await fetch("/api/lms/admin/users/" + selectedId, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "User update failed.");
      if (!unlockNow) setPeopleState(current => current.map(person => person.id === selectedId ? { ...person, ...payload } : person));
      setMessage(unlockNow ? "Account unlocked." : "User profile updated.");
    } catch (err) { setError(err instanceof Error ? err.message : "User update failed."); }
    finally { setBusy(false); }
  }

  async function inviteUser() {
    setMessage(""); setError("");
    if (busy || !inviteEmail.trim() || !inviteRole) return;
    setBusy(true);
    try {
      const response = await fetch("/api/lms/admin/invitations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: inviteEmail.trim(), role_id: inviteRole, expiry_days: 7 }) });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Invitation could not be created.");
      setInviteEmail(""); setMessage("Invitation created. Check email delivery configuration for delivery status.");
    } catch (err) { setError(err instanceof Error ? err.message : "Invitation could not be created."); }
    finally { setBusy(false); }
  }

  return (
    <div className="two-column">
      <div className="soft-panel">
        <div className="section-heading compact"><div><span className="eyebrow">Lifecycle</span><h3>Manage user</h3></div></div>
        <div className="form-grid">
          <label className="form-field full"><span>Employee</span><select value={selectedId} onChange={(event) => selectPerson(event.target.value)}>{peopleState.map((person) => <option key={person.id} value={person.id}>{person.first_name} {person.last_name} · {person.email}</option>)}</select></label>
          <label className="form-field"><span>First name</span><input value={firstName} onChange={(event) => setFirstName(event.target.value)} readOnly={!canManage} /></label>
          <label className="form-field"><span>Last name</span><input value={lastName} onChange={(event) => setLastName(event.target.value)} readOnly={!canManage} /></label>
          <label className="form-field"><span>Employee number</span><input value={employeeNumber} onChange={(event) => setEmployeeNumber(event.target.value)} readOnly={!canManage} /></label>
          <label className="form-field"><span>Job title</span><input value={jobTitle} onChange={(event) => setJobTitle(event.target.value)} readOnly={!canManage} /></label>
          <label className="form-field"><span>Organization unit</span><select value={orgUnitId} onChange={event => setOrgUnitId(event.target.value)} disabled={!canManage}><option value="">Unassigned</option>{units.map(unit => <option key={unit.id} value={unit.id}>{unit.name} · {unit.unit_type}</option>)}</select></label>
          <label className="form-field"><span>Manager</span><select value={managerId} onChange={event => setManagerId(event.target.value)} disabled={!canManage}><option value="">No manager</option>{peopleState.filter(person => person.id !== selectedId && person.is_active).map(person => <option key={person.id} value={person.id}>{person.first_name} {person.last_name}</option>)}</select></label>
          <label className="form-field full"><span>Status</span><select value={active ? "active" : "inactive"} onChange={(event) => setActive(event.target.value === "active")} disabled={!canManage}><option value="active">Active</option><option value="inactive">Inactive</option></select></label>
        </div>
        <div className="form-actions">{canManage&&<><button className="button button-primary" disabled={busy || !selectedId || !firstName.trim() || !lastName.trim()} onClick={() => void updateUser()}>Save changes</button><button className="button button-secondary" disabled={busy || !selectedId} onClick={() => void updateUser(true)}><RefreshCw size={15}/> Unlock account</button></>}{!canManage&&<span className="form-help">User lifecycle changes require the users.manage permission.</span>}</div>
      </div>
      <div className="soft-panel">
        <div className="section-heading compact"><div><span className="eyebrow">Onboarding</span><h3>Invite employee</h3></div><UserPlus size={18}/></div>
        <div className="form-grid"><label className="form-field full"><span>Work email</span><input type="email" disabled={!canManage || busy} value={inviteEmail} onChange={(event) => setInviteEmail(event.target.value)} placeholder="employee@company.com" /></label><label className="form-field full"><span>Initial role</span><select disabled={!canManage || busy} value={inviteRole} onChange={(event) => setInviteRole(event.target.value)}>{roles.map((role) => <option key={role.id} value={role.id}>{role.name}</option>)}</select></label></div>
        <div className="form-actions">{canManage?<button className="button button-primary" disabled={busy || !inviteEmail.trim() || !inviteRole} onClick={() => void inviteUser()}>Send invitation</button>:<span className="form-help">Invitations require the users.manage permission.</span>}</div>
        <p className="form-help">Invitations are tenant-scoped, role-bound and expire after seven days.</p>
      </div>
      {(error || message) && <div className={error ? "form-error full" : "form-success full"} role={error ? "alert" : "status"}>{error || message}</div>}
    </div>
  );
}
