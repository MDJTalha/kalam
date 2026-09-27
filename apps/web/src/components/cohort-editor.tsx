"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
type Member = { user_id: string; name: string; email: string; status: string };
type Person = { id: string; first_name: string; last_name: string; email: string; is_active: boolean };
type Cohort = { id: string; name: string; status: string; capacity?: number | null; members: Member[] };
export function CohortEditor({ initialCohort, people, canManageMembers }: { initialCohort: Cohort; people: Person[]; canManageMembers: boolean }) {
  const router = useRouter();
  const [members, setMembers] = useState(initialCohort.members);
  const [status, setStatus] = useState(initialCohort.status);
  const [personId, setPersonId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const available = people.filter(person => person.is_active && !members.some(member => member.user_id === person.id));
  async function request(url: string, method: string, body?: object) {
    const response = await fetch(url, { method, headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Cohort update failed.");
    return data;
  }
  async function run(action: () => Promise<void>) {
    setBusy(true); setError(""); setMessage("");
    try { await action(); router.refresh(); }
    catch (err) { setError(err instanceof Error ? err.message : "Cohort update failed."); }
    finally { setBusy(false); }
  }
  function add(event: FormEvent) { event.preventDefault(); if (!personId) return; const person = people.find(item => item.id === personId);
    void run(async () => {
      await request(`/api/lms/programs/cohorts/${initialCohort.id}/members`, "POST", { user_id: personId });
      setMembers(current => [...current, { user_id: personId, name: `${person?.first_name} ${person?.last_name}`, email: person?.email ?? "", status: "active" }]);
      setPersonId(""); setMessage("Learner added to cohort.");
    });
  }

  function remove(member: Member) {
    if (!window.confirm(`Remove “${member.name}” from this planned cohort?`)) return;
    void run(async () => {
      await request(`/api/lms/programs/cohorts/${initialCohort.id}/members/${member.user_id}`, "DELETE");
      setMembers(current => current.filter(item => item.user_id !== member.user_id)); setMessage("Learner removed.");
    });
  }
  function launch() {
    if (!window.confirm(`Launch “${initialCohort.name}” and assign its program courses to ${members.length} learners?`)) return;
    void run(async () => {
      const result = await request(`/api/lms/programs/cohorts/${initialCohort.id}/launch`, "POST");
      setStatus(result.status); setMessage(`Cohort launched. ${result.enrollments_created} course enrollments created.`);
    });
  }
  return <section className="data-panel" aria-label="Manage cohort">
    <div className="section-heading compact"><div><span className="eyebrow">Delivery control</span><h2>Manage cohort</h2></div></div>
    <p>{status === "planned" ? "Add active learners before launch. Launch assigns the program courses and cannot be repeated." : "This cohort has launched; its learners have their course enrollments."}</p>
    {error && <p className="form-error" role="alert">{error}</p>}{message && <p className="form-success" role="status">{message}</p>}
    {status === "planned" && canManageMembers && <form className="studio-form" onSubmit={add}>
      <div className="form-grid"><label>Active learner<select required value={personId} onChange={event => setPersonId(event.target.value)}>
        <option value="">Choose a learner</option>{available.map(person => <option key={person.id} value={person.id}>{person.first_name} {person.last_name} · {person.email}</option>)}</select></label></div>
      <p className="form-help">{members.length}{initialCohort.capacity ? ` of ${initialCohort.capacity}` : ""} cohort members</p>
      <button type="submit" className="button button-secondary" disabled={busy || !personId}>Add learner</button>
    </form>}
    {status === "planned" && canManageMembers && members.length > 0 && <div className="compact-list">{members.map(member => <div className="compact-row" key={member.user_id}><span>{member.name} · {member.email}</span><button type="button" className="button button-secondary" disabled={busy} onClick={() => remove(member)}>Remove</button></div>)}</div>}
    {status === "planned" && <div className="form-actions"><button type="button" className="button button-primary" disabled={busy || !members.length} onClick={launch}>Launch cohort</button></div>}
  </section>;
}
