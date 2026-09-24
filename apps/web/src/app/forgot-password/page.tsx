"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { ArrowRight, Mail, ShieldCheck } from "lucide-react";

export default function ForgotPasswordPage() {
  const [tenantSlug, setTenantSlug] = useState("demo-corporation");
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true); setError("");
    try {
      const origin = process.env.NEXT_PUBLIC_API_ORIGIN || "http://localhost:8000";
      const response = await fetch(`${origin}/api/v1/auth/forgot-password`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tenant_slug: tenantSlug, email }),
      });
      if (!response.ok) throw new Error("Request could not be accepted.");
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    } finally { setBusy(false); }
  }

  return (
    <main className="auth-shell">
      <section className="auth-brand"><div className="brand-lockup"><span className="brand-mark"><ShieldCheck size={19}/></span><span>Corporate LMS</span></div><div className="auth-brand-copy"><span className="eyebrow"><Mail size={15}/> Account recovery</span><h1>Recover access securely.</h1><p>Reset requests are scoped to the organization and protected by expiring, single-use tokens.</p></div></section>
      <section className="auth-panel"><div className="auth-card"><div className="auth-card-heading"><span className="eyebrow">Password recovery</span><h2>Forgot password?</h2><p>Enter your organization and work email.</p></div>{sent ? <div className="form-success">If the account exists, a reset message has been queued. Check your corporate inbox and use the expiring link.</div> : <form onSubmit={submit} className="form-stack"><label>Organization ID<input value={tenantSlug} onChange={(e)=>setTenantSlug(e.target.value.toLowerCase())} required /></label><label>Work email<input type="email" value={email} onChange={(e)=>setEmail(e.target.value)} required /></label>{error && <div className="form-error" role="alert">{error}</div>}<button className="button button-primary button-large submit-button" disabled={busy}>{busy ? "Submitting…" : "Send reset link"} <ArrowRight size={17}/></button></form>}<Link className="text-link" href="/login">← Back to sign in</Link></div></section>
    </main>
  );
}
