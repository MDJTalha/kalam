import Link from "next/link";
import { CircleAlert, RefreshCw } from "lucide-react";

export default function ServiceUnavailablePage() {
  return <main className="auth-shell k-auth">
    <section className="auth-brand"><div className="auth-brand-copy"><span className="eyebrow">Kalam Learning</span><h1>Learning and capability, connected.</h1><p>Your organization’s learning workspace is temporarily having trouble reaching its authentication service.</p></div></section>
    <section className="auth-panel"><div className="auth-card" role="alert">
      <div className="module-icon"><CircleAlert size={22}/></div>
      <span className="eyebrow">Temporary service interruption</span>
      <h2>Kalam is temporarily unavailable</h2>
      <p>The authentication service could not be reached. Your session and account data have not been changed. Please try again shortly.</p>
      <div className="form-actions"><Link className="button button-primary" href="/login"><RefreshCw size={15}/> Try again</Link></div>
    </div></section>
  </main>;
}
