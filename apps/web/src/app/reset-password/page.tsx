import Link from "next/link";
import { KeyRound, ShieldCheck, Sparkles } from "lucide-react";
import { ResetPasswordForm } from "@/components/reset-password-form";

export default async function ResetPasswordPage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>;
}) {
  const params = await searchParams;
  const token = params.token || "";
  return (
    <main className="auth-shell k-auth">
      <section className="auth-brand" aria-label="About Kognivon">
        <Link className="k-brand-lockup" href="/" aria-label="Kognivon home">
          <span className="k-brand-mark" aria-hidden="true"><Sparkles size={23} /></span>
          <span>Kognivon<small>Learning intelligence</small></span>
        </Link>
        <div className="auth-brand-copy">
          <span className="k-overline"><span className="k-overline-dot" /> Secure account recovery</span>
          <h1>A fresh start, <em>with confidence.</em></h1>
          <p>Set a new password to get back to your organization&apos;s learning workspace.</p>
        </div>
        <p className="k-brand-foot">Learning with purpose. Progress with proof.</p>
      </section>
      <section className="auth-panel" aria-labelledby="reset-title">        <div className="auth-card">
          <div className="k-mobile-brand">Kognivon <span>Learning intelligence</span></div>
          <div className="auth-card-heading">
            <span className="k-form-eyebrow"><KeyRound size={14} aria-hidden="true" /> Password reset</span>
            <h2 id="reset-title">Choose a new password</h2>
            <p>Use at least 12 characters and a password you do not use elsewhere.</p>
          </div>
          <ResetPasswordForm token={token} />
          <div className="k-auth-footer"><ShieldCheck size={15} aria-hidden="true" /> Reset links expire and can only be used once.</div>
        </div>
      </section>
    </main>
  );
}
