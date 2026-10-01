import { BarChart3, CircleDollarSign, Gauge, ReceiptText } from "lucide-react";
import Link from "next/link";
import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { EmptyState, MetricCard, SectionCard } from "@/components/ui";
import { apiJson } from "@/lib/server-api";

type Row={currency:string;stage:string;gross_minor:number;weighted_minor:number;opportunities:number};
type Forecast={pipeline:Row[];open_invoices:Array<{currency:string;outstanding_minor:number;invoices:number}>};
function money(minor:number,currency:string){return new Intl.NumberFormat("en-US",{style:"currency",currency,maximumFractionDigits:minor%100===0?0:2}).format(minor/100);}
function pct(value:number,total:number){return total?Math.round(value/total*100):0;}

export default async function SaaSForecastPage(){
  const forecast=await apiJson<Forecast>("/api/v1/saas/crm/forecast");
  if(!forecast)return <DashboardShell title="Forecast" eyebrow="SaaS CRM"><EmptyState title="Forecast access is restricted" description="This page requires authorized SaaS CRM access."/></DashboardShell>;
  const opportunityCount=forecast.pipeline.reduce((s,r)=>s+r.opportunities,0), invoiceCount=forecast.open_invoices.reduce((s,r)=>s+r.invoices,0);
  const currencies=[...new Set([...forecast.pipeline.map(r=>r.currency),...forecast.open_invoices.map(r=>r.currency)])];
  const byCurrency=currencies.map(currency=>{const rows=forecast.pipeline.filter(r=>r.currency===currency), gross=rows.reduce((s,r)=>s+r.gross_minor,0), weighted=rows.reduce((s,r)=>s+r.weighted_minor,0), receivable=forecast.open_invoices.find(r=>r.currency===currency); return {currency,rows,gross,weighted,receivable};});
  return <DashboardShell title="Forecast" eyebrow="SaaS CRM" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Forecast"}]}>
    <SaaSCrmNav/>
    <div className="forecast-hero"><div><span className="eyebrow">Executive revenue outlook</span><h2>Forecast & receivables</h2><p>Live weighted pipeline and outstanding receivables from the SaaS CRM.</p></div><Link className="button forecast-action" href="/dashboard/saas/pipeline">Open pipeline <span>→</span></Link></div>
    <div className="stat-grid forecast-stats">
      <MetricCard label="Open opportunities" value={opportunityCount} detail="Excludes won / lost" icon={BarChart3}/>
      <MetricCard label="Gross pipeline" value={currencies.length===1?money(byCurrency[0].gross,byCurrency[0].currency):currencies.length+" currencies"} detail="Reported by currency" icon={CircleDollarSign}/>
      <MetricCard label="Weighted pipeline" value={currencies.length===1?money(byCurrency[0].weighted,byCurrency[0].currency):"Multi-currency"} detail="Configured probability model" icon={Gauge}/>
      <MetricCard label="Open invoices" value={invoiceCount} detail="Issued / partial / overdue" icon={ReceiptText}/>
    </div>
    <div className="forecast-grid"><SectionCard eyebrow="Pipeline forecast" title="Gross vs weighted pipeline">
      {byCurrency.length?byCurrency.map(b=><div className="forecast-currency" key={b.currency}><div className="forecast-currency-head"><strong>{b.currency}</strong><span>{b.rows.reduce((s,r)=>s+r.opportunities,0)} opportunities</span></div><div className="forecast-metric"><span>Gross</span><strong>{money(b.gross,b.currency)}</strong><div className="forecast-track"><i className="forecast-track-full"/></div></div><div className="forecast-metric"><span>Weighted</span><strong>{money(b.weighted,b.currency)} <em>{pct(b.weighted,b.gross)}%</em></strong><div className="forecast-track weighted"><i style={{width:pct(b.weighted,b.gross)+"%"}}/></div></div><div className="forecast-stages">{b.rows.map(r=><div key={r.stage}><span>{r.stage.replace(/_/g," ")}</span><b>{money(r.gross_minor,b.currency)}</b><small>{r.opportunities} · {pct(r.weighted_minor,r.gross_minor)}% weighted</small></div>)}</div></div>):<EmptyState title="No open pipeline" description="Open opportunities with configured values will appear here."/>}
      <p className="muted forecast-note">Weighted pipeline is calculated from opportunity amount × configured probability. It is a planning view, not a revenue prediction.</p>
    </SectionCard>
    <SectionCard eyebrow="Receivables" title="Outstanding by currency">
      {byCurrency.filter(b=>b.receivable).length?byCurrency.filter(b=>b.receivable).map(b=><div className="receivable-row" key={b.currency}><div><strong>{b.currency}</strong><small>{b.receivable!.invoices} open invoices</small></div><strong>{money(b.receivable!.outstanding_minor,b.currency)}</strong></div>):<EmptyState title="No open invoices" description="Issued, partially paid or overdue invoices will appear here."/>}
    </SectionCard></div>
  </DashboardShell>;
}
