import { DashboardShell } from "@/components/dashboard-shell";
import { SessionManagement } from "@/components/session-management";
import { requireUser } from "@/lib/server-api";

export default async function SessionsPage() {
  await requireUser();
  return (
    <DashboardShell title="Session security" eyebrow="Account security" breadcrumbs={[{ label: "Settings", href: "/dashboard/settings" }, { label: "Session security" }]}>
      <SessionManagement />
    </DashboardShell>
  );
}
