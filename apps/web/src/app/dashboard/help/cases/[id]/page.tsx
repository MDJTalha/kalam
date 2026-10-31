import { notFound } from "next/navigation";
import { DashboardShell } from "@/components/dashboard-shell";
import { SupportCaseConversation, type SupportCaseDetail, type SupportCaseMessage } from "@/components/support-case-conversation";
import { apiFetch, requireUser } from "@/lib/server-api";

export default async function SupportCasePage({params}:{params:Promise<{id:string}>}){
  await requireUser();
  const {id}=await params;
  const response=await apiFetch("/api/v1/support/cases/"+encodeURIComponent(id));
  if(response.status===404)notFound();
  if(!response.ok)throw new Error("Support case could not be loaded.");
  const supportCase=await response.json() as SupportCaseDetail;
  const messages=await apiJsonResult<SupportCaseMessage[]>("/api/v1/support/cases/"+encodeURIComponent(id)+"/messages").then((result) => result.ok ? result.data : null);
  return <DashboardShell title={supportCase.case_number} eyebrow="Support case" breadcrumbs={[{label:"Help & Support",href:"/dashboard/help"},{label:supportCase.case_number}]}>{messages===null ? <section className="data-panel" role="alert"><h2>Conversation unavailable</h2><p>The case loaded, but its conversation could not be retrieved. Refresh and try again.</p></section> : <SupportCaseConversation supportCase={supportCase} initialMessages={messages}/>}</DashboardShell>;
}
