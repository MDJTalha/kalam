"use client";

import { FormEvent, useState } from "react";

type Incident = { id: string; incident_number: string; title: string; severity: string; status: string; impact: string | null; detected_at: string };

async function send(path: string, method: string, body?: Record<string, unknown>) {
  const response = await fetch(path, { method, headers: body ? { "content-type": "application/json" } : undefined, body: body ? JSON.stringify(body) : undefined });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : `Request failed (${response.status})`);
  return payload;
}

export function PlatformIncidentWorkspace({ initialIncidents }: { initialIncidents: Incident[] }) {
  const [incidents, setIncidents] = useState(initialIncidents);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy(true); setMessage("");
    try {
      await send("/api/v1/support/developer/incidents", "POST", { title: data.get("title"), description: data.get("description"), severity: data.get("severity"), impact: data.get("impact") || null });
      const latest = await send("/api/v1/support/developer/incidents", "GET") as Incident[];
      setIncidents(latest); form.reset(); setMessage("Incident recorded and audit event created.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to record incident"); }
    finally { setBusy(false); }
  }
  async function update(id: string, status: string) {
    setBusy(true); setMessage("");
    try {
      await send(`/api/v1/support/developer/incidents/${id}`, "PATCH", { status });
      const latest = await send("/api/v1/support/developer/incidents", "GET") as Incident[];
      setIncidents(latest); setMessage("Incident lifecycle updated and audited.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to update incident"); }
    finally { setBusy(false); }
  }
  return <div className="platform-incident-workspace">
    <form className="studio-form platform-incident-form" onSubmit={submit}>
      <h3>Record a platform incident</h3>
      <div className="form-grid">
        <label>Incident title<input name="title" required minLength={5} maxLength={180}/></label>
        <label>Severity<select name="severity"><option value="sev3">SEV3 · Moderate</option><option value="sev2">SEV2 · High</option><option value="sev1">SEV1 · Critical</option><option value="sev4">SEV4 · Low</option></select></label>
      </div>
      <label>Description<textarea name="description" required minLength={10} maxLength={10000} rows={3}/></label>
      <label>Customer / service impact<input name="impact" maxLength={500}/></label>
      <button className="button button-primary" disabled={busy}> {busy ? "Saving…" : "Create incident"} </button>
    </form>
    <div className="platform-incident-table-wrap">
      <table className="data-table">
        <thead><tr><th>Incident</th><th>Severity</th><th>Status</th><th>Impact</th><th>Detected</th><th>Lifecycle</th></tr></thead>
        <tbody>{incidents.map((incident) => <tr key={incident.id}>
          <td><strong>{incident.incident_number}</strong><br/><span>{incident.title}</span></td>
          <td>{incident.severity.toUpperCase()}</td><td>{incident.status}</td><td>{incident.impact || "—"}</td>
          <td><time dateTime={incident.detected_at}>{new Date(incident.detected_at).toLocaleString()}</time></td>
          <td><select aria-label={`Update ${incident.incident_number} status`} value={incident.status} disabled={busy || incident.status === "resolved"} onChange={(event) => void update(incident.id, event.target.value)}><option value="open">Open</option><option value="investigating">Investigating</option><option value="mitigated">Mitigated</option><option value="resolved">Resolved</option></select></td>
        </tr>)}</tbody>
      </table>
      {incidents.length === 0 && <p className="muted">No platform incidents recorded.</p>}
    </div>
    {message && <p className="platform-incident-status" role="status">{message}</p>}
  </div>;
}
