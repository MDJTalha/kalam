import { DashboardShell } from "@/components/dashboard-shell";
import { EvidenceOperations } from "@/components/evidence-operations";
import { EmptyState, Section } from "@/components/ui";
import { apiJsonResult, requireUser } from "@/lib/server-api";
import { FileCheck2 } from "lucide-react";

type Person={id:string;first_name:string;last_name:string;email:string;job_title?:string|null};
type PeoplePage={items:Person[];total:number};
type Competency={id:string;name:string;code:string;status:string};
type CompetencyPage={items:Competency[];total:number};
type Evidence={id:string;user_id:string;target_type:string;target_id:string;evidence_type:string;source_type:string;source_id?:string|null;demonstrated_level:number;confidence:number;status:string;observed_at:string;notes?:string|null;rejection_reason?:string|null;submitted_by?:string|null;assessor_id?:string|null};
type EvidencePage={items:Evidence[];total:number;page:number;page_size:number};

export default async function EvidenceAdminPage(){
 const user=await requireUser<{id:string;permissions?:string[]}>();
 const permissions=user.permissions??[];
 const canCapture=permissions.includes("evidence.manage");
 const canVerify=permissions.includes("evidence.verify");
 const canFilterPeople=permissions.includes("users.read");
 if(!permissions.includes("evidence.read")&&!canCapture&&!canVerify) return <DashboardShell title="Evidence operations" eyebrow="Capability evidence"><EmptyState title="Access restricted" description="This workspace requires capability evidence access." icon={FileCheck2}/></DashboardShell>;

 const peoplePromise=canCapture&&canFilterPeople
   ? apiJsonResult<PeoplePage>("/api/v1/people/page?page=1&page_size=20&status=active")
   : Promise.resolve(null);
 const [peopleResult,competencyResult,evidenceResult]=await Promise.all([
   peoplePromise,
   apiJsonResult<CompetencyPage>("/api/v1/capability-domain/competencies/page?page=1&page_size=100"),
   apiJsonResult<EvidencePage>("/api/v1/evidence/page?page=1&page_size=50"),
 ]);
 const people=peopleResult?.ok?peopleResult.data?.items??[]:[];
 const evidence=evidenceResult.ok?evidenceResult.data:null;
 const competencies=competencyResult.ok?competencyResult.data?.items:null;
 const failed=(canCapture&&canFilterPeople&&!peopleResult?.ok)
   ||!competencies
   ||!evidence
   ||((competencyResult.data?.total||0)>(competencies?.length||0));
 return <DashboardShell title="Evidence operations" eyebrow="Capability evidence" breadcrumbs={[{label:"Skills & Capabilities",href:"/dashboard/skills"},{label:"Evidence operations"}]}>
  {failed?<Section eyebrow="Evidence engine" title="Evidence data unavailable"><p>One or more authorized evidence sources could not be loaded, or the competency catalog exceeds the 100-item safety limit. Refresh after the capability services are available or narrow the catalog.</p></Section>:
   <EvidenceOperations
    people={people}
    competencies={(competencies??[]).filter(x=>x.status!=="retired")}
    initialEvidence={evidence?.items??[]}
    initialTotal={evidence?.total??0}
    canCapture={canCapture}
    canVerify={canVerify}
    canFilterPeople={canFilterPeople}
    currentUserId={user.id}
   />}
 </DashboardShell>;
}
