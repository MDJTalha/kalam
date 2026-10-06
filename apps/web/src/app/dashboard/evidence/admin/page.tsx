import { DashboardShell } from "@/components/dashboard-shell";
import { EvidenceOperations } from "@/components/evidence-operations";
import { EmptyState, Section } from "@/components/ui";
import { apiJson, apiJsonResult, requireUser } from "@/lib/server-api";
import { FileCheck2 } from "lucide-react";

type Person={id:string;first_name:string;last_name:string;email:string;job_title?:string|null};
type PeoplePage={items:Person[];total:number};
type Competency={id:string;name:string;code:string;status:string};
type Evidence={id:string;user_id:string;target_type:string;target_id:string;evidence_type:string;source_type:string;source_id?:string|null;demonstrated_level:number;confidence:number;status:string;observed_at:string;notes?:string|null;rejection_reason?:string|null};
type EvidencePage={items:Evidence[];total:number;page:number;page_size:number};

export default async function EvidenceAdminPage(){
 const user=await requireUser<{permissions?:string[]}>();
 const permissions=user.permissions??[];
 if(!permissions.includes("evidence.read")) return <DashboardShell title="Evidence operations" eyebrow="Capability evidence"><EmptyState title="Access restricted" description="This workspace requires evidence access." icon={FileCheck2}/></DashboardShell>;
 const [peoplePage,competencies,evidenceResult]=await Promise.all([apiJson<PeoplePage>("/api/v1/people/page?page=1&page_size=20&status=active"),apiJson<Competency[]>("/api/v1/capability-domain/competencies"),apiJsonResult<EvidencePage>("/api/v1/evidence/page?page=1&page_size=50")]);
 const people=peoplePage?.items??null;
 const evidence=evidenceResult.ok?evidenceResult.data:null;
 const failed=!people||!competencies||!evidence;
 return <DashboardShell title="Evidence operations" eyebrow="Capability evidence" breadcrumbs={[{label:"Skills & Capabilities",href:"/dashboard/skills"},{label:"Evidence operations"}]}>
  {failed?<Section eyebrow="Evidence engine" title="Evidence data unavailable"><p>One or more governed evidence sources could not be loaded. Refresh after the capability services are available.</p></Section>:
   <EvidenceOperations people={people??[]} competencies={(competencies??[]).filter(x=>x.status!=="retired")} initialEvidence={evidence?.items??[]} initialTotal={evidence?.total??0} canVerify={permissions.includes("evidence.verify")}/>}
 </DashboardShell>;
}
