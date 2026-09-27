import { DashboardShell } from "@/components/dashboard-shell";
import { CertificateAdmin } from "@/components/certificate-admin";
import { Section } from "@/components/ui";
import { apiFetch, requireUser } from "@/lib/server-api";

type Certificate={id:string;learner:string;course:string;verification_code:string;issued_at:string;expires_at:string|null;revoked:boolean;status:"active"|"expiring_soon"|"expired"|"revoked"};
type Template={title:string;subtitle:string;issuer_name:string;primary_color:string;accent_color:string;logo_url:string|null;footer_text:string;version?:number};

const defaultTemplate: Template = { title:"Certificate of Completion", subtitle:"This certifies that", issuer_name:"Kognivon", primary_color:"#0e4c3d", accent_color:"#df9d13", logo_url:null, footer_text:"Verify this credential using the verification code.", version:1 };

export default async function CertificateAdminPage(){
  const user=await requireUser<{permissions?:string[]}>();
  if(!user.permissions?.includes("certificates.manage")) return <DashboardShell title="Certificate administration" eyebrow="Credential governance"><Section eyebrow="Access" title="Restricted workspace"><p>This workspace requires certificate administration permission.</p></Section></DashboardShell>;
  const [certificatesResponse,templateResponse]=await Promise.all([
    apiFetch("/api/v1/certificates/admin"),
    apiFetch("/api/v1/certificates/templates/default"),
  ]);
  if(!certificatesResponse.ok || !templateResponse.ok) return <DashboardShell title="Certificate administration" eyebrow="Credential governance"><Section eyebrow="Service status" title="Certificate administration is temporarily unavailable"><div className="form-error" role="alert">The credential administration service could not load the current tenant data. No changes were made.</div><a className="text-link" href="/dashboard/certificates/admin">Retry administration workspace</a></Section></DashboardShell>;
  const [certificates,template]=await Promise.all([
    certificatesResponse.json() as Promise<Certificate[]>,
    templateResponse.json() as Promise<Template>,
  ]);
  return <DashboardShell title="Certificate administration" eyebrow="Credential governance">
    <CertificateAdmin initialCertificates={certificates ?? []} initialTemplate={template ?? defaultTemplate}/>
  </DashboardShell>;
}
