import Link from "next/link";
import { FileSignature } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { ContractCreateForm, ContractStatusControl } from "@/components/saas-crm-forms";
import { DataTable, EmptyState, MetricCard, SectionCard, StatusBadge } from "@/components/ui";
import { apiJsonResult } from "@/lib/server-api";

type Contract={id:string;account_id:string;account_name:string;subscription_id?:string|null;reference:string;status:string;currency:string;total_value_minor:number;starts_at?:string|null;ends_at?:string|null;signed_at?:string|null;renewal_terms?:string|null;notes?:string|null};
type ContractPage={items:Contract[];total:number;offset:number;limit:number;counts:{signed_active:number;expiring_90_days:number;draft_review:number}};
function money(minor:number,currency:string){return new Intl.NumberFormat("en-US",{style:"currency",currency,maximumFractionDigits:minor%100===0?0:2}).format(minor/100);}

export default async function SaaSContractsPage({searchParams}:{searchParams:Promise<{page?:string;status?:string}>}){
  const params=await searchParams;
  const requestedPage=Number(params.page||1);
  const page=Number.isSafeInteger(requestedPage)&&requestedPage>0?Math.min(requestedPage,100000):1;
  const query=new URLSearchParams({limit:"25",offset:String((page-1)*25)});
  if(params.status)query.set("status",params.status);
  const result=await apiJsonResult<ContractPage>("/api/v1/saas/crm/page/contracts?"+query.toString()).then((result) => result.ok ? result.data : null);
  if(!result)return <DashboardShell title="Contracts" eyebrow="SaaS CRM"><EmptyState title="Contract CRM access is restricted" description="This page requires authorized SaaS CRM access."/></DashboardShell>;

  const contracts=result.items;
  const pageCount=Math.max(1,Math.ceil(result.total/result.limit));
  const pageHref=(target:number)=>{const q=new URLSearchParams({page:String(target)});if(params.status)q.set("status",params.status);return "/dashboard/saas/contracts?"+q.toString();};

  return <DashboardShell title="Contracts" eyebrow="SaaS CRM" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Contracts"}]}>
    <SaaSCrmNav/>
    <div className="stat-grid saas-spaced-section">
      <MetricCard label="Contracts" value={result.total} detail="All commercial agreements" icon={FileSignature}/>
      <MetricCard label="Signed / active" value={result.counts.signed_active} detail="Current signed agreements" icon={FileSignature}/>
      <MetricCard label="Ending within 90 days" value={result.counts.expiring_90_days} detail="Review before renewal" icon={FileSignature}/>
      <MetricCard label="Draft / review" value={result.counts.draft_review} detail="Not yet active" icon={FileSignature}/>
    </div>
    <SectionCard eyebrow="Agreement register" title="Contracts" meta={result.total+" records"}>
      <form method="get" className="toolbar-row"><label>Status<select name="status" defaultValue={params.status||""}><option value="">All statuses</option><option value="draft">Draft</option><option value="review">Review</option><option value="signed">Signed</option><option value="active">Active</option><option value="expired">Expired</option><option value="terminated">Terminated</option></select></label><button className="button button-primary" type="submit">Apply filter</button><Link className="button button-secondary" href="/dashboard/saas/contracts">Clear</Link></form>
      <DataTable caption="Commercial contracts" columns={["Account","Reference","Value","Term","Signed","Status","Update"]} empty={<EmptyState title="No contracts yet" description="Create the first commercial agreement when scope and terms are ready."/>} rows={contracts.map(c=>[
        <Link key="a" className="text-link" href={"/dashboard/saas/clients/"+c.account_id}>{c.account_name}</Link>,
        <strong key="b">{c.reference}</strong>,
        <span key="c">{money(c.total_value_minor,c.currency)}</span>,
        <span key="d">{c.starts_at?new Date(c.starts_at).toLocaleDateString():"—"} → {c.ends_at?new Date(c.ends_at).toLocaleDateString():"—"}</span>,
        <span key="e">{c.signed_at?new Date(c.signed_at).toLocaleDateString():"—"}</span>,
        <StatusBadge key="f" status={c.status}/>,
        <ContractStatusControl key="g" id={c.id} status={c.status}/>
      ])}/>
      <nav className="toolbar-row saas-spaced-pagination" aria-label="Contract pages">
        {page>1?<Link className="button button-secondary" href={pageHref(page-1)}>Previous</Link>:null}
        <span>Page {page} of {pageCount} · {result.total} contracts</span>
        {page<pageCount?<Link className="button button-secondary" href={pageHref(page+1)}>Next</Link>:null}
      </nav>
    </SectionCard>
    <SectionCard eyebrow="New agreement" title="Create contract"><ContractCreateForm/></SectionCard>
  </DashboardShell>;
}
