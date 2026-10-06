import Link from "next/link";
import { ShieldX } from "lucide-react";

export default function AccessDeniedPage() {
  return <main className="auth-shell">
    <section className="auth-panel"><div className="auth-card">
      <div className="auth-card-heading"><ShieldX size={26} aria-hidden="true" /><span className="eyebrow">Access control</span>
        <h1>Access denied</h1><p>Your account is signed in, but it does not have permission to open this workspace. Ask your Kalam administrator to review your access.</p>
      </div><Link className="button button-primary button-large submit-button" href="/login">Return to sign in</Link>
    </div></section>
  </main>;
}
