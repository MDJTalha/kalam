import { KeyRound, ShieldCheck } from "lucide-react";
import { ResetPasswordForm } from "@/components/reset-password-form";

export default async function ResetPasswordPage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>;
}) {
  const params = await searchParams;
  const token = params.token || "";
  return (
    <main className="auth-shell">
      <section className="auth-brand"><div className="brand-lockup"><span className="brand-mark"><ShieldCheck size={19}/></span><span>Corporate LMS</span></div><div className="auth-brand-copy"><span className="eyebrow"><KeyRound size={15}/> Secure account recovery</span><h1>Set a new password.</h1><p>Reset links are single-use and expire automatically.</p></div></section>
      <section className="auth-panel"><div className="auth-card"><div className="auth-card-heading"><span className="eyebrow">Password reset</span><h2>Choose a new password</h2><p>Use a strong password you do not reuse elsewhere.</p></div><ResetPasswordForm token={token}/></div></section>
    </main>
  );
}
