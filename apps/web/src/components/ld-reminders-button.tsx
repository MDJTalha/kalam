"use client";
import { useState } from "react";
export function LdRemindersButton() {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  async function run() {
    if (!window.confirm("Check due assignments and create eligible in-app reminders now?")) return;
    setBusy(true); setMessage(""); setError("");
    try {
      const response = await fetch("/api/lms/admin/learning/reminders/run", { method: "POST" });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Reminder check failed.");
      setMessage(`Checked ${data.processed ?? 0} assignments; created ${data.created ?? 0} reminders.`);
    } catch (err) { setError(err instanceof Error ? err.message : "Reminder check failed."); }
    finally { setBusy(false); }
  }
  return <div className="stack"><button className="button button-secondary" type="button" disabled={busy} onClick={() => void run()}>{busy ? "Checking…" : "Run reminder check"}</button>
    {message && <p className="form-success" role="status">{message}</p>}
    {error && <p className="form-error" role="alert">{error}</p>}
  </div>;
}
