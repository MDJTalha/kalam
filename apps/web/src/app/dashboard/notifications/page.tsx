import { DashboardShell } from "@/components/dashboard-shell";
import { NotificationCenter, type NotificationItem } from "@/components/notification-center";
import { apiJson, requireUser } from "@/lib/server-api";

export default async function NotificationsPage(){
  const user=await requireUser<{preferences?:{timezone?:string}}>();
  const rows=await apiJson<NotificationItem[]>("/api/v1/notifications");
  const content=rows===null ? <section className="data-panel" role="alert"><h2>Notifications unavailable</h2><p>Workspace alerts could not be loaded. Refresh and try again.</p></section> : <NotificationCenter initialItems={rows} timezone={user.preferences?.timezone||"UTC"}/>;
  return <DashboardShell title="Notifications" eyebrow="Workspace alerts & activity">{content}</DashboardShell>;
}
