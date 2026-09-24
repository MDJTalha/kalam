import { Target, CheckCircle2 } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJson, requireUser } from "@/lib/server-api";

type Goal = { title: string; target_date?: string | null; status: string; notes?: string | null };
type Plan = { id: string; title: string; status: string; goals: Goal[]; created_at: string; updated_at: string };

export default async function DevelopmentPage() {
  await requireUser();
  const plans = await apiJson<Plan[]>("/api/v1/development/my");
  const goalCount = plans?.reduce((total, plan) => total + plan.goals.length, 0) ?? 0;
  const completed = plans?.reduce((total, plan) => total + plan.goals.filter((goal) => goal.status === "completed").length, 0) ?? 0;

  return (
    <DashboardShell title="Development plans" eyebrow="Individual capability growth">
      <div className="stat-grid">
        <div className="stat-card"><span>Plans</span><strong>{plans?.length ?? 0}</strong><small>Personal development plans</small></div>
        <div className="stat-card"><span>Goals</span><strong>{goalCount}</strong><small>Tracked development goals</small></div>
        <div className="stat-card"><span>Completed</span><strong>{completed}</strong><small>Goals completed</small></div>
        <div className="stat-card"><span>Progress</span><strong>{goalCount ? Math.round(completed / goalCount * 100) : 0}%</strong><small>Goal completion rate</small></div>
      </div>

      {plans?.length ? plans.map((plan) => (
        <section className="data-panel" key={plan.id}>
          <div className="section-heading compact"><div><span className="eyebrow">{plan.status}</span><h2>{plan.title}</h2></div><Target size={20}/></div>
          <div className="compact-list">
            {plan.goals.length ? plan.goals.map((goal, index) => (
              <div className="compact-row" key={plan.id + "-" + index}>
                <div><strong>{goal.title}</strong><small>{goal.target_date ? "Target " + new Date(goal.target_date).toLocaleDateString() : "No target date"} · {goal.status}</small></div>
                <CheckCircle2 size={17}/>
              </div>
            )) : <div className="empty-state"><p>No goals are attached to this plan.</p></div>}
          </div>
        </section>
      )) : (
        <section className="data-panel"><div className="empty-state"><Target size={28}/><h2>No development plans yet</h2><p>Create a plan through the HR/L&D workflow to start tracking capability goals.</p></div></section>
      )}
    </DashboardShell>
  );
}
