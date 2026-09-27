"use client";
import { useState } from "react";
type Role = { id: string; name: string };
const EMAIL = /^[^\s@,]+@[^\s@,]+\.[^\s@,]+$/;
export function PeopleBulkInvite({ roles }: { roles: Role[] }) {
  const [emails, setEmails] = useState<string[]>([]);
  const [roleId, setRoleId] = useState(roles[0]?.id ?? "");
  const [busy, setBusy] = useState(false);
  const [results, setResults] = useState<Array<{ email: string; result: string }>>([]);
  const [error, setError] = useState("");
  async function load(file?: File) {
    setError(""); setResults([]); setEmails([]);
    if (!file) return;
    if (file.size > 128_000) { setError("File must be smaller than 128 KB."); return; }
    const lines = (await file.text()).replace(/^\uFEFF/, "").split(/\r?\n/).map(line => line.trim()).filter(Boolean);
    const header = lines.shift()?.toLowerCase();
    if (header !== "email") { setError("Use a one-column CSV with 'email' as its first row."); return; }
    const normalized = lines.map(line => line.toLowerCase());
    if (!normalized.length || normalized.length > 100 || normalized.some(line => !EMAIL.test(line)) || new Set(normalized).size !== normalized.length) {
      setError("Provide 1–100 unique, valid email addresses, one per row."); return;
    }
    setEmails(normalized);
  }
  async function send() {
    if (!emails.length || !roleId || busy) return;
    if (!window.confirm(`Send ${emails.length} tenant invitations? Invitations may generate emails.`)) return;
    setBusy(true); setResults([]);
    const outcomes: Array<{ email: string; result: string }> = [];
    for (const email of emails) {
      try {
        const response = await fetch("/api/lms/admin/invitations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, role_id: roleId, expiry_days: 7 }) });
        const data = await response.json().catch(() => ({}));
        outcomes.push({ email, result: response.ok ? "Invited" : (typeof data.detail === "string" ? data.detail : "Failed") });
      } catch { outcomes.push({ email, result: "Connection failed" }); }
      setResults([...outcomes]);
    }
    setBusy(false);
  }
  return <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Bulk onboarding</span><h2>Invite people from CSV</h2></div></div>
    <p>Upload a CSV containing one <code>email</code> column. Review the list and choose the access role before sending invitations.</p>
    <div className="form-grid"><label className="form-field"><span>CSV file</span><input type="file" accept=".csv,text/csv" onChange={event => void load(event.target.files?.[0])} disabled={busy} /></label>
      <label className="form-field"><span>Initial role for all invitees</span><select value={roleId} onChange={event => setRoleId(event.target.value)} disabled={busy}>{roles.map(role => <option key={role.id} value={role.id}>{role.name}</option>)}</select></label></div>
    {error && <p className="form-error" role="alert">{error}</p>}
    {emails.length > 0 && <><p role="status">{emails.length} valid addresses ready. First: {emails[0]}{emails.length > 1 ? `; last: ${emails[emails.length - 1]}` : ""}</p>
      <details><summary>Review all {emails.length} addresses</summary><ul>{emails.map(email => <li key={email}>{email}</li>)}</ul></details>
      <button className="button button-primary" type="button" disabled={busy || !roleId || results.length > 0} onClick={() => void send()}>{busy ? `Processing ${results.length} of ${emails.length}…` : results.length ? "Processed — select another file to invite more" : `Send ${emails.length} invitations`}</button></>}
    {results.length > 0 && <div className="table-wrap" aria-live="polite"><table className="data-table"><thead><tr><th scope="col">Email</th><th scope="col">Result</th></tr></thead><tbody>{results.map(item => <tr key={item.email}><td>{item.email}</td><td>{item.result}</td></tr>)}</tbody></table></div>}
  </section>;
}
