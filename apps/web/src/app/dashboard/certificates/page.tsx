import { Award, ExternalLink } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJson, requireUser } from "@/lib/server-api";

type Certificate = { id: string; course: string; verification_code: string; issued_at: string; expires_at?: string | null; revoked: boolean };

export default async function CertificatesPage() {
  await requireUser();
  const certificates = await apiJson<Certificate[]>("/api/v1/certificates/my");
  return (
    <DashboardShell title="Credentials" eyebrow="Certificates & verification">
      <div className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Verified learning evidence</span><h2>Certificates</h2></div><span className="section-meta">{certificates?.length ?? 0} issued</span></div>
        {certificates?.length ? <div className="certificate-grid">{certificates.map((item)=><article className="certificate-card" key={item.id}><div className="certificate-symbol"><Award size={24}/></div><div><span className={`status-badge ${item.revoked ? "danger" : "success"}`}>{item.revoked ? "Revoked" : "Valid"}</span><h3>{item.course}</h3><p>Issued {new Date(item.issued_at).toLocaleDateString()}{item.expires_at ? ` · Expires ${new Date(item.expires_at).toLocaleDateString()}` : " · No expiry"}</p><small>Verification: {item.verification_code}</small><a className="text-link" target="_blank" rel="noreferrer" href={`/verify/${item.verification_code}`}>Verification endpoint <ExternalLink size={13}/></a></div></article>)}</div> : <div className="empty-state"><Award size={24}/><p>No certificates have been issued to this learner yet.</p></div>}
      </div>
    </DashboardShell>
  );
}
