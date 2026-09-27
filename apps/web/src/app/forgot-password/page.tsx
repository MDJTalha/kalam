"use client";
import { FormEvent, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight, Mail, ShieldCheck, Sparkles } from "lucide-react";

export default function ForgotPasswordPage() {
  const [tenantSlug, setTenantSlug] = useState("");
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/auth/forgot-password", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tenant_slug: tenantSlug.trim().toLowerCase(), email: email.trim() }),
      });
      if (!response.ok) throw new Error(response.status === 429 ? "Too many requests. Please wait before trying again." : "We couldn't process your request. Please try again shortly.");
      setSent(true);    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Password recovery is temporarily unavailable.");
    } finally { setBusy(false); }
  }

  return (
    <main className="auth-shell k-auth">
      <section className="auth-brand" aria-label="About Kognivon">
        <Link className="k-brand-lockup" href="/" aria-label="Kognivon home">
          <span className="k-brand-mark" aria-hidden="true"><Sparkles size={23} /></span>
          <span>Kognivon<small>Learning intelligence</small></span>
        </Link>
        <div className="auth-brand-copy">
          <span className="k-overline"><span className="k-overline-dot" /> Account recovery</span>
          <h1>Back to learning, <em>securely.</em></h1>
          <p>Request a password reset using your organization ID and work email. We&apos;ll send instructions if an account matches.</p>
        </div>
        <p className="k-brand-foot">Learning with purpose. Progress with proof.</p>
      </section>
      <section className="auth-panel" aria-labelledby="recovery-title">
        <div className="auth-card">          <div className="k-mobile-brand">Kognivon <span>Learning intelligence</span></div>
          <div className="auth-card-heading">
            <span className="k-form-eyebrow"><Mail size={14} aria-hidden="true" /> Account recovery</span>
            <h2 id="recovery-title">Reset your password</h2>
            <p>Enter your organization ID and work email to request a secure reset link.</p>
          </div>
          {sent ? (
            <div className="form-success" role="status">If the account exists, a reset link will be sent. Check your work inbox and spam folder.</div>
          ) : (
            <form onSubmit={submit} className="form-stack" aria-busy={busy}>
              <label htmlFor="recovery-organization">Organization ID</label>
              <input id="recovery-organization" type="text" autoComplete="organization" required autoCapitalize="none"
                spellCheck={false} placeholder="your-organization" value={tenantSlug} onChange={(event) => setTenantSlug(event.target.value)} />
              <label htmlFor="recovery-email">Work email</label>
              <input id="recovery-email" type="email" autoComplete="email" required placeholder="name@company.com"
                value={email} onChange={(event) => setEmail(event.target.value)} />
              {error && <div className="form-error" role="alert">{error}</div>}
              <button className="button button-primary button-large submit-button" disabled={busy}>
                {busy ? "Sending…" : "Send reset link"} {!busy && <ArrowRight size={18} aria-hidden="true" />}
              </button>
            </form>          )}
          <Link className="text-link" href="/login"><ArrowLeft size={15} aria-hidden="true" /> Back to sign in</Link>
          <div className="k-auth-footer"><ShieldCheck size={15} aria-hidden="true" /> Password reset links expire and can only be used once.</div>
        </div>
      </section>
    </main>
  );
}
