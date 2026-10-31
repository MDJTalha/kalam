"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { CalendarDays, CheckCircle2, ClipboardList, MessageSquare, Plus, RefreshCw, UserRound } from "lucide-react";
import { StatusBadge } from "@/components/ui";

type Member = { id: string; first_name: string; last_name: string; email: string; job_title?: string | null };
type Plan = { id: string; title: string; status: string; goals: Array<{ title: string; status: string; target_date?: string | null; notes?: string | null }> };
type Milestone = { id: string; title: string; description?: string | null; due_at?: string | null; status: string; completed_at?: string | null };
type Feedback = { id: string; reviewer_id: string; reviewer: string; rating?: number | null; strengths?: string | null; feedback: string; next_steps?: string | null; created_at: string };
type Progress = { plan: { id: string; title: string; status: string }; milestones: Milestone[]; feedback: Feedback[] };

async function request<T>(path: string, method = "GET", body?: Record<string, unknown>): Promise<T> {
  const response = await fetch(path, {
    method,
    headers: body ? { "content-type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Request failed (" + response.status + ")");
  return payload as T;
}

const formatDate = (value?: string | null) => value ? new Date(value).toLocaleDateString() : "No due date";

export function DevelopmentTeamReview({ members, initialSelectedId, organizationWide = false }: { members: Member[]; initialSelectedId?: string | null; organizationWide?: boolean }) {
  const initial = members.some(item => item.id === initialSelectedId) ? (initialSelectedId ?? "") : (members[0]?.id ?? "");
  const [memberId, setMemberId] = useState(initial);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [planId, setPlanId] = useState("");
  const [progress, setProgress] = useState<Progress | null>(null);
  const [loadingPlans, setLoadingPlans] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [milestoneTitle, setMilestoneTitle] = useState("");
  const [milestoneDescription, setMilestoneDescription] = useState("");
  const [milestoneDue, setMilestoneDue] = useState("");
  const [rating, setRating] = useState("");
  const [strengths, setStrengths] = useState("");
  const [feedback, setFeedback] = useState("");
  const [nextSteps, setNextSteps] = useState("");

  const selectedMember = members.find(item => item.id === memberId) ?? null;
  const selectedPlan = useMemo(() => plans.find(item => item.id === planId) ?? null, [plans, planId]);

  useEffect(() => {
    let active = true;
    async function load() {
      setPlans([]);
      setPlanId("");
      setProgress(null);
      setError("");
      setMessage("");
      if (!memberId) return;
      setLoadingPlans(true);
      try {
        const result = await request<Plan[]>("/api/lms/development/users/" + encodeURIComponent(memberId));
        if (!active) return;
        setPlans(result);
        setPlanId(result[0]?.id ?? "");
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Development plans could not be loaded.");
      } finally {
        if (active) setLoadingPlans(false);
      }
    }
    void load();
    return () => { active = false; };
  }, [memberId]);

  useEffect(() => {
    let active = true;
    async function load() {
      setProgress(null);
      if (!planId) return;
      setLoadingProgress(true);
      try {
        const result = await request<Progress>("/api/lms/development/" + encodeURIComponent(planId) + "/progress");
        if (active) setProgress(result);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Plan progress could not be loaded.");
      } finally {
        if (active) setLoadingProgress(false);
      }
    }
    void load();
    return () => { active = false; };
  }, [planId]);

  async function refresh() {
    if (!memberId) return;
    setError("");
    try {
      const result = await request<Plan[]>("/api/lms/development/users/" + encodeURIComponent(memberId));
      setPlans(result);
      if (!result.some(item => item.id === planId)) setPlanId(result[0]?.id ?? "");
      else if (planId) setProgress(await request<Progress>("/api/lms/development/" + encodeURIComponent(planId) + "/progress"));
      setMessage("Development records refreshed.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Development records could not be refreshed.");
    }
  }

  async function addMilestone(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!planId || !milestoneTitle.trim() || busy) return;
    setBusy(true); setError(""); setMessage("");
    try {
      await request("/api/lms/development/" + encodeURIComponent(planId) + "/milestones", "POST", {
        title: milestoneTitle.trim(),
        description: milestoneDescription.trim() || null,
        due_at: milestoneDue ? new Date(milestoneDue + "T23:59:00").toISOString() : null,
      });
      setMilestoneTitle(""); setMilestoneDescription(""); setMilestoneDue("");
      setProgress(await request<Progress>("/api/lms/development/" + encodeURIComponent(planId) + "/progress"));
      setMessage("Manager milestone added and audited.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Milestone could not be created.");
    } finally {
      setBusy(false);
    }
  }

  async function updateMilestone(item: Milestone, status: string) {
    if (!planId || busy) return;
    setBusy(true); setError(""); setMessage("");
    try {
      await request("/api/lms/development/" + encodeURIComponent(planId) + "/milestones/" + encodeURIComponent(item.id), "PATCH", { status });
      setProgress(await request<Progress>("/api/lms/development/" + encodeURIComponent(planId) + "/progress"));
      setMessage(status === "completed" ? "Milestone marked complete." : "Milestone reopened.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Milestone could not be updated.");
    } finally {
      setBusy(false);
    }
  }

  async function submitFeedback(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!planId || !feedback.trim() || busy) return;
    setBusy(true); setError(""); setMessage("");
    try {
      await request("/api/lms/development/" + encodeURIComponent(planId) + "/feedback", "POST", {
        rating: rating ? Number(rating) : null,
        strengths: strengths.trim() || null,
        feedback: feedback.trim(),
        next_steps: nextSteps.trim() || null,
      });
      setRating(""); setStrengths(""); setFeedback(""); setNextSteps("");
      setProgress(await request<Progress>("/api/lms/development/" + encodeURIComponent(planId) + "/progress"));
      setMessage("Reviewer feedback saved and audited.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Feedback could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  const milestones = progress?.milestones ?? [];
  const completedMilestones = milestones.filter(item => item.status === "completed").length;

  return (
    <div className="section-stack">
      <section className="data-panel">
        <div className="section-heading compact">
          <div><span className="eyebrow">{organizationWide ? "Authorized workforce scope" : "Authorized direct-report scope"}</span><h2>{organizationWide ? "Choose an employee" : "Choose a direct report"}</h2><p>{organizationWide ? "This role has workforce-wide development responsibility. Only the first page of active employee records matching the server-side search is loaded." : "Only employees who report directly to you are listed. The wider tenant directory is not queried."}</p></div>
          <UserRound size={18} />
        </div>
        <div className="form-grid">
          <label className="form-field"><span>Team member</span>
            <select value={memberId} onChange={event => setMemberId(event.target.value)}>
              {members.map(item => <option key={item.id} value={item.id}>{[item.first_name, item.last_name].filter(Boolean).join(" ")} · {item.job_title || item.email}</option>)}
            </select>
          </label>
          <label className="form-field"><span>Development plan</span>
            <select value={planId} disabled={loadingPlans || !plans.length} onChange={event => setPlanId(event.target.value)}>
              {plans.map(item => <option key={item.id} value={item.id}>{item.title} · {item.status.replaceAll("_", " ")}</option>)}
            </select>
          </label>
          <div className="form-actions"><button className="button button-secondary" type="button" disabled={!memberId || loadingPlans || busy} onClick={() => void refresh()}><RefreshCw size={14} /> Refresh record</button></div>
        </div>
        {selectedMember && <p className="form-help">Selected employee: <strong>{[selectedMember.first_name, selectedMember.last_name].filter(Boolean).join(" ")}</strong> · {selectedMember.job_title || selectedMember.email}</p>}
        {!members.length && <div className="empty-state"><UserRound size={24} /><p>{organizationWide ? "No active employees matched this search." : "No direct reports are assigned to your account."}</p><small>{organizationWide ? "Adjust the search to locate an employee." : "Ask People Operations to confirm your reporting line in the organization structure."}</small></div>}
        {!!memberId && !loadingPlans && !plans.length && <div className="empty-state"><ClipboardList size={24} /><p>No development plan has been created for this employee yet.</p><small>The employee can create their personal plan from My Development.</small></div>}
      </section>

      {error && <div className="form-error" role="alert">{error}</div>}
      {message && <div className="form-success" role="status"><CheckCircle2 size={15} />{message}</div>}

      {selectedPlan && <section className="data-panel">
        <div className="section-heading compact">
          <div><span className="eyebrow">Read-only plan goals</span><h2>{selectedPlan.title}</h2><p>The employee owns their plan goals. Managers and HRBPs add milestones and reviewer feedback without editing the employee's goal statements.</p></div>
          <StatusBadge status={selectedPlan.status} />
        </div>
        <div className="compact-list">
          {selectedPlan.goals.map((goal, index) => <div className="compact-row" key={index}>
            <div><strong>{goal.title}</strong><small>{goal.status.replaceAll("_", " ")} · Due {formatDate(goal.target_date)}</small>{goal.notes && <small>{goal.notes}</small>}</div>
          </div>)}
          {!selectedPlan.goals.length && <div className="empty-state"><p>This plan has no goals yet.</p></div>}
        </div>
      </section>}

      {selectedPlan && <section className="two-column">
        <section className="data-panel">
          <div className="section-heading compact"><div><span className="eyebrow">Execution checkpoints</span><h2>Manager milestones</h2></div><span className="section-meta">{completedMilestones}/{milestones.length} completed</span></div>
          {loadingProgress ? <p className="muted">Loading plan progress…</p> : <div className="compact-list">
            {milestones.map(item => <div className="compact-row" key={item.id}>
              <div><strong>{item.title}</strong><small>{item.description || "Milestone"} · Due {formatDate(item.due_at)}</small></div>
              <div className="section-actions"><StatusBadge status={item.status} />{item.status === "completed" ? <button className="button button-secondary" type="button" disabled={busy} onClick={() => void updateMilestone(item, "in_progress")}>Reopen</button> : <button className="button button-secondary" type="button" disabled={busy} onClick={() => void updateMilestone(item, "completed")}>Complete</button>}</div>
            </div>)}
            {!milestones.length && <div className="empty-state"><CalendarDays size={22} /><p>No milestones have been set for this plan.</p></div>}
          </div>}
          <form className="studio-form" onSubmit={addMilestone}>
            <h3>Add a milestone</h3>
            <label className="form-field"><span>Milestone title</span><input value={milestoneTitle} onChange={event => setMilestoneTitle(event.target.value)} required minLength={2} maxLength={240} placeholder="e.g. Complete two coached practice sessions" /></label>
            <label className="form-field"><span>Expected outcome / evidence</span><textarea rows={3} value={milestoneDescription} onChange={event => setMilestoneDescription(event.target.value)} maxLength={3000} /></label>
            <label className="form-field"><span>Due date</span><input type="date" value={milestoneDue} onChange={event => setMilestoneDue(event.target.value)} /></label>
            <button className="button button-primary" type="submit" disabled={busy || !milestoneTitle.trim()}><Plus size={14} /> Add milestone</button>
          </form>
        </section>
        <section className="data-panel">
          <div className="section-heading compact"><div><span className="eyebrow">Manager / HRBP review</span><h2>Reviewer feedback</h2></div><MessageSquare size={18} /></div>
          <form className="studio-form" onSubmit={submitFeedback}>
            <label className="form-field"><span>Rating (optional)</span><select value={rating} onChange={event => setRating(event.target.value)}><option value="">No rating</option><option value="1">1 · Needs significant support</option><option value="2">2 · Developing</option><option value="3">3 · On track</option><option value="4">4 · Strong progress</option><option value="5">5 · Exceeds expectations</option></select></label>
            <label className="form-field"><span>Strengths observed</span><textarea rows={2} value={strengths} onChange={event => setStrengths(event.target.value)} maxLength={3000} /></label>
            <label className="form-field"><span>Feedback</span><textarea rows={4} value={feedback} onChange={event => setFeedback(event.target.value)} required minLength={2} maxLength={5000} /></label>
            <label className="form-field"><span>Agreed next steps</span><textarea rows={3} value={nextSteps} onChange={event => setNextSteps(event.target.value)} maxLength={3000} /></label>
            <button className="button button-primary" type="submit" disabled={busy || feedback.trim().length < 2}>Save reviewer feedback</button>
          </form>
          <div className="compact-list">
            {(progress?.feedback ?? []).map(item => <article className="compact-row" key={item.id}>
              <div><strong>Reviewer feedback {item.rating ? "· " + item.rating + "/5" : ""}</strong><small>{item.reviewer} · {new Date(item.created_at).toLocaleString()}</small><p>{item.feedback}</p>{item.strengths && <small>Strengths: {item.strengths}</small>}{item.next_steps && <small>Next steps: {item.next_steps}</small>}</div>
            </article>)}
            {!progress?.feedback.length && <div className="empty-state"><MessageSquare size={22} /><p>No reviewer feedback has been recorded.</p></div>}
          </div>
        </section>
      </section>}
    </div>
  );
}
