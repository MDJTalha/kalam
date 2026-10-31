import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { CertificationCreateForm } from "@/components/saas-crm-forms";
import { CertificationsTable, type SaaSCertification } from "@/components/certifications-table";
import { MetricCard, SectionCard } from "@/components/ui";
import { apiJson, requireUser } from "@/lib/server-api";

export default async function SaaSCertificationsPage() {
  const user=await requireUser<{permissions?:string[]}>();
  const canManage=user.permissions?.includes("saas.platform.manage")??false;
  if(!user.permissions?.includes("saas.platform.read"))return <DashboardShell title="Certifications" eyebrow="SaaS platform"><SectionCard eyebrow="Access control" title="Platform certification access is restricted"><p className="muted">This role does not include platform certification visibility.</p></SectionCard></DashboardShell>;
  const certifications = await apiJson<SaaSCertification[]>("/api/v1/saas/crm/certifications");
  if (!certifications) return <DashboardShell title="Certifications" eyebrow="SaaS CRM"><SectionCard eyebrow="Access control" title="Certification CRM access is restricted"><p className="muted">This page requires authorized SaaS CRM access.</p></SectionCard></DashboardShell>;

  // Request-scoped server rendering requires a current timestamp for the 90-day window.
  // eslint-disable-next-line react-hooks/purity
  const now = Date.now();
  const activeCount = certifications.filter((item) => item.status === "active").length;
  const publicCount = certifications.filter((item) => item.public_visible).length;
  const expiringSoon = certifications.filter((item) => item.expires_at && new Date(item.expires_at).getTime() >= now && new Date(item.expires_at).getTime() <= now + 90 * 86400000).length;

  return <DashboardShell title="Certifications" eyebrow="SaaS CRM" breadcrumbs={[{ label: "SaaS Operations", href: "/dashboard/saas" }, { label: "Certifications" }]}>
    <SaaSCrmNav />
    <section className="certification-summary" aria-label="Certification summary">
      <MetricCard label="Total records" value={certifications.length} detail="Evidence register" icon="shield" />
      <MetricCard label="Active" value={activeCount} detail="Currently valid" icon="check" />
      <MetricCard label="Expiring soon" value={expiringSoon} detail="Within 90 days" icon="calendar" />
      <MetricCard label="Public" value={publicCount} detail="Published externally" icon="webhook" />
    </section>
    <div className="certifications-layout">
      <SectionCard eyebrow="Evidence register" title="Corporate certifications" meta={certifications.length + " records"}>
        <CertificationsTable certifications={certifications} />
      </SectionCard>
      {canManage&&<SectionCard eyebrow="New evidence" title="Register certification" meta="Authoritative record">
        <p className="certification-form-intro">Capture the issuer, registration reference and validity dates exactly as they appear on the source certificate.</p>
        <CertificationCreateForm />
      </SectionCard>}
    </div>
  </DashboardShell>;
}