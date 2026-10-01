import { DashboardShell } from "@/components/dashboard-shell";
import { EvidenceOperations } from "@/components/evidence-operations";
import { EmptyState, Section } from "@/components/ui";
import { apiJson, requireUser } from "@/lib/server-api";
import { FileCheck2 } from "lucide-react";

type Person={id:string;first_name:string;last_name:string;email:string;job_title?:string|null};
type Competency={id:string;name:string;code:string;status:string};
type Evidence={id:string;user_id:string;target_type:string;target_id:string;evidence_type:string;source_type:string;source_id?:string|null;demonstrated_level:number;confidence:number;status:string;observed_at:string;notes?:string|null;rejection_reason?:string|null};

export default async function EvidenceAdminPage(){
 const user=await requireUser<{permissions?:string[]}>();
 const permissions=user.permissions??[];
 if(!permissions.includes("evidence.read")) return <DashboardShell title="Evidence operations" eyebrow="Capability evidence"><EmptyState title="Access restricted" description="This workspace requires evidence access." icon={FileCheck2}/></DashboardShell>;
 const [people,competencies,evidence]=await Promise.all([apiJson<Person[]>("/api/v1/people"),apiJson<Competency[]>("/api/v1/capability-domain/competencies"),apiJson<Evidence[]>("/api/v1/evidence")]);
 const failed=[people,competencies,evidence].some(x=>!x);
 return <DashboardShell title="Evidence operations" eyebrow="Capability evidence" breadcrumbs={[{label:"Skills & Capabilities",href:"/dashboard/skills"},{label:"Evidence operations"}]}>
  {failed?<Section eyebrow="Evidence engine" title="Evidence data unavailable"><p>One or more governed evidence sources could not be loaded. Refresh after the capability services are available.</p></Section>:
   <EvidenceOperations people={people??[]} competencies={(competencies??[]).filter(x=>x.status!=="retired")} initialEvidence={evidence??[]} canVerify={permissions.includes("evidence.verify")}/>}
 </DashboardShell>;
}
