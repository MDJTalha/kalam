import { DashboardShell } from "@/components/dashboard-shell";
import { EmptyState, Section, StatusBadge } from "@/components/ui";
import { apiJsonResult, requireUser } from "@/lib/server-api";
import { Activity, ArrowRight, CalendarDays, CheckCircle2, Cloud, Mail, Network, RefreshCw, ShieldCheck, Webhook, UsersRound } from "lucide-react";
import { IntegrationConsole } from "@/components/integration-console";

type Integration={id:string;provider:string;status:string;config:Record<string,unknown>;last_checked_at?:string|null;last_check_status?:string|null;last_check_message?:string|null};
const providers=["hris","oidc","saml","email","calendar","lti","xapi","scorm","cmi5"];
const providerMeta:Record<string,{name:string;purpose:string;icon:typeof Network}> = {
  hris:{name:"HRIS",purpose:"Workforce & people data",icon:UsersRound},
  oidc:{name:"OpenID Connect",purpose:"Enterprise SSO",icon:ShieldCheck},
  saml:{name:"SAML 2.0",purpose:"Federated identity",icon:ShieldCheck},
  email:{name:"Email",purpose:"Transactional delivery",icon:Mail},
  calendar:{name:"Calendar",purpose:"Learning & event scheduling",icon:CalendarDays},
  lti:{name:"LTI",purpose:"Learning tool interoperability",icon:Network},
  xapi:{name:"xAPI",purpose:"Learning event telemetry",icon:Activity},
  scorm:{name:"SCORM",purpose:"Course interoperability",icon:Cloud},
  cmi5:{name:"cmi5",purpose:"Modern LMS interoperability",icon:Cloud},
};

export default async function IntegrationsPage(){
  const user=await requireUser<{permissions?:string[]}>();
  const rowsResult=await apiJsonResult<Integration[]>("/api/v1/integrations");
  const canManage=user.permissions?.includes("integrations.manage")??false;
  if (!rowsResult.ok || rowsResult.data === null) return <DashboardShell title="Integrations" eyebrow="Enterprise connectivity"><section className="data-panel" role="alert"><h2>{rowsResult.status===403?"Integration access is restricted":"Integration registry unavailable"}</h2><p>{rowsResult.status===403?"Your role does not have permission to view integration records.":rowsResult.status===0?"The API service could not be reached. Check that it is running and try again.":`The integration registry could not be loaded (HTTP ${rowsResult.status}). Refresh or try again later.`}</p></section></DashboardShell>;
  const rows=rowsResult.data;
  const connected=rows.filter(x=>x.status==="connected").length;
  const healthy=rows.filter(x=>x.last_check_status==="passed").length;
  const attention=rows.filter(x=>x.last_check_status==="failed"||x.status==="disabled").length;
  return <DashboardShell title="Integrations" eyebrow="Enterprise connectivity">    <div className="kalam-integration-hero">
      <div className="kalam-integration-hero-copy">
        <span className="kalam-integration-eyebrow"><Network size={13}/> INTEGRATION CONTROL CENTER</span>
        <h2>Connect the enterprise.<br/><span>Govern every data boundary.</span></h2>
        <p>One controlled workspace for identity, workforce data, learning interoperability and event delivery.</p>
      </div>
      <div className="kalam-integration-hero-side">
        <div className="kalam-live-status"><i/> Registry response received</div>
        <div className="kalam-hero-rule"/>
        <small>Connection evidence is sourced from the integration registry.</small>
        <span className="kalam-registry-badge"><RefreshCw size={13}/> Snapshot loaded for this request</span>
      </div>
    </div>
    <div className="kalam-integration-metrics">
      <article><CheckCircle2 size={16}/><span>Connected</span><strong>{connected}</strong><small>Providers with connected status</small></article>
      <article><ShieldCheck size={16}/><span>Healthy</span><strong>{healthy}</strong><small>Passed checks</small></article>
      <article><Activity size={16}/><span>Attention</span><strong>{attention}</strong><small>Requires review</small></article>
      <article><Webhook size={16}/><span>Event layer</span><strong>Separate</strong><small>Managed in Webhooks</small></article>
    </div>
    <Section eyebrow="Connection landscape" title="Enterprise integration fabric">
      <div className="kalam-provider-grid">
        {providers.map(name=>{const item=rows.find(x=>x.provider===name);const meta=providerMeta[name];const Icon=meta.icon;return <article className={"kalam-provider-card "+(item?.status==="connected"?"is-connected":"")} key={name}>
          <div className="kalam-provider-top"><span className="kalam-provider-icon"><Icon size={17}/></span><StatusBadge status={item?.status||"not configured"}/></div>
          <h3>{meta.name}</h3><p>{meta.purpose}</p>
          <div className="kalam-provider-evidence"><span>{item?.last_checked_at?"Last checked":"Status"}</span><strong>{item?.last_checked_at?new Date(item.last_checked_at).toLocaleString():"Not tested"}</strong></div>
          <div className="kalam-provider-action"><span>{item?.last_check_status==="passed"?"Connection verified":item?.last_check_status==="failed"?"Check failed":"Awaiting verification"}</span><ArrowRight size={14}/></div>
        </article>})}
      </div>
    </Section>    <Section eyebrow="Identity & access" title="SSO readiness">
      <div className="kalam-identity-grid">
        <div><div className="kalam-panel-icon"><ShieldCheck size={17}/></div><div><strong>OpenID Connect</strong><p>Active SSO path for enterprise identity. Use deployment-managed secret references rather than storing credentials in the application.</p></div><span className="kalam-readiness">ACTIVE PATH</span></div>
        <div><div className="kalam-panel-icon"><ShieldCheck size={17}/></div><div><strong>SAML 2.0</strong><p>Metadata can be configured and tested. Interactive sign-in remains unavailable until the signed assertion flow is implemented and validated.</p></div><span className="kalam-readiness muted">READINESS</span></div>
      </div>
    </Section>    {canManage?<Section eyebrow="Administration" title="Configure a connection"><IntegrationConsole initialRows={rows}/></Section>:null}
    <Section eyebrow="Operational evidence" title="Registry activity">
      {rows?.length?<div className="table-wrap" tabIndex={0} aria-label="Integration registry evidence table"><table className="data-table kalam-integration-table"><thead><tr><th>Provider</th><th>State</th><th>Last check</th><th>Result</th></tr></thead><tbody>{rows.map(x=><tr key={x.id}><td><strong>{providerMeta[x.provider]?.name||x.provider.toUpperCase()}</strong><small>{providerMeta[x.provider]?.purpose||"Integration provider"}</small></td><td><StatusBadge status={x.status}/></td><td>{x.last_checked_at?new Date(x.last_checked_at).toLocaleString():"Not tested"}</td><td>{x.last_check_status?<StatusBadge status={x.last_check_status}/>:null}<small>{x.last_check_message||"No diagnostic message recorded."}</small></td></tr>)}</tbody></table></div>:<EmptyState title="No integrations configured" description="Connect identity, workforce, learning or event services to establish the enterprise integration fabric."/>}
    </Section>
  </DashboardShell>;
}
