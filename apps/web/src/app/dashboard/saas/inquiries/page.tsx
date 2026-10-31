import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { apiFetch, requireUser } from "@/lib/server-api";
import { InquiryQueue, type Inquiry } from "@/app/dashboard/admin/inquiries/queue";

export default async function SaaSInquiriesPage() {
  const user=await requireUser<{permissions?:string[]}>();
  const canRead=user.permissions?.includes("saas.sales.read")??false;
  const canManage=user.permissions?.includes("saas.sales.manage")??false;
  if(!canRead)return <DashboardShell title="Leads & Inquiries" eyebrow="SaaS Sales"><div className="data-panel"><h2>Sales access is restricted</h2><p>Your role does not include inquiry review.</p></div></DashboardShell>;
  const response = await apiFetch("/api/v1/marketing/inquiries");
  if (!response.ok) {
    return <DashboardShell title="Leads & Inquiries" eyebrow="SaaS CRM" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Leads & Inquiries"}]}>
      <SaaSCrmNav/>
      <div className="data-panel saas-spaced-section"><div className="empty-state">
        <h2>Inquiry queue unavailable</h2>
        <p>Access is limited to authorized Kalam SaaS operations users.</p>
      </div></div>
    </DashboardShell>;
  }
  const inquiries = (await response.json()) as Inquiry[];
  const newCount = inquiries.filter(item => item.status === "new").length;
  const contactedCount = inquiries.filter(item => item.status === "contacted").length;
  return <DashboardShell title="Leads & Inquiries" eyebrow="SaaS CRM" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Leads & Inquiries"}]}>
    <SaaSCrmNav/>
    <div className="stat-grid saas-spaced-section">
      <div className="stat-card"><span>Total inquiries</span><strong>{inquiries.length}</strong><small>Website and commercial intake</small></div>
      <div className="stat-card"><span>New</span><strong>{newCount}</strong><small>Awaiting review</small></div>
      <div className="stat-card"><span>Contacted / converted</span><strong>{contactedCount}</strong><small>Moved forward in the process</small></div>
      <div className="stat-card"><span>Closed</span><strong>{inquiries.filter(item=>item.status==="closed").length}</strong><small>Completed or disqualified</small></div>
    </div>
    <div className="data-panel">
      <p>Review inbound requests, update their status, and convert qualified organizations into CRM accounts and opportunities without re-entering the requester data.</p>
      <InquiryQueue initial={inquiries} canManage={canManage}/>
    </div>
  </DashboardShell>;
}
