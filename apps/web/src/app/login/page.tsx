"use client";

import { FormEvent, useState } from "react";
import { ArrowRight, BriefcaseBusiness, Eye, EyeOff, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [tenantSlug, setTenantSlug] = useState("demo-corporation");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const apiOrigin = process.env.NEXT_PUBLIC_API_ORIGIN || "http://localhost:8000";
      const response = await fetch(apiOrigin + "/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ tenant_slug: tenantSlug, email, password }),
      });
      if (!response.ok) {
        setError("The credentials could not be authenticated.");
        return;
      }
      router.push("/dashboard");
      router.refresh();
    } catch {
      setError("The learning service is unavailable. Start the API and try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-brand">
        <div className="brand-lockup"><span className="brand-mark"><BriefcaseBusiness size={19} /></span><span>Corporate LMS</span></div>
        <div className="auth-brand-copy"><span className="eyebrow"><ShieldCheck size={15} /> Secure learning workspace</span><h1>Learning that can stand up to scrutiny.</h1><p>Manage people, learning, compliance evidence, skills and credentials from one controlled platform.</p></div>
      </section>
      <section className="auth-panel">
        <div className="auth-card">
          <div className="auth-card-heading"><span className="eyebrow">Sign in</span><h2>Welcome back</h2><p>Use your corporate LMS account to continue.</p></div>
          <form onSubmit={submit} className="form-stack">
            <label>Organization ID<input type="text" autoComplete="organization" required value={tenantSlug} onChange={(e) => setTenantSlug(e.target.value.toLowerCase())} placeholder="your-company" /></label>
            <label>Work email<input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></label>
            <label>Password<span className="password-field"><input type={showPassword ? "text" : "password"} autoComplete="current-password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} /><button type="button" className="icon-button" onClick={() => setShowPassword((v) => !v)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></span></label>
            {error && <div className="form-error" role="alert">{error}</div>}
            <div className="form-link-row"><span></span><a href="/forgot-password">Forgot password?</a></div>
            <button className="button button-primary button-large submit-button" disabled={busy}>{busy ? "Authenticating…" : "Sign in"} <ArrowRight size={17} /></button>
          </form>
        </div>
      </section>
    </main>
  );
}
