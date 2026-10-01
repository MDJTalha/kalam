import { DashboardShell } from "@/components/dashboard-shell";
import { SessionManagement } from "@/components/session-management";
import { requireUser } from "@/lib/server-api";

export default async function SessionsPage() {
  const user = await requireUser<{preferences?:{timezone?:string}}>();
  return (
    <DashboardShell title="Active sessions" eyebrow="Account security" breadcrumbs={[{ label: "Settings", href: "/dashboard/settings" }, { label: "Active sessions" }]}>
      <SessionManagement timezone={user.preferences?.timezone || "UTC"} />
    </DashboardShell>
  );
}
