import { DashboardShell } from "@/components/dashboard-shell";
import { HelpCenter } from "@/components/help-center";
import { requireUser } from "@/lib/server-api";

type SupportCase={
  id:string;case_number:string;category:string;severity:string;subject:string;status:string;route?:string|null;created_at:string;resolved_at?:string|null;
};

type User={
  first_name:string;last_name:string;email:string;tenant_name?:string|null;job_title?:string|null;
  roles?:Array<{name:string}>;permissions?:string[];preferences?:{timezone?:string};
};

export default async function HelpPage(){
  const user=await requireUser<User>();
  const cases=await apiJsonResult<SupportCase[]>("/api/v1/support/cases").then((result) => result.ok ? result.data : null);
  return <DashboardShell title="Help & Support" eyebrow="Guidance, diagnostics & service support">
    {cases===null ? <section className="data-panel" role="alert"><h2>Support history unavailable</h2><p>Your support workspace could not be loaded. Refresh and try again.</p></section> : <HelpCenter user={user} initialCases={cases}/>} 
  </DashboardShell>;
}
