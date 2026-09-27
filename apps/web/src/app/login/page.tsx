"use client";
import { FormEvent, useState } from "react";
import Link from "next/link";
import { ArrowRight, Eye, EyeOff, LockKeyhole, ShieldCheck, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [tenantSlug, setTenantSlug] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST", headers: { "Content-Type": "application/json" },
        credentials: "include", cache: "no-store",
        body: JSON.stringify({ tenant_slug: tenantSlug.trim().toLowerCase(), email: email.trim(), password }),
      });      if (!response.ok) {
        let message = response.status === 401
          ? "We couldn't sign you in. Check your organization ID, email and password."
          : response.status === 429
            ? "Too many attempts. Wait a moment before trying again."
            : "We couldn't sign you in right now. Please try again shortly.";
        if (response.status !== 401 && response.status !== 429) {
          try {
            const payload = await response.json() as { detail?: string };
            if (typeof payload.detail === "string" && response.status === 400) message = payload.detail;
          } catch { /* Keep a safe recovery message. */ }
        }
        setError(message);
        return;
      }
      router.replace("/dashboard");
      router.refresh();
    } catch {
      setError("We couldn't reach Kognivon. Check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-shell k-auth">      <section className="auth-brand" aria-label="About Kognivon">
        <Link className="k-brand-lockup" href="/" aria-label="Kognivon home">
          <span className="k-brand-mark" aria-hidden="true"><Sparkles size={23} /></span>
          <span>Kognivon<small>Learning intelligence</small></span>
        </Link>
        <div className="auth-brand-copy">
          <span className="k-overline"><span className="k-overline-dot" /> The learning intelligence platform</span>
          <h1>Build a workforce <em>ready for what&apos;s next.</em></h1>
          <p>Bring learning, skills and compliance into focus, with a clear view of progress across your organization.</p>
          <div className="k-proof" aria-label="Platform capabilities">
            <span><ShieldCheck size={16} aria-hidden="true" /> Governed learning</span>
            <span><Sparkles size={16} aria-hidden="true" /> Capability intelligence</span>
          </div>
        </div>
        <p className="k-brand-foot">Learning with purpose. Progress with proof.</p>
      </section>
      <section className="auth-panel" aria-labelledby="login-title">
        <div className="auth-card">
          <div className="k-mobile-brand">Kognivon <span>Learning intelligence</span></div>
          <div className="auth-card-heading">
            <span className="k-form-eyebrow"><LockKeyhole size={14} aria-hidden="true" /> Secure access</span>
            <h2 id="login-title">Welcome back</h2>
            <p>Sign in to your organization&apos;s learning workspace.</p>
          </div>          <form onSubmit={submit} className="form-stack" aria-busy={busy}>
            <label htmlFor="login-organization">Organization ID</label>
            <input id="login-organization" name="organization" type="text" autoComplete="organization"
              autoCapitalize="none" spellCheck={false} required placeholder="your-organization"
              value={tenantSlug} onChange={(event) => setTenantSlug(event.target.value)} aria-describedby="organization-hint" />
            <p className="k-field-hint" id="organization-hint">Your administrator can provide this ID.</p>
            <label htmlFor="login-email">Work email</label>
            <input id="login-email" name="email" type="email" autoComplete="username" required
              placeholder="name@company.com" value={email} onChange={(event) => setEmail(event.target.value)} />
            <div className="k-label-row">
              <label htmlFor="login-password">Password</label>
              <Link href="/forgot-password">Forgot password?</Link>
            </div>
            <div className="password-field">
              <input id="login-password" name="password" type={showPassword ? "text" : "password"}
                autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)}
                aria-invalid={Boolean(error)} aria-describedby={error ? "login-error" : undefined} />
              <button type="button" className="icon-button" onClick={() => setShowPassword((value) => !value)}
                aria-label={showPassword ? "Hide password" : "Show password"} aria-pressed={showPassword}>
                {showPassword ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}
              </button>
            </div>            {error && <div id="login-error" className="form-error" role="alert">{error}</div>}
            <button className="button button-primary button-large submit-button" type="submit" disabled={busy}>
              <span>{busy ? "Signing in…" : "Sign in to Kognivon"}</span>
              {!busy && <ArrowRight size={18} aria-hidden="true" />}
            </button>
          </form>
          <p className="k-support">Need access? Contact your organization&apos;s learning administrator.</p>
          <div className="k-auth-footer"><ShieldCheck size={15} aria-hidden="true" /> Your workspace is protected by organization-based access.</div>
        </div>
      </section>
    </main>
  );
}
