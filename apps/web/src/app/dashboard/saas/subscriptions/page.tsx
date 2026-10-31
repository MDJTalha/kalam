import Link from "next/link";
import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { SubscriptionCreateForm, SubscriptionQuickActions } from "@/components/saas-crm-forms";
import { DataTable, EmptyState, SectionCard, StatusBadge } from "@/components/ui";
import { apiJson, requireUser } from "@/lib/server-api";

type Subscription={id:string;account_id:string;account_name:string;plan_id?:string|null;plan_name?:string|null;status:string;billing_cycle:string;currency:string;seats:number;list_price_minor:number;discount_minor:number;net_price_minor:number;renews_at?:string|null};
type SubscriptionPage={items:Subscription[];total:number;offset:number;limit:number};
function money(minor:number,currency:string){return new Intl.NumberFormat("en-US",{style:"currency",currency,maximumFractionDigits:minor%100===0?0:2}).format(minor/100);}

export default async function SaaSSubscriptionsPage({searchParams}:{searchParams:Promise<{page?:string;status?:string}>}){
  const user=await requireUser<{permissions?:string[]}>();
  const canManage=user.permissions?.includes("saas.finance.manage")??false;
  if(!user.permissions?.includes("saas.finance.read"))return <DashboardShell title="Subscriptions" eyebrow="SaaS Finance"><EmptyState title="Finance access is restricted" description="This role does not include subscription visibility."/></DashboardShell>;
  const params=await searchParams;
  const requestedPage=Number(params.page||1);
  const page=Number.isSafeInteger(requestedPage)&&requestedPage>0?Math.min(requestedPage,100000):1;
  const query=new URLSearchParams({limit:"25",offset:String((page-1)*25)});
  if(params.status)query.set("status",params.status);
  const result=await apiJson<SubscriptionPage>("/api/v1/saas/crm/page/subscriptions?"+query.toString());
  if(!result)return <DashboardShell title="Subscriptions" eyebrow="SaaS CRM"><EmptyState title="Subscription CRM access is restricted" description="This page requires authorized SaaS CRM access."/></DashboardShell>;
  const subscriptions=result.items;
  const pageCount=Math.max(1,Math.ceil(result.total/result.limit));
  const pageHref=(target:number)=>{const q=new URLSearchParams({page:String(target)});if(params.status)q.set("status",params.status);return "/dashboard/saas/subscriptions?"+q.toString();};
  return <DashboardShell title="Subscriptions" eyebrow="SaaS CRM" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Subscriptions"}]}>
    <SaaSCrmNav/>
    <SectionCard eyebrow="Commercial register" title="Subscriptions" meta={result.total+" records"}>
      <form method="get" className="toolbar-row"><label>Status<select name="status" defaultValue={params.status||""}><option value="">All statuses</option><option value="draft">Draft</option><option value="active">Active</option><option value="paused">Paused</option><option value="cancelled">Cancelled</option></select></label><button className="button button-primary" type="submit">Apply filter</button><Link className="button button-secondary" href="/dashboard/saas/subscriptions">Clear</Link></form>
      <DataTable caption="Commercial subscriptions" columns={["Account","Plan","Seats","List","Discount","Net","Status"]} empty={<EmptyState title="No subscriptions yet" description="Create a commercial subscription after plan, scope and pricing are agreed."/>} rows={subscriptions.map(s=>[
        <strong key="a">{s.account_name}</strong>,
        <span key="b">{s.plan_name||"Custom"}</span>,
        <span key="c">{s.seats}</span>,
        <span key="d">{money(s.list_price_minor,s.currency)}</span>,
        <span key="e">{money(s.discount_minor,s.currency)}</span>,
        <span key="f"><strong>{money(s.net_price_minor,s.currency)}</strong><small>{s.billing_cycle}</small></span>,
        <span key="g"><StatusBadge status={s.status}/>{canManage?<SubscriptionQuickActions id={s.id} status={s.status}/>:null}</span>
      ])}/>
      <nav className="toolbar-row saas-spaced-pagination" aria-label="Subscription pages">
        {page>1?<Link className="button button-secondary" href={pageHref(page-1)}>Previous</Link>:null}
        <span>Page {page} of {pageCount} · {result.total} subscriptions</span>
        {page<pageCount?<Link className="button button-secondary" href={pageHref(page+1)}>Next</Link>:null}
      </nav>
    </SectionCard>
    {canManage&&<SectionCard eyebrow="New agreement" title="Create subscription"><SubscriptionCreateForm/></SectionCard>}
  </DashboardShell>;
}
