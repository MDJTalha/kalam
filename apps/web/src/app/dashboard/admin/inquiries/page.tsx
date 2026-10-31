import Link from "next/link";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJsonResult, requireUser } from "@/lib/server-api";
import { InquiryQueue, type Inquiry } from "./queue";

export default async function InquiriesPage() {
  await requireUser();
  const result = await apiJsonResult<Inquiry[]>("/api/v1/marketing/inquiries");
  if (!result.ok || !result.data) return <DashboardShell title="Demo requests" eyebrow="Kalam operations">
    <div className="data-panel"><div className="empty-state">
      <h2>Review queue unavailable</h2>
      <p>Access is limited to authorized reviewers in the Kalam operations workspace.</p>
      <Link href="/dashboard/admin">Return to administration</Link>
    </div></div>
  </DashboardShell>;
  const inquiries = result.data;
  return <DashboardShell title="Demo requests" eyebrow="Kalam operations">
    <div className="data-panel"><p>Review incoming conversations. Contact requesters using your approved business process, then update their status here.</p>
      <InquiryQueue initial={inquiries} /></div>
  </DashboardShell>;
}
