import { Target } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { CapabilityAssessmentWorkspace } from "@/components/capability-assessment-workspace";
import { apiJson, requireUser } from "@/lib/server-api";

type Assessment={id:string;title:string;assessment_type:string;measurement_method:string;validity_days:number|null;reassessment_interval_days:number|null};
type Person={id:string;first_name:string;last_name:string;email:string;job_title?:string|null};
type Candidate={id:string;type:string;name:string;code?:string};
type Target={id:string;assessment_id:string;target_type:string;target_id:string;target_name:string|null;target_level:number;weight:number};
type Cycle={id:string;assessment_id:string;assessment_title:string;assessment_type:string;user_id:string;target_type:string;target_id:string;required_level:number;baseline_level:number|null;current_level:number|null;gap:number|null;improvement:number|null;status:string;next_reassessment_due_at:string|null;development_plan_id:string|null};
type PeoplePage={items:Person[];total:number};

export default async function CapabilityAssessmentsPage({searchParams}:{searchParams:Promise<{assessment?:string}>}){
  const user=await requireUser<{id:string;permissions?:string[]}>();
  const permissions=user.permissions||[];
  const canManage=permissions.includes("capability_assessments.manage");
  if(!permissions.includes("capability_assessments.read")&&!canManage){
    return <DashboardShell title="Capability Assessments" eyebrow="Capability measurement"><section className="data-panel"><Target size={22}/><h2>Access restricted</h2><p>Your role does not have access to capability assessment cycles.</p></section></DashboardShell>;
  }
  const assessments=await apiJson<Assessment[]>("/api/v1/assessments")||[];
  const currentPerson=await apiJson<Person>("/api/v1/people/me");
  const peoplePage=canManage ? await apiJson<PeoplePage>("/api/v1/people/page?page=1&page_size=20&status=active") : null;
  const people=canManage ? [...(peoplePage?.items||[]), ...(currentPerson?[currentPerson]:[])].filter((person,index,array)=>array.findIndex(item=>item.id===person.id)===index) : (currentPerson?[currentPerson]:[]);
  const candidates:Candidate[]=[];
  if(canManage){
    const [capabilities,competencies]=await Promise.all([
      apiJson<Array<{id:string;name:string;code:string;status:string}>>("/api/v1/capabilities?status=active"),
      apiJson<Array<{id:string;name:string;code:string;status:string}>>("/api/v1/capability-domain/competencies")
    ]);
    (capabilities||[]).forEach(x=>candidates.push({id:x.id,type:"capability",name:x.name,code:x.code}));
    (competencies||[]).filter(x=>x.status!=="retired").forEach(x=>candidates.push({id:x.id,type:"competency",name:x.name,code:x.code}));
  }
  const {assessment: requestedAssessment}=await searchParams;
  const selectedAssessment=assessments.find(item=>item.id===requestedAssessment)??assessments[0];
  const targets=selectedAssessment ? await apiJson<Target[]>("/api/v1/capability-assessments/assessments/"+selectedAssessment.id+"/targets")||[] : [];
  const initialCycles=await apiJson<Cycle[]>("/api/v1/capability-assessments/cycles?user_id="+encodeURIComponent(user.id))||[];

  return <DashboardShell title="Capability Assessments" eyebrow="Capability measurement" breadcrumbs={[{label:"Overview",href:"/dashboard"},{label:"Capability Assessments"}]}>
    <CapabilityAssessmentWorkspace assessments={assessments} initialAssessmentId={selectedAssessment?.id||""} people={people} candidates={candidates} initialTargets={targets} initialCycles={initialCycles} canManage={canManage} currentUserId={user.id}/>
  </DashboardShell>;
}
