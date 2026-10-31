import Link from "next/link";
import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { AccountCreateForm, AccountQuickActions, ProvisionTenantButton } from "@/components/saas-crm-forms";
import { DataTable, EmptyState, SectionCard, StatusBadge } from "@/components/ui";
import { apiJson } from "@/lib/server-api";

type Account={id:string;name:string;slug:string;account_type:string;lifecycle_stage:string;industry?:string|null;country?:string|null;employee_band?:string|null;public_showcase:boolean;plan_id?:string|null;managed_tenant_id?:string|null};
type Plan={id:string;name:string};
type AccountPage={items:Account[];total:number;offset:number;limit:number};

export default async function SaaSClientsPage({searchParams}:{searchParams:Promise<{q?:string;stage?:string;page?:string}>}){
  const params=await searchParams;
  const query=new URLSearchParams();
  if(params.q?.trim())query.set("q",params.q.trim());
  if(params.stage?.trim())query.set("stage",params.stage.trim());
  const requestedPage=Number(params.page||1);
  const page=Number.isSafeInteger(requestedPage)&&requestedPage>0?Math.min(requestedPage,100000):1;
  const listQuery=new URLSearchParams(query);
  listQuery.set("limit","25");
  listQuery.set("offset",String((page-1)*25));
  const accountPath="/api/v1/saas/crm/page/accounts?"+listQuery.toString();
  const [result,plans]=await Promise.all([
    apiJsonResult<AccountPage>(accountPath).then((result) => result.ok ? result.data : null),
    apiJsonResult<Plan[]>("/api/v1/saas/crm/plans").then((result) => result.ok ? result.data : null),
  ]);
  if(!result||!plans)return <DashboardShell title="Clients" eyebrow="SaaS CRM"><EmptyState title="Client CRM access is restricted" description="This page requires authorized SaaS CRM access."/></DashboardShell>;
  const accounts=result.items;
  const pageCount=Math.max(1,Math.ceil(result.total/result.limit));
  const pageHref=(target:number)=>{const search=new URLSearchParams(query);search.set("page",String(target));return "/dashboard/saas/clients?"+search.toString();};
  const exportQuery=query.size?"?"+query.toString():"";
  return <DashboardShell title="Clients" eyebrow="SaaS CRM" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Clients"}]}>
    <SaaSCrmNav/>
    <SectionCard eyebrow="Find accounts" title="Search & filter" meta={result.total+" matching records"}>
      <form method="get" className="toolbar-row">
        <label>Search<input name="q" defaultValue={params.q||""} placeholder="Account, industry, country…"/></label>
        <label>Lifecycle<select name="stage" defaultValue={params.stage||""}><option value="">All stages</option><option value="lead">Lead</option><option value="qualified">Qualified</option><option value="trial">Trial</option><option value="customer">Customer</option><option value="churned">Churned</option></select></label>
        <button className="button button-primary" type="submit">Apply filters</button>
        <Link className="button button-secondary" href="/dashboard/saas/clients">Clear</Link>
        <a className="button button-secondary" href={"/api/lms/saas/crm/export/accounts.csv"+exportQuery}>Export CSV</a>
      </form>
    </SectionCard>
    <div className="two-column">
      <SectionCard eyebrow="Client registry" title="Accounts" meta={result.total+" records"}>
        <DataTable caption="CRM accounts" columns={["Account","Lifecycle","Market","Public","Tenant","Actions"]} empty={<EmptyState title="No CRM accounts match these filters" description="Change the search or add a new prospect/client record."/>} rows={accounts.map(a=>[
          <span key="a"><strong><Link className="text-link" href={"/dashboard/saas/clients/"+a.id}>{a.name}</Link></strong><small>{a.slug} · {a.account_type}</small></span>,
          <StatusBadge key="b" status={a.lifecycle_stage}/>,
          <span key="c">{[a.industry,a.country,a.employee_band].filter(Boolean).join(" · ")||"—"}</span>,
          <StatusBadge key="d" status={a.public_showcase?"published":"private"}/>,
          <ProvisionTenantButton key="e" accountId={a.id} disabled={!!a.managed_tenant_id}/>,
          <AccountQuickActions key="f" id={a.id} lifecycleStage={a.lifecycle_stage} publicShowcase={a.public_showcase}/>
        ])}/>
        <nav className="toolbar-row saas-spaced-pagination" aria-label="Account pages">
          {page>1?<Link className="button button-secondary" href={pageHref(page-1)}>Previous</Link>:null}
          <span>Page {page} of {pageCount} · {result.total} accounts</span>
          {page<pageCount?<Link className="button button-secondary" href={pageHref(page+1)}>Next</Link>:null}
        </nav>
      </SectionCard>
      <SectionCard eyebrow="New account" title="Add prospect, client or partner"><AccountCreateForm plans={plans}/></SectionCard>
    </div>
  </DashboardShell>;
}
