"use client";

import { useState } from "react";
import { BrainCircuit, Send, ShieldCheck } from "lucide-react";
import { StateMessage } from "@/components/ui";

type Source = { citation_id: string; course_title: string; lesson_title: string; chunk_index: number };

type Props = {
  title: string;
  description: string;
  question: string;
  mode?: "qa" | "summary" | "recommendation" | "skill_gap";
};

export function GovernedAIAction({ title, description, question, mode = "skill_gap" }: Props) {
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [error, setError] = useState("");

  async function run() {
    setLoading(true); setError(""); setAnswer(""); setSources([]);
    try {
      const response = await fetch("/api/lms/ai/query", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, mode }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "Governed AI request failed.");
      setAnswer(payload.answer || "No grounded explanation was returned.");
      setSources(payload.sources || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Governed AI request failed.");
    } finally { setLoading(false); }
  }

  return (
    <section className="data-panel governed-ai-action">
      <div className="section-heading compact">
        <div><span className="eyebrow">Governed intelligence</span><h2>{title}</h2><p>{description}</p></div>
        <BrainCircuit size={22} aria-hidden="true" />
      </div>
      <div className="governed-ai-trust"><span><ShieldCheck size={13} /> Evidence grounded</span><span>Authorized learner context</span><span>Audited interaction</span></div>
      <button className="button button-primary" type="button" onClick={() => void run()} disabled={loading}>
        <Send size={14} />{loading ? "Generating grounded explanation…" : "Explain with Kalam AI"}
      </button>
      {error ? <StateMessage tone="danger" title="Kalam AI unavailable">{error}</StateMessage> : null}
      {answer ? <div className="governed-ai-answer" aria-live="polite"><p>{answer}</p>{sources.length ? <div className="governed-ai-sources"><strong>Evidence used</strong>{sources.map(source => <span key={source.citation_id + source.chunk_index}>[{source.citation_id}] {source.lesson_title} · {source.course_title}</span>)}</div> : null}</div> : null}
    </section>
  );
}
