import { DashboardShell } from "@/components/dashboard-shell";
import { CapabilityGapWorkspace } from "@/components/capability-gap-workspace";
import { apiJsonResult, requireUser } from "@/lib/server-api";
import { Target } from "lucide-react";
import { StateMessage } from "@/components/ui";

type Gap={user_id:string;role_id:string;role:string;role_requirement_id:string;target_type:string;target_id:string;target:string|null;required_level:number;demonstrated_level:number|null;gap:number|null;severity:string;criticality:string;weight:number;evidence_confidence:number;evidence_count:number;evidence_observed_at:string|null;evidence_freshness:string;calculation_version:string};
type Summary={scope:string;total_requirements:number;material_gaps:number;counts:Record<string,number>;critical_exposure:number;major_exposure:number;weighted_gap:number;calculation_version:string;freshness_days:number};
type Person={id:string;first_name:string;last_name:string;email:string;job_title?:string|null};
type PeoplePage={items:Person[]};

export default async function CapabilityGapsPage(){
 const user=await requireUser<{id:string;permissions?:string[]}>();
 const permissions=user.permissions||[];
 const canManage=permissions.includes("capability_gaps.manage");
 if(!permissions.includes("capability_gaps.read")&&!canManage)return <DashboardShell title="Capability Gaps" eyebrow="Capability intelligence"><section className="data-panel"><Target size={22}/><h2>Access restricted</h2><p>Your role does not have access to capability gap intelligence.</p></section></DashboardShell>;
 const query=canManage?"":"?user_id="+encodeURIComponent(user.id);
 const fallback:Summary={scope:canManage?"enterprise":"person",total_requirements:0,material_gaps:0,counts:{},critical_exposure:0,major_exposure:0,weighted_gap:0,calculation_version:"phase4.v1",freshness_days:180}; const [gapsResult,summaryResult,peopleResult,currentPerson]=await Promise.all([
  apiJsonResult<Gap[]>("/api/v1/capability-gaps"+query),
  apiJsonResult<Summary>("/api/v1/capability-gaps/summary?scope="+(canManage?"enterprise":"person")+(canManage?"":"&scope_id="+encodeURIComponent(user.id))),
  canManage?apiJsonResult<PeoplePage>("/api/v1/people/page?page=1&page_size=20&status=active"):Promise.resolve({ok:true,status:200,data:{items:[]},error:null}),
  canManage?apiJsonResult<Person>("/api/v1/people/me"):Promise.resolve({ok:true,status:200,data:null,error:null})
 ]);
 const failed=!gapsResult.ok || !summaryResult.ok || !peopleResult.ok || !currentPerson.ok;
 const people=[...(peopleResult.data?.items||[]),...(currentPerson.data?[currentPerson.data]:[])].filter((person,index,array)=>array.findIndex(item=>item.id===person.id)===index);
 return <DashboardShell title="Capability Gaps" eyebrow="Capability intelligence" breadcrumbs={[{label:"Overview",href:"/dashboard"},{label:"Capability Gaps"}]}>
   {failed
     ? <StateMessage tone="danger" title="Capability gap intelligence is incomplete">One or more capability datasets could not be loaded. Gap values are not replaced with zero when the service fails; refresh the workspace before making development decisions.</StateMessage>
     : <CapabilityGapWorkspace initialGaps={gapsResult.data ?? []} initialSummary={summaryResult.data ?? fallback} people={people} canManage={canManage} currentUserId={user.id}/>}
 </DashboardShell>;
}
