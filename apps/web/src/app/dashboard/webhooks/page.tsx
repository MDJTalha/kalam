import { Webhook } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { ResourceForm } from "@/components/resource-form";
import { EmptyState, Section, StatusBadge } from "@/components/ui";
import { apiJson, requireUser } from "@/lib/server-api";

type Hook={id:string;url:string;event_types:string[];active:boolean;created_at:string};

export default async function WebhooksPage(){
  const user=await requireUser<{permissions?:string[]}>();
  if(!user.permissions?.includes("integrations.manage")){
    return <DashboardShell title="Webhooks" eyebrow="Event delivery" breadcrumbs={[{label:"Integrations",href:"/dashboard/integrations"},{label:"Webhooks"}]}>
      <EmptyState title="Access restricted" description="Webhook administration requires integration management permission." icon={Webhook}/>
    </DashboardShell>;
  }
  const hooks=await apiJson<Hook[]>("/api/v1/webhooks");
  return <DashboardShell title="Webhooks" eyebrow="Event delivery" breadcrumbs={[{label:"Integrations",href:"/dashboard/integrations"},{label:"Webhooks"}]}>
    <div className="two-column">
      <Section eyebrow="Endpoint" title="Create webhook">
        <ResourceForm title="Add event destination" endpoint="/api/lms/webhooks" fields={[
          {name:"url",label:"HTTPS endpoint",required:true,placeholder:"https://example.com/lms-events"},
          {name:"event_types",label:"Event types — comma separated",required:true,placeholder:"course.completed, certificate.issued"},
        ]} transformProfile="webhook_events"/>
      </Section>
      <div className="callout"><Webhook size={16}/><strong>Secure event delivery</strong><p>A signing secret is generated once when the endpoint is created. Store it securely; it is not recoverable later.</p></div>
    </div>
    <Section eyebrow="Event endpoints" title="Configured webhooks">
      {hooks?.length?<div className="compact-list">{hooks.map(item=><div className="compact-row" key={item.id}>
        <div><strong>{item.url}</strong><small>{item.event_types.join(" · ")} · {new Date(item.created_at).toLocaleDateString()}</small></div>
        <StatusBadge status={item.active?"active":"disabled"}/>
      </div>)}</div>:<EmptyState title="No webhooks" description="Create a webhook for downstream HRIS, analytics or workflow automation." icon="webhook"/>}
    </Section>
  </DashboardShell>;
}
