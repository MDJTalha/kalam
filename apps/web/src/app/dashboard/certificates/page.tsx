import { Award, ExternalLink } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type CertificateStatus = "active" | "expiring_soon" | "expired" | "revoked";
type Certificate = { id: string; course: string; verification_code: string; issued_at: string; expires_at?: string | null; revoked: boolean; status: CertificateStatus };

const statusLabel: Record<CertificateStatus, string> = {
  active: "Valid",
  expiring_soon: "Expiring soon",
  expired: "Expired",
  revoked: "Revoked",
};

const statusClass: Record<CertificateStatus, string> = {
  active: "success",
  expiring_soon: "warning",
  expired: "danger",
  revoked: "danger",
};

export default async function CertificatesPage() {
  await requireUser();
  const result = await apiJsonResult<Certificate[]>("/api/v1/certificates/my");
  if (!result.ok) {
    const restricted = result.status === 403;
    const serviceFailure = result.status >= 500;
    return <DashboardShell title="Credentials" eyebrow="Certificates & verification"><section className="data-panel" role="alert"><h2>{restricted ? "Credential access restricted" : serviceFailure ? "Credential service unavailable" : "Credentials could not be loaded"}</h2><p>{restricted ? "Your role does not have access to these credential records." : serviceFailure ? "The credential service did not respond successfully. No empty credential list is being shown." : result.error || "Certificate records could not be loaded. Try again."}</p></section></DashboardShell>;
  }
  const certificates = result.data ?? [];
  const counts = {
    issued: certificates.length,
    active: certificates.filter((item) => item.status === "active").length,
    expiring: certificates.filter((item) => item.status === "expiring_soon").length,
    revoked: certificates.filter((item) => item.status === "revoked").length,
  };
  return (
    <DashboardShell title="Credentials" eyebrow="Certificates & verification">
      <section className="certificate-command-hero"><div><span className="eyebrow">Verified learning evidence</span><h2>Your credentials, ready to verify</h2><p>Review certificates issued to you, monitor expiry dates and share a trusted public verification page when you need to evidence your learning.</p></div></section>
      <section className="metric-strip certificate-stat-grid" aria-label="Credential summary"><span><b>{counts.issued}</b> issued</span><span><b>{counts.active}</b> valid</span><span><b>{counts.expiring}</b> expiring soon</span><span><b>{counts.revoked}</b> revoked</span></section>
      <div className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Credential records</span><h2>Certificates</h2></div><span className="section-meta">{counts.issued} issued</span></div>
        {certificates.length ? <div className="certificate-grid">{certificates.map((item)=><article className="certificate-card certificate-card-enhanced" key={item.id}><div className="certificate-symbol"><Award size={24}/></div><div className="certificate-card-body"><span className={`status-badge ${statusClass[item.status]}`}>{statusLabel[item.status]}</span><h3>{item.course}</h3><p>Issued {new Date(item.issued_at).toLocaleDateString()}{item.expires_at ? ` · Expires ${new Date(item.expires_at).toLocaleDateString()}` : " · No expiry"}</p><div className="certificate-code"><span>Verification code</span><code>{item.verification_code}</code></div><a className="text-link certificate-verify-action" target="_blank" rel="noreferrer" href={`/verify/${item.verification_code}`}>Verify credential <ExternalLink size={13}/></a></div></article>)}</div> : <div className="empty-state"><Award size={24}/><h3>No certificates issued yet</h3><p>Certificates will appear here after you complete certificate-eligible learning.</p></div>}
      </div>
    </DashboardShell>
  );
}
