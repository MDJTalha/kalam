import { DashboardShell } from "@/components/dashboard-shell";
import { ApiActionButton } from "@/components/api-action-button";
import { EmptyState, Section, StatusBadge } from "@/components/ui";
import { apiJson, requireUser } from "@/lib/server-api";

type Notification={id:string;type:string;title:string;body:string;read_at?:string|null;created_at:string};

export default async function NotificationsPage(){
  await requireUser();
  const rows=await apiJson<Notification[]>("/api/v1/notifications");
  return <DashboardShell title="Notifications" eyebrow="Learning inbox">
    <Section eyebrow="Inbox" title="Recent notifications">
      {rows?.length?<div className="compact-list">{rows.map(x=><div className="compact-row" key={x.id}>
        <div><strong>{x.title}</strong><small>{x.body+" · "+new Date(x.created_at).toLocaleString()}</small></div>
        <div className="button-row"><StatusBadge status={x.read_at?"read":"unread"} tone={x.read_at?"muted":"warning"}/>{!x.read_at?<ApiActionButton endpoint={"/api/lms/notifications/"+x.id+"/read"} label="Mark read"/>:null}</div>
      </div>)}</div>:<EmptyState title="Inbox clear" description="Learning and compliance notifications will appear here."/>}
    </Section>
  </DashboardShell>;
}
