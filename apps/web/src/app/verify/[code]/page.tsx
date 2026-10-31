import Link from "next/link";
import { Award, ShieldCheck } from "lucide-react";
import { apiJsonResult } from "@/lib/server-api";
import { KalamBrand } from "@/components/kalam-brand";

type Verification = { valid: boolean; certificate_id: string; course: string; learner: string; issued_at: string; expires_at?: string | null; revoked: boolean; status: "active" | "expiring_soon" | "expired" | "revoked"; verification_code: string; template: { title: string; subtitle: string; issuer_name: string; primary_color: string; accent_color: string; footer_text: string } };

export default async function VerificationPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const data = await apiJsonResult<Verification>(`/api/v1/certificates/verify/${encodeURIComponent(code)}`).then((result) => result.ok ? result.data : null);
  return (
    <main className="auth-shell">
      <section className="auth-brand"><KalamBrand dark compact className="brand-lockup" /><div className="auth-brand-copy"><span className="eyebrow"><ShieldCheck size={15}/> Credential verification</span><h1>Verify learning evidence.</h1><p>Confirm the current status of this learning credential using the issuer’s verification service.</p></div></section>
      <section className="auth-panel"><div className="auth-card verification-card">{data ? <><div className={`verification-icon ${data.valid ? "valid" : "invalid"}`}><Award size={34}/></div><span className={`status-badge ${data.valid ? "success" : "danger"}`}>{data.valid ? data.status === "expiring_soon" ? "Valid — expiring soon" : "Valid credential" : data.revoked ? "Revoked credential" : "Expired credential"}</span><p className="eyebrow" style={{color:data.template.primary_color}}>{data.template.issuer_name}</p><h2 style={{color:data.template.accent_color}}>{data.template.title}</h2><p>{data.template.subtitle}</p><h3>{data.course}</h3><p className="verification-learner">Awarded to {data.learner}</p><div className="detail-grid"><span><b>Issued</b>{new Date(data.issued_at).toLocaleDateString()}</span><span><b>Expires</b>{data.expires_at ? new Date(data.expires_at).toLocaleDateString() : "No expiry"}</span><span><b>Verification code</b><code>{data.verification_code}</code></span><span><b>Credential ID</b><code>{data.certificate_id}</code></span></div><p className="verification-footer">{data.template.footer_text}</p></> : <div className="empty-state"><Award size={34}/><h2>Credential not found</h2><p>The verification code is invalid or the credential is no longer available.</p></div>}<Link className="text-link" href="/">← Kalam home</Link></div></section>
    </main>
  );
}
