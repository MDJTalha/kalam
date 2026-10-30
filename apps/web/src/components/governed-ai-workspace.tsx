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

type AIProvider = {
  id: string;
  name: string;
  provider_type: string;
  endpoint_url: string | null;
  secret_ref_configured: boolean;
  status: string;
  priority: number;
  enabled: boolean;
  capabilities: Record<string, unknown>;
  last_check_status: string | null;
  last_check_message: string | null;
};

type AIModel = {
  id: string;
  provider_id: string;
  model_key: string;
  display_name: string;
  enabled: boolean;
};

type AIPolicy = {
  id: string;
  enabled: boolean;
  require_grounding: boolean;
  employment_decisioning_allowed: boolean;
  raw_prompt_storage_allowed: boolean;
  raw_response_storage_allowed: boolean;
  max_input_chars: number;
  max_output_tokens: number;
  daily_token_budget: number;
  allowed_provider_types: string[];
};

type Props = {
  initialStatus: AIStatus;
  canManage?: boolean;
  initialTelemetry?: AITelemetry | null;
  initialInteractions?: AIInteraction[];
  initialProviders?: AIProvider[];
  initialModels?: AIModel[];
  initialPolicy?: AIPolicy | null;
};

const PROVIDER_TYPES = [
  { value: "openai_compatible", label: "OpenAI-compatible (OpenAI or gateway)" },
  { value: "anthropic", label: "Anthropic Claude" },
  { value: "ollama", label: "Ollama (local development)" },
];

export function GovernedAIWorkspace({ initialStatus, canManage = false, initialTelemetry = null, initialInteractions = [], initialProviders = [], initialModels = [], initialPolicy = null }: Props) {
  const [status] = useState(initialStatus);
  const [mode, setMode] = useState<"qa" | "summary" | "recommendation" | "skill_gap">("qa");
  const [question, setQuestion] = useState("");
  const [courseId, setCourseId] = useState("");
  const [telemetry, setTelemetry] = useState(initialTelemetry);
  const [interactions, setInteractions] = useState(initialInteractions);
  const [providers, setProviders] = useState(initialProviders);
  const [models, setModels] = useState(initialModels);
  const [policy, setPolicy] = useState<AIPolicy | null>(initialPolicy);
  const [providerName, setProviderName] = useState("");
  const [providerType, setProviderType] = useState("openai_compatible");
  const [providerEndpoint, setProviderEndpoint] = useState("https://api.openai.com");
  const [providerSecretRef, setProviderSecretRef] = useState("OPENAI_API_KEY");
  const [providerPriority, setProviderPriority] = useState(10);
  const [providerEnabled, setProviderEnabled] = useState(false);
  const [modelProviderId, setModelProviderId] = useState(initialProviders[0]?.id || "");
  const [modelKey, setModelKey] = useState("");
  const [modelDisplayName, setModelDisplayName] = useState("");
  const [modelEnabled, setModelEnabled] = useState(false);
  const [adminBusy, setAdminBusy] = useState(false);
  const [adminMessage, setAdminMessage] = useState("");
  const [adminMessageTone, setAdminMessageTone] = useState<"success" | "warning" | "danger">("warning");
  const [reviewBusy, setReviewBusy] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<AISource[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function jsonResponse(response: Response) {
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || "Kalam AI configuration request failed.");
    return payload;
  }

  async function createProvider(event: FormEvent) {
    event.preventDefault();
    setAdminBusy(true);
    setAdminMessage("");
    try {
      const payload = await jsonResponse(await fetch("/api/lms/ai/admin/providers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: providerName.trim(),
          provider_type: providerType,
          endpoint_url: providerEndpoint.trim() || null,
          secret_ref: providerSecretRef.trim() || null,
          priority: Number(providerPriority),
          enabled: providerEnabled,
          capabilities: { chat: true, grounding: true, content_assistance: true },
        }),
      }));
      setProviders((items) => [...items, payload]);
      setModelProviderId((value) => value || payload.id);
      setProviderName("");
      setAdminMessageTone("success");
      setAdminMessage("Provider saved. Run its connection test before enabling AI policy.");
    } catch (err) {
      setAdminMessageTone("danger");
      setAdminMessage(err instanceof Error ? err.message : "Provider could not be saved.");
    } finally {
      setAdminBusy(false);
    }
  }

  async function testProvider(providerId: string) {
    setAdminBusy(true);
    setAdminMessage("");
    try {
      const payload = await jsonResponse(await fetch(`/api/lms/ai/admin/providers/${providerId}/test`, { method: "POST" }));
      setProviders((items) => items.map((item) => item.id === providerId ? { ...item, status: payload.provider_status, last_check_status: "passed", last_check_message: payload.message } : item));
      setAdminMessageTone("success");
      setAdminMessage(payload.message || "Provider connection passed.");
    } catch (err) {
      setAdminMessageTone("danger");
      setAdminMessage(err instanceof Error ? err.message : "Provider connection test failed.");
    } finally {
      setAdminBusy(false);
    }
  }

  async function toggleProviderEnabled(providerId: string, enabled: boolean) {
    setAdminBusy(true);
    setAdminMessage("");
    try {
      const payload = await jsonResponse(await fetch(`/api/lms/ai/admin/providers/${providerId}/state`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled }),
      }));
      setProviders((items) => items.map((item) => item.id === providerId ? payload : item));
      setAdminMessageTone("success");
      setAdminMessage(enabled ? "Provider enabled. Enable the tenant policy only after selecting the approved model and controls." : "Provider disabled.");
    } catch (err) {
      setAdminMessageTone("danger");
      setAdminMessage(err instanceof Error ? err.message : "Provider state could not be updated.");
    } finally {
      setAdminBusy(false);
    }
  }

  async function createModel(event: FormEvent) {
    event.preventDefault();
    setAdminBusy(true);
    setAdminMessage("");
    try {
      const payload = await jsonResponse(await fetch("/api/lms/ai/admin/models", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider_id: modelProviderId,
          model_key: modelKey.trim(),
          display_name: modelDisplayName.trim(),
          capabilities: { chat: true, grounding: true },
          limits: { max_output_tokens: policy?.max_output_tokens || 1200 },
          enabled: modelEnabled,
        }),
      }));
      setModels((items) => [...items.filter((item) => !(modelEnabled && item.provider_id === payload.provider_id)), payload]);
      setModelKey("");
      setModelDisplayName("");
      setAdminMessageTone("success");
      setAdminMessage("Model saved. Enable the governance policy only after the provider and model are ready.");
    } catch (err) {
      setAdminMessageTone("danger");
      setAdminMessage(err instanceof Error ? err.message : "Model could not be saved.");
    } finally {
      setAdminBusy(false);
    }
  }

  async function savePolicy(event: FormEvent) {
    event.preventDefault();
    if (!policy) return;
    setAdminBusy(true);
    setAdminMessage("");
    try {
      const payload = await jsonResponse(await fetch("/api/lms/ai/admin/policy", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(policy),
      }));
      setPolicy(payload);
      setAdminMessageTone("success");
      setAdminMessage(payload.enabled ? "AI policy enabled. Confirm provider status and model readiness before user rollout." : "AI policy saved disabled.");
    } catch (err) {
      setAdminMessageTone("danger");
      setAdminMessage(err instanceof Error ? err.message : "AI policy could not be saved.");
    } finally {
      setAdminBusy(false);
    }
  }

  function toggleProviderType(providerTypeToToggle: string) {
    setPolicy((value) => value ? {
      ...value,
      allowed_provider_types: value.allowed_provider_types.includes(providerTypeToToggle)
        ? value.allowed_provider_types.filter((item) => item !== providerTypeToToggle)
        : [...value.allowed_provider_types, providerTypeToToggle],
    } : value);
  }

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

  async function refreshGovernance() {
    setAdminBusy(true);
    setAdminMessage("");
    try {
      const response = await fetch("/api/lms/ai/admin/telemetry", { cache: "no-store" });
      const payload = await jsonResponse(response);
      setTelemetry(payload);
      setAdminMessageTone("success");
      setAdminMessage("Governance telemetry refreshed from the server.");
    } catch (err) {
      setAdminMessageTone("danger");
      setAdminMessage(err instanceof Error ? err.message : "Governance telemetry could not be refreshed.");
    } finally {
      setAdminBusy(false);
    }
  }

  async function reviewInteraction(interactionId: string, decision: "approved" | "rejected" | "needs_followup") {
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

      {canManage && policy ? (
        <section className="data-panel">
          <div className="section-heading compact">
            <div><span className="eyebrow">Deployment configuration</span><h2>Connect and govern an AI provider</h2><p>Credentials remain in the deployment secret store; Kalam stores only the environment-variable reference.</p></div>
            <ShieldCheck size={22} aria-hidden="true" />
          </div>
          {adminMessage ? <StateMessage tone={adminMessageTone} title={adminMessageTone === "success" ? "AI configuration updated" : adminMessageTone === "danger" ? "AI configuration failed" : "AI configuration update"}>{adminMessage}</StateMessage> : null}
          <div className="form-grid">
            <form className="soft-panel stack-md" onSubmit={createProvider}>
              <strong>Register provider</strong>
              <label className="form-field"><span>Name</span><input value={providerName} onChange={(event) => setProviderName(event.target.value)} placeholder="Production OpenAI" required /></label>
              <label className="form-field"><span>Provider type</span><select value={providerType} onChange={(event) => setProviderType(event.target.value)}>{PROVIDER_TYPES.map((item) => <option value={item.value} key={item.value}>{item.label}</option>)}</select></label>
              <label className="form-field"><span>Endpoint URL</span><input type="url" value={providerEndpoint} onChange={(event) => setProviderEndpoint(event.target.value)} placeholder="https://api.openai.com" required={providerType !== "ollama"} /><small>Use the provider base URL; OpenAI-compatible endpoints may include /v1.</small></label>
              <label className="form-field"><span>Secret reference</span><input value={providerSecretRef} onChange={(event) => setProviderSecretRef(event.target.value.toUpperCase())} placeholder="OPENAI_API_KEY" /><small>Only OPENAI_API_KEY at api.openai.com or ANTHROPIC_API_KEY at api.anthropic.com is accepted. Credentials are deployment-managed; tenant-isolated secret-vault integration is still required for separate customer keys.</small></label>
              <div className="form-grid">
                <label className="form-field"><span>Priority</span><input type="number" min={0} max={1000} value={providerPriority} onChange={(event) => setProviderPriority(Number(event.target.value))} /></label>
                <label className="form-field"><span>Initial state</span><select value={providerEnabled ? "enabled" : "disabled"} onChange={(event) => setProviderEnabled(event.target.value === "enabled")}><option value="disabled">Disabled until tested</option><option value="enabled">Enabled</option></select></label>
              </div>
              <button className="button button-primary" type="submit" disabled={adminBusy || providerName.trim().length < 2}>Save provider</button>
            </form>

            <form className="soft-panel stack-md" onSubmit={createModel}>
              <strong>Register model</strong>
              <label className="form-field"><span>Provider</span><select value={modelProviderId} onChange={(event) => setModelProviderId(event.target.value)} required><option value="">Select a provider</option>{providers.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>
              <label className="form-field"><span>Model or deployment key</span><input value={modelKey} onChange={(event) => setModelKey(event.target.value)} placeholder="gpt-4o-mini or claude-sonnet-4-5" required /></label>
              <label className="form-field"><span>Display name</span><input value={modelDisplayName} onChange={(event) => setModelDisplayName(event.target.value)} placeholder="Production reasoning model" required /></label>
              <label className="form-field"><span>Initial state</span><select value={modelEnabled ? "enabled" : "disabled"} onChange={(event) => setModelEnabled(event.target.value === "enabled")}><option value="disabled">Disabled until provider passes</option><option value="enabled">Enabled after provider passes</option></select></label>
              <button className="button button-primary" type="submit" disabled={adminBusy || !modelProviderId || !modelKey.trim() || !modelDisplayName.trim()}>Save model</button>
            </form>
          </div>

          <div className="two-column" style={{ marginTop: 14 }}>
            <div className="soft-panel">
              <strong>Registered providers</strong>
              <div className="compact-list">
                {providers.map((item) => <div className="compact-row" key={item.id}><div><strong>{item.name}</strong><small>{item.provider_type} · {item.endpoint_url || "managed endpoint"} · {item.enabled ? "Enabled" : "Disabled"} · {item.status}</small><small>{item.last_check_message || (item.secret_ref_configured ? "Secret reference configured" : "No secret reference configured")}</small></div><div className="button-row"><button className="button button-secondary" type="button" disabled={adminBusy} onClick={() => void testProvider(item.id)}>Test</button><button className="button button-secondary" type="button" disabled={adminBusy || (!item.enabled && item.status !== "ready")} onClick={() => void toggleProviderEnabled(item.id, !item.enabled)}>{item.enabled ? "Disable" : "Enable"}</button></div></div>)}
                {!providers.length ? <span className="muted-text">No provider registered.</span> : null}
              </div>
            </div>
            <div className="soft-panel">
              <strong>Registered models</strong>
              <div className="compact-list">
                {models.map((item) => <div className="compact-row" key={item.id}><div><strong>{item.display_name}</strong><small>{item.model_key} · {item.enabled ? "Enabled" : "Disabled"}</small></div></div>)}
                {!models.length ? <span className="muted-text">No model registered.</span> : null}
              </div>
            </div>
          </div>

          <form className="soft-panel stack-md" style={{ marginTop: 14 }} onSubmit={savePolicy}>
            <div><strong>Tenant AI policy</strong><small className="muted-text">Enable this only after the provider connection test and model registration pass.</small></div>
            <div className="form-grid">
              <label className="form-field"><span>Policy state</span><select value={policy.enabled ? "enabled" : "disabled"} onChange={(event) => setPolicy({ ...policy, enabled: event.target.value === "enabled" })}><option value="disabled">Disabled</option><option value="enabled">Enabled</option></select></label>
              <label className="form-field"><span>Daily token budget (0 = unlimited)</span><input type="number" min={0} max={100000000} value={policy.daily_token_budget} onChange={(event) => setPolicy({ ...policy, daily_token_budget: Number(event.target.value) })} /></label>
              <label className="form-field"><span>Max input characters</span><input type="number" min={100} max={20000} value={policy.max_input_chars} onChange={(event) => setPolicy({ ...policy, max_input_chars: Number(event.target.value) })} /></label>
              <label className="form-field"><span>Max output tokens</span><input type="number" min={64} max={8192} value={policy.max_output_tokens} onChange={(event) => setPolicy({ ...policy, max_output_tokens: Number(event.target.value) })} /></label>
            </div>
            <div className="button-row">
              <label><input type="checkbox" checked={policy.require_grounding} onChange={(event) => setPolicy({ ...policy, require_grounding: event.target.checked })} /> Require evidence grounding</label>
              <label><input type="checkbox" checked={policy.employment_decisioning_allowed} onChange={(event) => setPolicy({ ...policy, employment_decisioning_allowed: event.target.checked })} /> Allow employment decisioning</label>
            </div>
            <div className="button-row"><span className="muted-text">Allowed providers:</span>{PROVIDER_TYPES.map((item) => <label key={item.value}><input type="checkbox" checked={policy.allowed_provider_types.includes(item.value)} onChange={() => toggleProviderType(item.value)} /> {item.value === "openai_compatible" ? "OpenAI-compatible" : item.value === "anthropic" ? "Claude" : "Ollama"}</label>)}</div>
            <button className="button button-primary" type="submit" disabled={adminBusy}>Save tenant policy</button>
          </form>
        </section>
      ) : null}

      {canManage ? (
        <section className="data-panel">
          <div className="section-heading compact">
            <div><span className="eyebrow">Kalam AI governance</span><h2>Governance &amp; oversight</h2></div>
            <div className="button-row"><button className="button button-secondary" type="button" disabled={adminBusy} onClick={() => void refreshGovernance()}>{adminBusy ? "Refreshing..." : "Refresh telemetry"}</button><ShieldCheck size={22} aria-hidden="true" /></div>
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
                  <button className="button button-secondary" type="button" disabled={reviewBusy === item.id} onClick={() => reviewInteraction(item.id, "rejected")}>Reject</button><button className="button button-secondary" type="button" disabled={reviewBusy === item.id} onClick={() => reviewInteraction(item.id, "needs_followup")}>Follow up</button>
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
