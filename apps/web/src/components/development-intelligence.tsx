"use client";

import { useMemo, useState } from "react";
import { BrainCircuit, CheckCircle2, RefreshCcw } from "lucide-react";

type Recommendation = {
  id: string; capability_gap_id: string; intervention_type: string; source_type: string;
  title: string; rationale: string; score: number; priority: string; timeframe_days: number;
  status: string; metadata: Record<string, unknown>; recommendation_version: string;
};

const pretty = (value: string) => value.replaceAll("_", " ");
const metaText = (value: unknown, fallback = "Not available") =>
  value === null || value === undefined || value === "" ? fallback : String(value);

export function DevelopmentIntelligence({ initial }: { initial: Recommendation[] }) {
  const [items, setItems] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [filter, setFilter] = useState("all");

  const visible = useMemo(
    () => filter === "all" ? items : items.filter(item => item.intervention_type === filter),
    [items, filter],
  );

  async function load() {
    setBusy(true); setError(""); setMessage("");
    try {
      const response = await fetch("/api/v1/development/recommendations?limit=100", { cache: "no-store" });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Development recommendations could not be loaded.");
      setItems(Array.isArray(data) ? data : []);
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : "Development recommendations could not be loaded.");
    } finally { setBusy(false); }
  }

  async function accept(id: string) {
    setBusy(true); setError(""); setMessage("");
    try {
      const response = await fetch("/api/v1/development/recommendations/" + id + "/accept", { method: "POST" });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Recommendation could not be accepted.");
      setItems(current => current.map(item => item.id === id ? { ...item, status: "accepted" } : item));
      setMessage("Intervention accepted and connected to the development workflow.");
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : "Recommendation could not be accepted.");
    } finally { setBusy(false); }
  }

  const filters = ["all", "learning", "coaching", "mentoring", "experiential", "evidence_building"];

  return <section className="data-panel" aria-labelledby="development-intelligence-title">
    <div className="section-heading compact">
      <div><span className="eyebrow">Intervention intelligence</span><h2 id="development-intelligence-title">Recommended development actions</h2>
        <p>Recommendations combine governed capability gaps, evidence confidence, assessment history, role context, prior learning and configured development preferences.</p>
      </div>
      <button className="button button-secondary" onClick={() => void load()} disabled={busy}><RefreshCcw size={14} />{busy ? "Refreshing…" : "Refresh"}</button>
    </div>
    <div className="section-actions" role="group" aria-label="Intervention type">
      {filters.map(value => <button key={value} type="button" className={"button " + (filter === value ? "button-primary" : "button-secondary")} onClick={() => setFilter(value)} aria-pressed={filter === value}>{pretty(value)}</button>)}
    </div>
    {error && <div className="form-error" role="alert">{error}</div>}
    {message && <div className="form-success" role="status"><CheckCircle2 size={15} />{message}</div>}
    {visible.length ? <div className="recommendation-grid">{visible.slice(0, 24).map(item => {
      const meta = item.metadata || {};
      return <article className="data-card" key={item.id}>
        <div className="section-heading compact"><div><span className="eyebrow">{pretty(item.intervention_type)} · {pretty(item.priority)} · {pretty(item.source_type)}</span><h3>{item.title}</h3></div><strong aria-label={"Recommendation score " + item.score}>{item.score.toFixed(0)}</strong></div>
        <p>{item.rationale}</p>
        <div className="compact-list">
          <div className="compact-row"><span>Role context</span><strong>{metaText(meta.role)}</strong></div>
          <div className="compact-row"><span>Gap evidence age</span><strong>{metaText(meta.evidence_age_days, "No evidence")}{meta.evidence_age_days !== undefined ? " days" : ""}</strong></div>
          <div className="compact-row"><span>Assessment history</span><strong>{metaText(meta.assessment_history_count, "0")} records</strong></div>
          <div className="compact-row"><span>Target timeframe</span><strong>{item.timeframe_days} days</strong></div>
        </div>
        <div className="card-actions"><button className="button button-primary" disabled={busy || item.status === "accepted"} onClick={() => void accept(item.id)}>{item.status === "accepted" ? "Accepted" : "Accept intervention"}</button></div>
      </article>;
    })}</div> : <div className="empty-state"><BrainCircuit size={24} /><p>No actionable capability gaps currently generate recommendations.</p><small>Recommendations are only generated from governed capability-gap data; learning completion alone does not establish capability achievement.</small></div>}
  </section>;
}
