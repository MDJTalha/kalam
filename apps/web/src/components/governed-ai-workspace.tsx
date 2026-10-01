"use client";

import { FormEvent, useState } from "react";
import { BrainCircuit, Send, ShieldCheck } from "lucide-react";
import { StateMessage } from "@/components/ui";

type AIStatus = {
  configured: boolean;
  provider: string;
  model: string | null;
  governance: {
    authorized_content_only: boolean;
    employment_decisioning: boolean;
    audit_logging: boolean;
    raw_prompt_storage: boolean;
    raw_response_storage: boolean;
    daily_token_budget: number;
    daily_token_usage: number;
  };
};

type AISource = {
  citation_id: string;
  lesson_id: string;
  course_id: string;
  course_title: string;
  lesson_title: string;
  chunk_index: number;
  score: number;
};

type AITelemetry = {
  requests: number;
  allowed: number;
  blocked_or_failed: number;
  average_latency_ms: number | null;
  input_tokens: number;
  output_tokens: number;
  human_reviews: number;
};

type AIInteraction = {
  id: string;
  request_type: string;
  provider: string;
  model: string | null;
  allowed: boolean;
  latency_ms: number | null;
  created_at: string;
  source_count: number;
  review: { decision: string; notes: string | null; reviewed_at: string } | null;
};

type Props = {
  initialStatus: AIStatus;
  canManage?: boolean;
  initialTelemetry?: AITelemetry | null;
  initialInteractions?: AIInteraction[];
};

export function GovernedAIWorkspace({ initialStatus, canManage = false, initialTelemetry = null, initialInteractions = [] }: Props) {
  const [status] = useState(initialStatus);
  const [mode, setMode] = useState<"qa" | "summary" | "recommendation" | "skill_gap">("qa");
  const [question, setQuestion] = useState("");
  const [courseId, setCourseId] = useState("");
  const [telemetry, setTelemetry] = useState(initialTelemetry);
  const [interactions, setInteractions] = useState(initialInteractions);
  const [reviewBusy, setReviewBusy] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<AISource[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function ask(event: FormEvent) {
    event.preventDefault();
    if (question.trim().length < 3) return;
    setLoading(true);
    setError("");
    setAnswer("");
    setSources([]);
    try {
      const response = await fetch("/api/lms/ai/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question.trim(), course_id: courseId.trim() || null, mode }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Governed AI request failed.");
      setAnswer(payload.answer || "");
      setSources(payload.sources || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Governed AI request failed.");
    } finally {
      setLoading(false);
    }
  }

  async function reviewInteraction(interactionId: string, decision: "approved" | "rejected") {
    setReviewBusy(interactionId);
    setError("");
    try {
      const response = await fetch(`/api/lms/ai/admin/interactions/${interactionId}/review`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "AI review update failed.");
      setInteractions((items) => items.map((item) => item.id === interactionId ? { ...item, review: { decision: payload.decision, notes: payload.notes, reviewed_at: payload.reviewed_at } } : item));
      setTelemetry((value) => value ? { ...value, human_reviews: value.human_reviews + (interactions.find((item) => item.id === interactionId)?.review ? 0 : 1) } : value);
    } catch (err) {
      setError(err instanceof Error ? err.message : "AI review update failed.");
    } finally {
      setReviewBusy("");
    }
  }

  return (
    <div className="stack-lg">
      <section className="data-panel">
        <div className="section-heading">
          <div>
            <span className="eyebrow">Kalam AI · Governed intelligence</span>
            <h2>Workforce intelligence, governed by design</h2>
            <p>Kalam AI answers from authorized learning content, respects tenant access boundaries, and keeps AI activity auditable.</p>
          </div>
          <BrainCircuit size={28} aria-hidden="true" />
        </div>
        <div className="metric-grid">
          <div className="metric-card"><span>Provider</span><strong>{status.provider}</strong></div>
          <div className="metric-card"><span>Model</span><strong>{status.model || "Not configured"}</strong></div>
          <div className="metric-card"><span>Grounding</span><strong>Authorized content only</strong></div>
          <div className="metric-card"><span>Audit</span><strong>{status.governance.audit_logging ? "Enabled" : "Disabled"}</strong></div>
        </div>
        <div className="ai-trust-strip" aria-label="Kalam AI governance safeguards">
          <span><ShieldCheck size={14} aria-hidden="true"/> Authorized content only</span><span>Tenant access rules apply</span><span>Evidence grounded</span><span>Activity audited</span>
        </div>
        {!status.configured ? <StateMessage tone="warning" title="Kalam AI is not configured">An administrator must enable a ready governed provider, model, and tenant AI policy before generation is available.</StateMessage> : null}
      </section>

      {canManage ? (
        <section className="data-panel">
          <div className="section-heading compact">
            <div><span className="eyebrow">Kalam AI governance</span><h2>Governance &amp; oversight</h2></div>
            <ShieldCheck size={22} aria-hidden="true" />
          </div>
          {telemetry ? <div className="metric-grid">
            <div className="metric-card"><span>Requests</span><strong>{telemetry.requests}</strong></div>
            <div className="metric-card"><span>Allowed</span><strong>{telemetry.allowed}</strong></div>
            <div className="metric-card"><span>Blocked / failed</span><strong>{telemetry.blocked_or_failed}</strong></div>
            <div className="metric-card"><span>Avg latency</span><strong>{telemetry.average_latency_ms ?? "—"} ms</strong></div>
            <div className="metric-card"><span>Input tokens</span><strong>{telemetry.input_tokens}</strong></div>
            <div className="metric-card"><span>Output tokens</span><strong>{telemetry.output_tokens}</strong></div>
            <div className="metric-card"><span>Human reviews</span><strong>{telemetry.human_reviews}</strong></div>
            <div className="metric-card"><span>Daily AI budget</span><strong>{status.governance.daily_token_budget > 0 ? status.governance.daily_token_usage + " / " + status.governance.daily_token_budget : "Unlimited"}</strong></div>
          </div> : null}
          <div className="compact-list">
            {interactions.slice(0, 12).map((item) => (
              <div className="compact-row" key={item.id}>
                <div>
                  <strong>{item.request_type.toUpperCase()} · {item.provider} / {item.model || "model unavailable"}</strong>
                  <small>{item.allowed ? "Allowed" : "Blocked / failed"} · {item.source_count} source(s) · {item.latency_ms ?? "—"} ms · {item.review?.decision || "Pending review"}</small>
                </div>
                <div className="button-row">
                  <button className="button button-secondary" type="button" disabled={reviewBusy === item.id} onClick={() => reviewInteraction(item.id, "approved")}>Approve</button>
                  <button className="button button-secondary" type="button" disabled={reviewBusy === item.id} onClick={() => reviewInteraction(item.id, "rejected")}>Reject</button>
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="data-panel">
        <div className="section-heading compact">
          <div><span className="eyebrow">Kalam AI workspace</span><h2>Understand your capability with governed AI</h2></div>
          <ShieldCheck size={22} aria-hidden="true" />
        </div>
        {error ? <StateMessage tone="danger" title="Kalam AI request failed">{error}</StateMessage> : null}
        <form onSubmit={ask} className="stack-md">
          <label htmlFor="ai-mode">Request type</label>
          <select id="ai-mode" value={mode} onChange={(event) => setMode(event.target.value as "qa" | "summary" | "recommendation" | "skill_gap")}>
            <option value="qa">Question & answer</option>
            <option value="summary">Grounded summary</option>
            <option value="recommendation">Learning recommendations</option>
            <option value="skill_gap">Skill-gap explanation</option>
          </select>
          <label htmlFor="ai-question">{mode === "qa" ? "Question" : "Request"}</label>
          <textarea id="ai-question" value={question} onChange={(event) => setQuestion(event.target.value)} rows={5} maxLength={4000} placeholder={mode === "qa" ? "Ask a question grounded in your enrolled courses..." : mode === "summary" ? "Describe what you want summarized from your authorized course content..." : mode === "recommendation" ? "Ask for learning options based on your persisted skill gaps..." : "Ask for an explanation of your persisted role-to-skill gaps..."} />
          <label htmlFor="ai-course">Course ID (optional)</label>
          <input id="ai-course" value={courseId} onChange={(event) => setCourseId(event.target.value)} placeholder="Limit retrieval to one enrolled course" />
          <button className="button button-primary" type="submit" disabled={loading || question.trim().length < 3}><Send size={16} />{loading ? "Kalam is thinking..." : "Ask Kalam"}</button>
        </form>
      </section>

      {answer ? (
        <section className="data-panel">
          <div className="section-heading compact"><div><span className="eyebrow">Kalam response</span><h2>Answer</h2></div></div>
          <p className="ai-response">{answer}</p>
          <div className="section-heading compact"><div><span className="eyebrow">Evidence used</span><h3>Authorized sources</h3></div></div>
          {sources.map((source) => (
            <div className="compact-row" key={`${source.lesson_id}-${source.citation_id}-${source.chunk_index}`}>
              <strong>[{source.citation_id}] {source.lesson_title}</strong>
              <span>{source.course_title} · evidence {source.chunk_index + 1}</span>
            </div>
          ))}
        </section>
      ) : null}
    </div>
  );
}
