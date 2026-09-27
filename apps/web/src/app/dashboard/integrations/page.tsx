import { DashboardShell } from "@/components/dashboard-shell";
import { ResourceForm } from "@/components/resource-form";
import { EmptyState, Section, StatusBadge } from "@/components/ui";
import { apiJson, requireUser } from "@/lib/server-api";

type Integration={id:string;provider:string;status:string;config:Record<string,unknown>;last_checked_at?:string|null;last_check_status?:string|null;last_check_message?:string|null};
const providers=["hris","oidc","saml","email","calendar","lti","xapi","scorm","cmi5"];

export default async function IntegrationsPage(){
  const user=await requireUser<{permissions?:string[]}>();
  const rows=await apiJson<Integration[]>("/api/v1/integrations");
  const canManage=user.permissions?.includes("integrations.manage")??false;
  return <DashboardShell title="Integrations" eyebrow="Enterprise interoperability">
    {canManage?<Section eyebrow="Connection registry" title="Configure integration"><ResourceForm
      title="Save and test provider"
      endpoint="/api/lms/integrations/:provider"
      method="PUT"
      testEndpoint="/api/lms/integrations/:provider/test"
      jsonFields={["config"]}
      fields={[
        {name:"provider",label:"Provider",type:"select",required:true,options:providers.map(x=>({value:x,label:x.toUpperCase()}))},
        {name:"status",label:"Status",type:"select",required:true,defaultValue:"configured",options:[{value:"configured",label:"Configured"},{value:"disabled",label:"Disabled"}]},
        {name:"config",label:"Provider configuration (JSON; secrets must be environment references)",type:"textarea",required:true,defaultValue:"{}"},
      ]}
    /></Section>:null}
    <Section eyebrow="Connection evidence" title="Configured integrations">{rows?.length?<div className="table-wrap"><table className="data-table">
      <thead><tr><th>Provider</th><th>Status</th><th>Last check</th><th>Result</th></tr></thead>
      <tbody>{rows.map(x=><tr key={x.id}><td><strong>{x.provider.toUpperCase()}</strong></td><td><StatusBadge status={x.status}/></td><td>{x.last_checked_at?new Date(x.last_checked_at).toLocaleString():"Not tested"}</td><td>{x.last_check_status?<StatusBadge status={x.last_check_status}/>:null} <small>{x.last_check_message||""}</small></td></tr>)}</tbody>
    </table></div>:<EmptyState title="No integrations configured" description="Configure HRIS, identity, learning interoperability, email or calendar providers."/>}</Section>
  </DashboardShell>;
}
