import { DashboardShell } from "@/components/dashboard-shell";
import { DevelopmentPlanner } from "@/components/development-planner";
import { apiJson, requireUser } from "@/lib/server-api";
type Goal={title:string;target_date?:string|null;status:string;notes?:string|null};
type Plan={id:string;title:string;status:string;goals:Goal[]};
export default async function DevelopmentPage(){
  await requireUser();
  const plans=await apiJson<Plan[]>("/api/v1/development/my");
  const goals=plans?.flatMap(plan=>plan.goals)??[];
  const completed=goals.filter(goal=>goal.status==="completed").length;
  const active=plans?.filter(plan=>plan.status==="active").length??0;
  return <DashboardShell title="Development Plans" eyebrow="Individual capability growth">
    <section className="skills-command-hero"><div><span className="eyebrow">My development</span><h2>Turn capability needs into achievable goals.</h2><p>Create a plan, set a target date for each goal, record progress, and review manager milestones and feedback in one place.</p></div><div className="skills-command-aside"><span>Active plans</span><strong>{active}</strong><small>of {plans?.length??0} personal plans</small></div></section>
    <section className="stat-grid" aria-label="Development indicators">
      <div className="stat-card"><span>Plans</span><strong>{plans?.length??0}</strong><small>Personal plans</small></div>
      <div className="stat-card"><span>Goals</span><strong>{goals.length}</strong><small>Across all plans</small></div>
      <div className="stat-card"><span>Completed</span><strong>{completed}</strong><small>Goals marked complete</small></div>
      <div className="stat-card"><span>Goal progress</span><strong>{goals.length?Math.round(completed/goals.length*100):0}%</strong><small>Of recorded goals</small></div>
    </section>
    <DevelopmentPlanner initial={plans??[]}/>
  </DashboardShell>;
}
