import { DashboardShell } from "@/components/dashboard-shell";
import { GovernedAIWorkspace } from "@/components/governed-ai-workspace";
import { apiJsonResult, requireUser } from "@/lib/server-api";

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

type AITelemetry = { requests:number; allowed:number; blocked_or_failed:number; average_latency_ms:number|null; input_tokens:number; output_tokens:number; human_reviews:number };
type AIInteraction = {
  id:string; request_type:string; provider:string; model:string|null; allowed:boolean; latency_ms:number|null;
  created_at:string; source_count:number; review:{decision:string;notes:string|null;reviewed_at:string}|null;
};

export default async function AIPage() {
  const user = await requireUser<{ permissions?: string[] }>();
  const canManage = user.permissions?.includes("ai.manage") ?? false;
  const [statusResult, telemetryResult, interactionResult] = await Promise.all([
    apiJsonResult<AIStatus>("/api/v1/ai/status"),
    canManage ? apiJsonResult<AITelemetry>("/api/v1/ai/admin/telemetry") : Promise.resolve(null),
    canManage ? apiJsonResult<{ interactions: AIInteraction[] }>("/api/v1/ai/admin/interactions") : Promise.resolve(null),
  ]);
  const [providersResult, modelsResult, policyResult] = canManage
    ? await Promise.all([
      apiJsonResult<{ providers: AIProvider[] }>("/api/v1/ai/admin/providers"),
      apiJsonResult<{ models: AIModel[] }>("/api/v1/ai/admin/models"),
      apiJsonResult<AIPolicy>("/api/v1/ai/admin/policy"),
    ])
    : [null, null, null];
  const governanceDataUnavailable = canManage && [telemetryResult, interactionResult].some((result) => result !== null && !result.ok);
  const configurationDataUnavailable = canManage && [providersResult, modelsResult, policyResult].some((result) => result !== null && !result.ok);
  if (!statusResult.ok) {
    const restricted = statusResult.status === 403;
    const serviceFailure = statusResult.status >= 500;
    return <DashboardShell title="Kalam AI" eyebrow="Enterprise workforce intelligence"><section className="data-panel" role="alert"><h2>{restricted ? "Kalam AI access restricted" : serviceFailure ? "Kalam AI service unavailable" : "Kalam AI status could not be loaded"}</h2><p>{restricted ? "Your role does not have access to Kalam AI." : serviceFailure ? "The AI service did not respond successfully. Configuration is not being inferred from an empty response." : statusResult.error || "The AI service status could not be confirmed."}</p></section></DashboardShell>;
  }
  const status = statusResult.data;
  if (!status) return <DashboardShell title="Kalam AI" eyebrow="Enterprise workforce intelligence"><section className="data-panel" role="alert"><h2>Kalam AI status unavailable</h2><p>The service returned no usable status payload.</p></section></DashboardShell>;

  return (
    <DashboardShell title="Kalam AI" eyebrow="Enterprise workforce intelligence">
      {canManage && (governanceDataUnavailable || configurationDataUnavailable) && <section className="data-panel" role="alert"><h2>Some Kalam AI administration data is unavailable</h2><p>{configurationDataUnavailable ? "Provider, model or tenant-policy configuration could not be confirmed. Kalam is not presenting missing configuration as an empty state; retry after the AI service and database are healthy." : (telemetryResult?.status === 403 || interactionResult?.status === 403) ? "Your role cannot access one or more governance datasets." : (telemetryResult?.status && telemetryResult.status >= 500) || (interactionResult?.status && interactionResult.status >= 500) ? "The AI governance service is unavailable for one or more datasets. Missing data is not shown as zero." : "Telemetry or interaction history could not be loaded. Review it again before making an administrative decision."}</p></section>}
      <GovernedAIWorkspace
        initialStatus={status}
        canManage={canManage}
        initialTelemetry={telemetryResult?.data ?? null}
        initialInteractions={interactionResult?.data?.interactions ?? []}
        initialProviders={providersResult?.data?.providers ?? []}
        initialModels={modelsResult?.data?.models ?? []}
        initialPolicy={policyResult?.data ?? null}
      />
    </DashboardShell>
  );
}
