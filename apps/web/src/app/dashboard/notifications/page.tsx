import { DashboardShell } from "@/components/dashboard-shell";
import { NotificationCenter, type NotificationItem } from "@/components/notification-center";
import { apiJsonResult, requireUser } from "@/lib/server-api";

export default async function NotificationsPage(){
  const user=await requireUser<{preferences?:{timezone?:string}}>();
  const result=await apiJsonResult<NotificationItem[]>("/api/v1/notifications");
  if(!result.ok||result.data===null)return <DashboardShell title="Notifications" eyebrow="Workspace alerts & activity"><section className="data-panel" role="alert"><h2>{result.status===403?"Notification access restricted":"Notifications unavailable"}</h2><p>{result.status===403?"Your role does not have permission to view this notification feed.":result.status===0?"The API service could not be reached. Refresh when it is available.":`Workspace alerts could not be loaded (HTTP ${result.status}). Refresh and try again.`}</p></section></DashboardShell>;
  return <DashboardShell title="Notifications" eyebrow="Workspace alerts & activity"><NotificationCenter initialItems={result.data} timezone={user.preferences?.timezone||"UTC"}/></DashboardShell>;
}
