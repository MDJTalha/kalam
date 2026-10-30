"use client";
import { FormEvent, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, Eye, EyeOff, LockKeyhole, ShieldCheck, Target, UsersRound } from "lucide-react";
import { KalamBrand } from "@/components/kalam-brand";

export function LoginClient({ initialOrganization = "", initialSsoError = "" }: { initialOrganization?: string; initialSsoError?: string }) {
  const router = useRouter();
  const linkedOrganization = initialOrganization.trim().toLowerCase();
  const [showPassword, setShowPassword] = useState(false);
  const [tenantSlug, setTenantSlug] = useState(linkedOrganization);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(initialSsoError);
  const [passwordAvailable, setPasswordAvailable] = useState(true);
  const [organizationName, setOrganizationName] = useState("");
  const [ssoProviders, setSsoProviders] = useState<{ provider: string; label: string }[]>([]);
  const discoveryRequestId = useRef(0);
  const [discoveryState, setDiscoveryState] = useState<"idle" | "checking" | "recognized" | "unrecognized" | "unavailable">(
    linkedOrganization.length >= 2 ? "checking" : "idle",
  );

  useEffect(() => {
    const slug = tenantSlug.trim().toLowerCase();
    if (slug.length < 2) return;
    const requestId = ++discoveryRequestId.current;
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      try {
        const response = await fetch("/api/lms/auth/discovery/" + encodeURIComponent(slug), {
          cache: "no-store",
          signal: controller.signal,
        });
        if (!response.ok) {
          if (requestId !== discoveryRequestId.current) return;
          setDiscoveryState("unavailable");
          return;
        }
        const payload = await response.json() as {
          recognized?: boolean;
          tenant_name?: string | null;
          sso_providers?: { provider: string; label: string }[];
          password_available?: boolean;
        };
        if (requestId !== discoveryRequestId.current) return;
        setOrganizationName(payload.recognized ? String(payload.tenant_name || "") : "");
        setSsoProviders(payload.recognized ? (payload.sso_providers || []) : []);
        setPasswordAvailable(payload.recognized ? payload.password_available !== false : true);
        setDiscoveryState(payload.recognized ? "recognized" : "unrecognized");
      } catch {
        if (!controller.signal.aborted && requestId === discoveryRequestId.current) {
          setOrganizationName("");
          setSsoProviders([]);
          setPasswordAvailable(true);
          setDiscoveryState("unavailable");
        }
      }
    }, 350);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [tenantSlug]);

  function changeTenantSlug(value: string) {
    discoveryRequestId.current += 1;
    setTenantSlug(value);
    setOrganizationName("");
    setSsoProviders([]);
    setPasswordAvailable(true);
    setDiscoveryState(value.trim().length >= 2 ? "checking" : "idle");
  }

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
      });
      if (!response.ok) {
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
      // The login response has already set the HttpOnly session cookie. Navigate
      // without an immediate refresh so the App Router does not race its new session.
      router.replace("/dashboard");
    } catch {
      setError("We couldn't reach Kalam. Check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-shell k-auth">
      <section className="auth-brand" aria-label="About Kalam">
        <KalamBrand dark descriptor="Enterprise Workforce Capability Platform" className="k-brand-lockup" />
        <div className="auth-brand-copy">
          <h1>Build capability. <em>Prove readiness.</em></h1>
          <p>Access the role-aware workspace that connects learning, skills, compliance, assessments and development across your organization.</p>
          <div className="k-proof" role="group" aria-label="Platform principles">
            <span><ShieldCheck size={16} aria-hidden="true" /> Governed workflows</span>
            <span><Target size={16} aria-hidden="true" /> Connected evidence</span>
            <span><UsersRound size={16} aria-hidden="true" /> Role-aware access</span>
          </div>
        </div>
        <p className="k-brand-foot">Workforce capability, with clarity.</p>
      </section>

      <section className="auth-panel" aria-labelledby="login-title">
        <div className="auth-card">
          <KalamBrand descriptor="Enterprise Workforce Capability Platform" className="k-mobile-brand" />
          <div className="auth-card-heading">
            <span className="k-form-eyebrow"><LockKeyhole size={14} aria-hidden="true" /> Secure access</span>
            <h1 id="login-title">Welcome back</h1>
            <p>Sign in securely to your organization&apos;s Kalam workspace.</p>
          </div>

          <form onSubmit={submit} className="form-stack" aria-busy={busy}>
            <label htmlFor="login-organization">Organization ID</label>
            <input id="login-organization" name="organization" type="text" autoComplete="organization"
              autoCapitalize="none" spellCheck={false} required placeholder="your-organization"
              value={tenantSlug} onChange={(event) => changeTenantSlug(event.target.value)} aria-describedby="organization-hint" />
            <p className="k-field-hint" id="organization-hint" aria-live="polite" aria-atomic="true">{discoveryState === "checking"
              ? "Checking organization ID…"
              : discoveryState === "recognized"
                ? organizationName ? `Organization recognized: ${organizationName}.` : "Organization recognized."
                : discoveryState === "unrecognized"
                  ? "We couldn't confirm this Organization ID. Check it or contact your administrator."
                  : discoveryState === "unavailable"
                    ? "Organization lookup is temporarily unavailable. You can still try signing in."
                    : linkedOrganization
                      ? "Organization detected from your company sign-in link. You can change it if needed."
                      : "Use the Organization ID supplied by your administrator, or your company-specific Kalam sign-in link."}</p>
            {error && <div id="login-error" className="form-error" role="alert">{error}</div>}
            {ssoProviders.length > 0 && <>
              <div className="k-sso-stack">
                {ssoProviders.map(provider => <a className="k-sso-button" key={provider.provider} href={"/api/auth/sso/" + encodeURIComponent(tenantSlug.trim().toLowerCase()) + "/oidc/start"}>
                  <ShieldCheck size={16} aria-hidden="true" /><span>Continue with {provider.label}</span><ArrowRight size={16} aria-hidden="true" />
                </a>)}
              </div>
              {passwordAvailable && <div className="k-auth-divider"><span>or use password</span></div>}
            </>}

            {passwordAvailable ? <>
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
              </div>

              <button className="button button-primary button-large submit-button" type="submit" disabled={busy}>
                <span>{busy ? "Signing in…" : "Sign in to Kalam"}</span>
                {!busy && <ArrowRight size={18} aria-hidden="true" />}
              </button>
            </> : <div className="k-auth-method-note" role="status"><ShieldCheck size={15} aria-hidden="true" /><span>{ssoProviders.length > 0
              ? "Password sign-in is disabled for this organization. Use the approved enterprise SSO method above."
              : "No sign-in method is currently available for this organization. Contact your organization administrator for access."}</span></div>}
          </form>

          <p className="k-support">Need access or your Organization ID? Contact your organization&apos;s Kalam administrator.</p>
          <div className="k-auth-footer"><ShieldCheck size={15} aria-hidden="true" /><span>Organization-scoped access keeps each workspace separated and role-aware.</span></div>
          <Link className="k-back-link" href="/"><ArrowLeft size={14} aria-hidden="true" /> Back to Kalam platform</Link>
        </div>
      </section>
    </main>
  );
}
