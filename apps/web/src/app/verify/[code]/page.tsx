import Link from "next/link";
import { Award, ShieldCheck } from "lucide-react";
import { apiJson } from "@/lib/server-api";

type Verification = { valid: boolean; certificate_id: string; course: string; learner: string; issued_at: string; expires_at?: string | null; revoked: boolean };

export default async function VerificationPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const data = await apiJson<Verification>(`/api/v1/certificates/verify/${encodeURIComponent(code)}`);
  return (
    <main className="auth-shell">
      <section className="auth-brand"><div className="brand-lockup"><span className="brand-mark"><ShieldCheck size={19}/></span><span>Corporate LMS</span></div><div className="auth-brand-copy"><span className="eyebrow"><ShieldCheck size={15}/> Credential verification</span><h1>Verify learning evidence.</h1><p>This public page reports the current credential status returned by the LMS verification service.</p></div></section>
      <section className="auth-panel"><div className="auth-card verification-card">{data ? <><div className={`verification-icon ${data.valid ? "valid" : "invalid"}`}><Award size={34}/></div><span className={`status-badge ${data.valid ? "success" : "danger"}`}>{data.valid ? "Valid credential" : data.revoked ? "Revoked credential" : "Expired credential"}</span><h2>{data.course}</h2><p className="verification-learner">{data.learner}</p><div className="detail-grid"><span><b>Issued</b>{new Date(data.issued_at).toLocaleDateString()}</span><span><b>Expires</b>{data.expires_at ? new Date(data.expires_at).toLocaleDateString() : "No expiry"}</span></div></> : <div className="empty-state"><Award size={34}/><h2>Credential not found</h2><p>The verification code is invalid or the credential is no longer available.</p></div>}<Link className="text-link" href="/">← Corporate LMS home</Link></div></section>
    </main>
  );
}
