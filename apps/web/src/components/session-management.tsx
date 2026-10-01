"use client";

import { useEffect, useState } from "react";
import { LogOut, RefreshCw, ShieldCheck } from "lucide-react";

type Session = { id: string; is_current: boolean; status: "active" | "expired" | "revoked"; expires_at: string; revoked_at?: string | null };

export function SessionManagement({ timezone = "UTC" }: { timezone?: string }) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [confirmAction, setConfirmAction] = useState<"others" | string | null>(null);

  async function load() {
    setError("");
    setLoading(true);
    try {
      const response = await fetch("/api/lms/auth/sessions", { cache: "no-store" });
      const data: unknown = await response.json().catch(() => null);
      if (!response.ok) {
        const detail = data && typeof data === "object" && "detail" in data && typeof data.detail === "string" ? data.detail : "Sessions could not be loaded.";
        setError(detail);
        return;
      }
      if (!Array.isArray(data)) {
        setError("Sessions could not be loaded.");
        return;
      }
      setSessions(data as Session[]);
    } catch {
      setError("Sessions could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let mounted = true;
    fetch("/api/lms/auth/sessions", { cache: "no-store" })
      .then(async (response) => ({ ok: response.ok, data: await response.json().catch(() => null) as unknown }))
      .then(({ ok, data }) => {
        if (!mounted) return;
        if (!ok) {
          const detail = data && typeof data === "object" && "detail" in data && typeof data.detail === "string" ? data.detail : "Sessions could not be loaded.";
          setError(detail);
        } else if (Array.isArray(data)) {
          setSessions(data as Session[]);
        } else {
          setError("Sessions could not be loaded.");
        }
        setLoading(false);
      })
      .catch(() => { if (mounted) { setError("Sessions could not be loaded."); setLoading(false); } });
    return () => { mounted = false; };
  }, []);

  async function revoke(id: string) {
    setBusy(true); setMessage(""); setError("");
    try {
      const response = await fetch("/api/lms/auth/sessions/" + id, { method: "DELETE" });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) setError(typeof data.detail === "string" ? data.detail : "Session could not be revoked.");
      else { setMessage("Session revoked."); await load(); }
    } catch { setError("Session could not be revoked."); }
    finally { setBusy(false); }
  }

  async function revokeOthers() {
    setBusy(true); setMessage(""); setError("");
    try {
      const response = await fetch("/api/lms/auth/sessions/revoke-others", { method: "POST" });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) setError(typeof data.detail === "string" ? data.detail : "Other sessions could not be revoked.");
      else { setMessage(String(data.count ?? 0) + " other session(s) revoked."); await load(); }
    } catch { setError("Other sessions could not be revoked."); }
    finally { setBusy(false); }
  }

  async function confirmDestructiveAction() {
    if (!confirmAction) return;
    const action = confirmAction;
    setConfirmAction(null);
    if (action === "others") await revokeOthers();
    else await revoke(action);
  }

  return (
    <div className="data-panel">
      <div className="section-heading compact">
        <div><span className="eyebrow">Security</span><h2>Active sessions</h2><p>Review signed-in sessions and revoke access you no longer recognize.</p></div>
        <ShieldCheck size={20} />
      </div>
      <div className="form-actions"><button className="button button-secondary" onClick={() => void load()} disabled={busy || loading}><RefreshCw size={15}/> {loading ? "Loading…" : "Refresh"}</button><button className="button button-primary" onClick={() => setConfirmAction("others")} disabled={busy || loading}><LogOut size={15}/> Sign out other sessions</button></div>
      {error && <div className="form-error" role="alert">{error}</div>}
      {message && <div className="form-success" role="status">{message}</div>}
      {confirmAction && <div className="form-actions" role="group" aria-label="Confirm session action"><strong>{confirmAction === "others" ? "Sign out all other sessions?" : "Revoke this session?"}</strong><button className="button button-primary" onClick={() => void confirmDestructiveAction()} disabled={busy}>Confirm</button><button className="button button-secondary" onClick={() => setConfirmAction(null)} disabled={busy}>Cancel</button></div>}
      <div className="table-wrap" tabIndex={0} aria-label="Active sessions table"><table className="data-table"><thead><tr><th scope="col">Session</th><th scope="col">Status</th><th scope="col">Expires</th><th scope="col">Action</th></tr></thead><tbody>{loading ? <tr><td colSpan={4}>Loading session records…</td></tr> : sessions.length ? sessions.map((session) => <tr key={session.id}><td><strong>{session.is_current ? "Current browser" : "Signed-in session"}</strong><small className="code-pill">{session.id.slice(0, 8)}</small></td><td><span className={"status-badge " + (session.status === "active" ? "success" : "muted")}>{session.status}</span></td><td>{new Date(session.expires_at).toLocaleString(undefined,{timeZone:timezone})}</td><td>{session.is_current || session.status !== "active" ? "—" : <button className="button button-secondary" onClick={() => setConfirmAction(session.id)} disabled={busy}>Revoke</button>}</td></tr>) : <tr><td colSpan={4}>No session records are available.</td></tr>}</tbody></table></div>
    </div>
  );
}
