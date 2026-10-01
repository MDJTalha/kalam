import { DashboardShell } from "@/components/dashboard-shell";
import { DevelopmentIntelligence } from "@/components/development-intelligence";
import { DevelopmentPlanner } from "@/components/development-planner";
import { DevelopmentExecution } from "@/components/development-execution";
import { apiJsonResult, requireUser } from "@/lib/server-api";
type Goal={title:string;target_date?:string|null;status:string;notes?:string|null};
type Plan={id:string;title:string;status:string;goals:Goal[]};
type Recommendation={id:string;capability_gap_id:string;intervention_type:string;source_type:string;title:string;rationale:string;score:number;priority:string;timeframe_days:number;status:string;metadata:Record<string,unknown>;recommendation_version:string};
export default async function DevelopmentPage(){
  const user=await requireUser<{permissions?:string[]}>();
  const canVerify=user.permissions?.includes("development.recommendations.manage")??false;
  const result=await apiJsonResult<Plan[]>("/api/v1/development/my");
  if (!result.ok) {
    const restricted=result.status===403; const serviceFailure=result.status>=500;
    return <DashboardShell title="Development Plans" eyebrow="Individual capability growth"><section className="data-panel" role="alert"><h2>{restricted?"Development access restricted":serviceFailure?"Development service unavailable":"Development plans could not be loaded"}</h2><p>{restricted?"Your role does not have access to development plans.":serviceFailure?"The development service did not respond successfully. No empty plan list is being shown.":result.error||"Plans could not be loaded. Refresh and try again."}</p></section></DashboardShell>;
  }
  const plans=result.data??[]; const goals=plans.flatMap(plan=>plan.goals); const completed=goals.filter(goal=>goal.status==="completed").length; const active=plans.filter(plan=>plan.status==="active").length;
  const recResult=await apiJsonResult<Recommendation[]>("/api/v1/development/recommendations"); const recommendations=recResult.ok?(recResult.data??[]):[];
  return <DashboardShell title="Development Plans" eyebrow="Individual capability growth">
    <section className="skills-command-hero"><div><span className="eyebrow">My development</span><h2>Turn capability needs into achievable goals.</h2><p>Connect capability gaps to the right development intervention, then track goals, milestones and feedback in one place.</p></div><div className="skills-command-aside"><span>Active plans</span><strong>{active}</strong><small>of {plans.length} personal plans</small></div></section>
    <section className="stat-grid" aria-label="Development indicators"><div className="stat-card"><span>Plans</span><strong>{plans.length}</strong><small>Personal plans</small></div><div className="stat-card"><span>Goals</span><strong>{goals.length}</strong><small>Across all plans</small></div><div className="stat-card"><span>Completed</span><strong>{completed}</strong><small>Goals marked complete</small></div><div className="stat-card"><span>Recommendations</span><strong>{recommendations.length}</strong><small>Governed interventions</small></div></section>
    {recResult.ok?<DevelopmentIntelligence initial={recommendations}/>:<section className="data-panel" role="alert"><h2>Development intelligence unavailable</h2><p>{recResult.error||"Recommendations could not be loaded. Your existing development plans remain available."}</p></section>}
    <DevelopmentExecution canVerify={canVerify} />
    <DevelopmentPlanner initial={plans}/>
  </DashboardShell>;
}
