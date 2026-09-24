"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function ResetPasswordForm({ token }: { token: string }) {
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (password !== confirmation) { setError("Passwords do not match."); return; }
    if (password.length < 12) { setError("Use at least 12 characters."); return; }
    setBusy(true);
    try {
      const origin = process.env.NEXT_PUBLIC_API_ORIGIN || "http://localhost:8000";
      const response = await fetch(`${origin}/api/v1/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ token, new_password: password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Reset request failed.");
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reset request failed.");
    } finally { setBusy(false); }
  }

  if (done) {
    return <><div className="form-success">Your password has been updated. You can now sign in.</div><Link className="text-link" href="/login">← Back to sign in</Link></>;
  }

  return token ? (
    <form onSubmit={submit} className="form-stack">
      <label>New password<input type="password" minLength={12} required value={password} onChange={(e)=>setPassword(e.target.value)} autoComplete="new-password" /></label>
      <label>Confirm password<input type="password" minLength={12} required value={confirmation} onChange={(e)=>setConfirmation(e.target.value)} autoComplete="new-password" /></label>
      {error && <div className="form-error" role="alert">{error}</div>}
      <button className="button button-primary button-large submit-button" disabled={busy}>{busy ? "Updating…" : "Update password"} <ArrowRight size={17}/></button>
      <Link className="text-link" href="/login">← Back to sign in</Link>
    </form>
  ) : <div className="form-error">The password-reset token is missing.</div>;
}
