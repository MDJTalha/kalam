import { Target } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { CapabilityAssessmentWorkspace } from "@/components/capability-assessment-workspace";
import { StateMessage } from "@/components/ui";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type Assessment={id:string;title:string;assessment_type:string;measurement_method:string;validity_days:number|null;reassessment_interval_days:number|null};
type Person={id:string;first_name:string;last_name:string;email:string;job_title?:string|null};
type Candidate={id:string;type:string;name:string;code?:string};
type Target={id:string;assessment_id:string;target_type:string;target_id:string;target_name:string|null;target_level:number;weight:number};
type Cycle={id:string;assessment_id:string;assessment_title:string;assessment_type:string;user_id:string;target_type:string;target_id:string;required_level:number;baseline_level:number|null;current_level:number|null;gap:number|null;improvement:number|null;status:string;next_reassessment_due_at:string|null;development_plan_id:string|null};
type PeoplePage={items:Person[];total:number};
type CandidateRecord={id:string;name:string;code:string;status:string};
type CompetencyPage={items:CandidateRecord[];total:number};

export default async function CapabilityAssessmentsPage({searchParams}:{searchParams:Promise<{assessment?:string}>}){
  const user=await requireUser<{id:string;permissions?:string[]}>();
  const permissions=user.permissions||[];
  const canManage=permissions.includes("capability_assessments.manage");
  if(!permissions.includes("capability_assessments.read")&&!canManage){
    return <DashboardShell title="Capability Assessments" eyebrow="Capability measurement"><section className="data-panel"><Target size={22}/><h2>Access restricted</h2><p>Your role does not have access to capability assessment cycles.</p></section></DashboardShell>;
  }
  const assessmentResult=await apiJsonResult<Assessment[]>("/api/v1/assessments");
  if(!assessmentResult.ok)return <DashboardShell title="Capability Assessments" eyebrow="Capability measurement"><StateMessage tone="danger" title="Assessment data unavailable">HTTP {assessmentResult.status}: {assessmentResult.error||"The assessment service could not be reached."}</StateMessage></DashboardShell>;
  const assessments=assessmentResult.data||[];
  const currentPersonResult=await apiJsonResult<Person>("/api/v1/people/me");
  if(!currentPersonResult.ok)return <DashboardShell title="Capability Assessments" eyebrow="Capability measurement"><StateMessage tone="danger" title="Your learner profile could not be loaded">HTTP {currentPersonResult.status}: {currentPersonResult.error||"Refresh after the profile service is available."}</StateMessage></DashboardShell>;
  const currentPerson=currentPersonResult.data;
  const peopleResult=canManage ? await apiJsonResult<PeoplePage>("/api/v1/people/page?page=1&page_size=20&status=active") : null;
  if(peopleResult&&!peopleResult.ok)return <DashboardShell title="Capability Assessments" eyebrow="Capability measurement"><StateMessage tone="danger" title="People lookup unavailable">HTTP {peopleResult.status}: {peopleResult.error||"Required people permission or service is unavailable."}</StateMessage></DashboardShell>;
  const peoplePage=peopleResult?.data;
  const people=canManage ? [...(peoplePage?.items||[]), ...(currentPerson?[currentPerson]:[])].filter((person,index,array)=>array.findIndex(item=>item.id===person.id)===index) : (currentPerson?[currentPerson]:[]);
  const candidates:Candidate[]=[];
  if(canManage){
    const [capabilityResult,competencyResult]=await Promise.all([
      apiJsonResult<CandidateRecord[]>("/api/v1/capabilities?status=active"),
      apiJsonResult<CompetencyPage>("/api/v1/capability-domain/competencies/page?page=1&page_size=100")
    ]);
    if(!capabilityResult.ok||!competencyResult.ok){const failed=[capabilityResult,competencyResult].filter(result=>!result.ok).map(result=>`HTTP ${result.status}: ${result.error||"request failed"}`);return <DashboardShell title="Capability Assessments" eyebrow="Capability measurement"><StateMessage tone="danger" title="Assessment target catalog unavailable">{failed.join(" · ")}</StateMessage></DashboardShell>;}
    const capabilities=capabilityResult.data||[],competencies=competencyResult.data?.items||[];
    if((competencyResult.data?.total||0)>competencies.length)return <DashboardShell title="Capability Assessments" eyebrow="Capability measurement"><StateMessage tone="danger" title="Assessment target catalog exceeds the loaded limit">The competency catalog has more than 100 records. Narrow the catalog or add server-side search before creating assessment targets; the current screen will not present an incomplete list.</StateMessage></DashboardShell>;
    (capabilities||[]).forEach(x=>candidates.push({id:x.id,type:"capability",name:x.name,code:x.code}));
    (competencies||[]).filter(x=>x.status!=="retired").forEach(x=>candidates.push({id:x.id,type:"competency",name:x.name,code:x.code}));
  }
  const {assessment: requestedAssessment}=await searchParams;
  const selectedAssessment=assessments.find(item=>item.id===requestedAssessment)??assessments[0];
  const targetsResult=selectedAssessment ? await apiJsonResult<Target[]>("/api/v1/capability-assessments/assessments/"+selectedAssessment.id+"/targets") : null;
  if(targetsResult&&!targetsResult.ok)return <DashboardShell title="Capability Assessments" eyebrow="Capability measurement"><StateMessage tone="danger" title="Assessment targets unavailable">HTTP {targetsResult.status}: {targetsResult.error||"Target mapping could not be loaded."}</StateMessage></DashboardShell>;
  const targets=targetsResult?.data||[];
  const cyclesResult=await apiJsonResult<Cycle[]>("/api/v1/capability-assessments/cycles?user_id="+encodeURIComponent(user.id));
  if(!cyclesResult.ok)return <DashboardShell title="Capability Assessments" eyebrow="Capability measurement"><StateMessage tone="danger" title="Assessment cycles unavailable">HTTP {cyclesResult.status}: {cyclesResult.error||"Assessment cycles could not be loaded."}</StateMessage></DashboardShell>;
  const initialCycles=cyclesResult.data||[];

  return <DashboardShell title="Capability Assessments" eyebrow="Capability measurement" breadcrumbs={[{label:"Overview",href:"/dashboard"},{label:"Capability Assessments"}]}>
    <CapabilityAssessmentWorkspace assessments={assessments} initialAssessmentId={selectedAssessment?.id||""} people={people} candidates={candidates} initialTargets={targets} initialCycles={initialCycles} canManage={canManage} currentUserId={user.id}/>
  </DashboardShell>;
}
