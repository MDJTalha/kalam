"use client";

import { useEffect, useState } from "react";
import { LogOut, RefreshCw, ShieldCheck } from "lucide-react";

type Session = { id: string; is_current: boolean; status: "active" | "expired" | "revoked"; expires_at: string; revoked_at?: string | null };

export function SessionManagement() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function load() {
    setError("");
    const response = await fetch("/api/lms/auth/sessions", { cache: "no-store" });
    const data = await response.json().catch(() => []);
    if (!response.ok) { setError(data.detail || "Sessions could not be loaded."); return; }
    setSessions(data);
  }

  useEffect(() => {
    let mounted = true;
    fetch("/api/lms/auth/sessions", { cache: "no-store" })
      .then(async (response) => ({ ok: response.ok, data: await response.json().catch(() => []) }))
      .then(({ ok, data }) => {
        if (!mounted) return;
        if (!ok) setError(data.detail || "Sessions could not be loaded.");
        else setSessions(data);
      })
      .catch(() => { if (mounted) setError("Sessions could not be loaded."); });
    return () => { mounted = false; };
  }, []);

  async function revoke(id: string) {
    setBusy(true); setMessage(""); setError("");
    const response = await fetch("/api/lms/auth/sessions/" + id, { method: "DELETE" });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) setError(data.detail || "Session could not be revoked.");
    else { setMessage("Session revoked."); await load(); }
    setBusy(false);
  }

  async function revokeOthers() {
    setBusy(true); setMessage(""); setError("");
    const response = await fetch("/api/lms/auth/sessions/revoke-others", { method: "POST" });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) setError(data.detail || "Other sessions could not be revoked.");
    else { setMessage(String(data.count ?? 0) + " other session(s) revoked."); await load(); }
    setBusy(false);
  }

  return (
    <div className="data-panel">
      <div className="section-heading compact">
        <div><span className="eyebrow">Security</span><h2>Active sessions</h2><p>Review signed-in sessions and revoke access you no longer recognize.</p></div>
        <ShieldCheck size={20} />
      </div>
      <div className="form-actions"><button className="button button-secondary" onClick={() => void load()} disabled={busy}><RefreshCw size={15}/> Refresh</button><button className="button button-primary" onClick={() => void revokeOthers()} disabled={busy}><LogOut size={15}/> Sign out other sessions</button></div>
      {error && <div className="form-error" role="alert">{error}</div>}
      {message && <div className="form-success" role="status">{message}</div>}
      <div className="table-wrap"><table className="data-table"><thead><tr><th>Session</th><th>Status</th><th>Expires</th><th>Action</th></tr></thead><tbody>{sessions.length ? sessions.map((session) => <tr key={session.id}><td><strong>{session.is_current ? "Current browser" : "Signed-in session"}</strong><small className="code-pill">{session.id.slice(0, 8)}</small></td><td><span className={"status-badge " + (session.status === "active" ? "success" : "muted")}>{session.status}</span></td><td>{new Date(session.expires_at).toLocaleString()}</td><td>{session.is_current || session.status !== "active" ? "—" : <button className="button button-secondary" onClick={() => void revoke(session.id)} disabled={busy}>Revoke</button>}</td></tr>) : <tr><td colSpan={4}>No session records are available.</td></tr>}</tbody></table></div>
    </div>
  );
}
