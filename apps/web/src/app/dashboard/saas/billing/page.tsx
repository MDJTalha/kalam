import Link from "next/link";
import { CircleDollarSign, ReceiptText, WalletCards } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { InvoiceCreateForm, InvoiceStatusControl, PaymentCreateForm, PaymentStatusControl } from "@/components/saas-crm-forms";
import { DataTable, EmptyState, MetricCard, SectionCard, StatusBadge } from "@/components/ui";
import { apiJson, requireUser } from "@/lib/server-api";

type Invoice={id:string;account_id:string;account_name:string;subscription_id?:string|null;contract_id?:string|null;invoice_number:string;status:string;currency:string;amount_minor:number;tax_minor:number;total_minor:number;paid_minor:number;outstanding_minor:number;issued_at?:string|null;due_at?:string|null;paid_at?:string|null;external_ref?:string|null;notes?:string|null};
type Payment={id:string;account_id:string;account_name:string;invoice_id:string;invoice_number:string;amount_minor:number;currency:string;status:string;received_at:string;method?:string|null;reference?:string|null};
type InvoicePage={items:Invoice[];total:number;offset:number;limit:number};
type PaymentPage={items:Payment[];total:number;offset:number;limit:number};
type FinanceOverview={invoice_counts:{total:number;open:number;overdue:number;paid:number};payment_count:number};

function money(minor:number,currency:string){
  return new Intl.NumberFormat("en-US",{style:"currency",currency,maximumFractionDigits:minor%100===0?0:2}).format(minor/100);
}

function billingHref(values:{invoicePage?:number;paymentPage?:number;invoiceStatus?:string;paymentStatus?:string}){
  const q=new URLSearchParams();
  if(values.invoicePage)q.set("invoice_page",String(values.invoicePage));
  if(values.paymentPage)q.set("payment_page",String(values.paymentPage));
  if(values.invoiceStatus)q.set("invoice_status",values.invoiceStatus);
  if(values.paymentStatus)q.set("payment_status",values.paymentStatus);
  return "/dashboard/saas/billing"+(q.toString()?"?"+q.toString():"");
}
export default async function SaaSBillingPage({searchParams}:{searchParams:Promise<{invoice_page?:string;payment_page?:string;invoice_status?:string;payment_status?:string}>}){
  const user=await requireUser<{permissions?:string[]}>();
  const canManage=user.permissions?.includes("saas.finance.manage")??false;
  if(!user.permissions?.includes("saas.finance.read"))return <DashboardShell title="Billing" eyebrow="SaaS Finance"><EmptyState title="Finance access is restricted" description="This role is not authorized to view invoices or payments."/></DashboardShell>;
  const params=await searchParams;
  const invoicePageNumber=Math.max(1,Math.min(100000,Number(params.invoice_page||1)||1));
  const paymentPageNumber=Math.max(1,Math.min(100000,Number(params.payment_page||1)||1));
  const invoiceQuery=new URLSearchParams({limit:"25",offset:String((invoicePageNumber-1)*25)});
  const paymentQuery=new URLSearchParams({limit:"25",offset:String((paymentPageNumber-1)*25)});
  if(params.invoice_status)invoiceQuery.set("status",params.invoice_status);
  if(params.payment_status)paymentQuery.set("status",params.payment_status);

  const [invoices,payments,finance]=await Promise.all([
    apiJson<InvoicePage>("/api/v1/saas/crm/page/invoices?"+invoiceQuery.toString()),
    apiJson<PaymentPage>("/api/v1/saas/crm/page/payments?"+paymentQuery.toString()),
    apiJson<FinanceOverview>("/api/v1/saas/crm/finance/overview"),
  ]);

  if(!invoices||!payments||!finance){
    return <DashboardShell title="Billing" eyebrow="SaaS CRM"><EmptyState title="Billing CRM data unavailable" description="One or more billing sources could not be loaded. Refresh and try again; unavailable data is not shown as zero."/></DashboardShell>;
  }
  const invoicePages=Math.max(1,Math.ceil(invoices.total/invoices.limit));
  const paymentPages=Math.max(1,Math.ceil(payments.total/payments.limit));

  return <DashboardShell title="Billing" eyebrow="SaaS CRM" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Billing"}]}>
    <SaaSCrmNav/>
    <div className="stat-grid saas-spaced-section">
      <MetricCard label="Open invoices" value={finance.invoice_counts.open} detail="Issued / partial / overdue" icon={ReceiptText}/>
      <MetricCard label="Overdue" value={finance.invoice_counts.overdue} detail="Past due balance requires attention" icon={WalletCards}/>
      <MetricCard label="Paid invoices" value={finance.invoice_counts.paid} detail="Fully reconciled" icon={CircleDollarSign}/>
      <MetricCard label="Payments recorded" value={finance.payment_count} detail="Received payment records" icon={CircleDollarSign}/>
    </div>
    <SectionCard eyebrow="Accounts receivable" title="Invoices" meta={invoices.total+" invoices"}>
      <form method="get" className="toolbar-row">
        <label>Status<select name="invoice_status" defaultValue={params.invoice_status||""}><option value="">All statuses</option><option value="draft">Draft</option><option value="issued">Issued</option><option value="partially_paid">Partially paid</option><option value="overdue">Overdue</option><option value="paid">Paid</option><option value="void">Void</option></select></label>
        <input type="hidden" name="payment_page" value={String(paymentPageNumber)}/>
        {params.payment_status&&<input type="hidden" name="payment_status" value={params.payment_status}/>}
        <button className="button button-primary" type="submit">Apply</button>
        <Link className="button button-secondary" href="/dashboard/saas/billing">Clear</Link>
      </form>
      <DataTable columns={["Invoice","Account","Total","Paid","Outstanding","Due","Status","Update"]} empty={<EmptyState title="No invoices on this page" description="Create an invoice or adjust the invoice filter."/>} rows={invoices.items.map(i=>[
        <strong key="a">{i.invoice_number}</strong>,
        <Link key="b" className="text-link" href={"/dashboard/saas/clients/"+i.account_id}>{i.account_name}</Link>,
        <span key="c">{money(i.total_minor,i.currency)}</span>,
        <span key="d">{money(i.paid_minor,i.currency)}</span>,
        <strong key="e">{money(i.outstanding_minor,i.currency)}</strong>,
        <span key="f">{i.due_at?new Date(i.due_at).toLocaleDateString():"—"}</span>,
        <StatusBadge key="g" status={i.status}/>,
        canManage?<InvoiceStatusControl key="h" id={i.id} status={i.status}/>:<span key="h">Read only</span>
      ])}/>
      <nav className="toolbar-row saas-spaced-pagination" aria-label="Invoice pages">
        <span>Page {invoicePageNumber} of {invoicePages} · {invoices.total} invoices</span>
        {invoicePageNumber>1&&<Link className="button button-secondary" href={billingHref({invoicePage:invoicePageNumber-1,paymentPage:paymentPageNumber,invoiceStatus:params.invoice_status,paymentStatus:params.payment_status})}>Previous</Link>}
        {invoicePageNumber<invoicePages&&<Link className="button button-secondary" href={billingHref({invoicePage:invoicePageNumber+1,paymentPage:paymentPageNumber,invoiceStatus:params.invoice_status,paymentStatus:params.payment_status})}>Next</Link>}
      </nav>
    </SectionCard>

    <div className="two-column">
      {canManage&&<SectionCard eyebrow="New receivable" title="Create invoice"><InvoiceCreateForm/></SectionCard>}
      {canManage&&<SectionCard eyebrow="Cash receipt" title="Record payment"><PaymentCreateForm/></SectionCard>}
    </div>
    <SectionCard eyebrow="Payment register" title="Received payments" meta={payments.total+" payments"}>
      <form method="get" className="toolbar-row">
        <label>Status<select name="payment_status" defaultValue={params.payment_status||""}><option value="">All statuses</option><option value="received">Received</option><option value="reversed">Reversed</option></select></label>
        <input type="hidden" name="invoice_page" value={String(invoicePageNumber)}/>
        {params.invoice_status&&<input type="hidden" name="invoice_status" value={params.invoice_status}/>}
        <button className="button button-primary" type="submit">Apply</button>
        <Link className="button button-secondary" href="/dashboard/saas/billing">Clear</Link>
      </form>
      <DataTable columns={["Payment date","Invoice","Account","Amount","Method","Reference","Status","Update"]} empty={<EmptyState title="No payments on this page" description="Received payments will appear here after reconciliation."/>} rows={payments.items.map(p=>[
        <span key="a">{new Date(p.received_at).toLocaleDateString()}</span>,
        <strong key="b">{p.invoice_number}</strong>,
        <Link key="c" className="text-link" href={"/dashboard/saas/clients/"+p.account_id}>{p.account_name}</Link>,
        <strong key="d">{money(p.amount_minor,p.currency)}</strong>,
        <span key="e">{p.method||"—"}</span>,
        <span key="f">{p.reference||"—"}</span>,
        <StatusBadge key="g" status={p.status}/>,
        canManage?<PaymentStatusControl key="h" id={p.id} status={p.status}/>:<span key="h">Read only</span>
      ])}/>
      <nav className="toolbar-row saas-spaced-pagination" aria-label="Payment pages">
        <span>Page {paymentPageNumber} of {paymentPages} · {payments.total} payments</span>
        {paymentPageNumber>1&&<Link className="button button-secondary" href={billingHref({invoicePage:invoicePageNumber,paymentPage:paymentPageNumber-1,invoiceStatus:params.invoice_status,paymentStatus:params.payment_status})}>Previous</Link>}
        {paymentPageNumber<paymentPages&&<Link className="button button-secondary" href={billingHref({invoicePage:invoicePageNumber,paymentPage:paymentPageNumber+1,invoiceStatus:params.invoice_status,paymentStatus:params.payment_status})}>Next</Link>}
      </nav>
    </SectionCard>
  </DashboardShell>;
}
