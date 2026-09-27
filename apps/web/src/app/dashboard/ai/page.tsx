import { DashboardShell } from "@/components/dashboard-shell";
import { GovernedAIWorkspace } from "@/components/governed-ai-workspace";
import { apiJson, requireUser } from "@/lib/server-api";

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

type AITelemetry = { requests:number; allowed:number; blocked_or_failed:number; average_latency_ms:number|null; input_tokens:number; output_tokens:number; human_reviews:number };
type AIInteraction = {
  id:string; request_type:string; provider:string; model:string|null; allowed:boolean; latency_ms:number|null;
  created_at:string; source_count:number; review:{decision:string;notes:string|null;reviewed_at:string}|null;
};

export default async function AIPage() {
  const user = await requireUser<{ permissions?: string[] }>();
  const canManage = user.permissions?.includes("ai.manage") ?? false;
  const [status, telemetry, interactionPayload] = await Promise.all([
    apiJson<AIStatus>("/api/v1/ai/status"),
    canManage ? apiJson<AITelemetry>("/api/v1/ai/admin/telemetry") : Promise.resolve(null),
    canManage ? apiJson<{ interactions: AIInteraction[] }>("/api/v1/ai/admin/interactions") : Promise.resolve(null),
  ]);
  const fallback: AIStatus = {
    configured: false,
    provider: "Not configured",
    model: null,
    governance: { authorized_content_only: true, employment_decisioning: false, audit_logging: true, raw_prompt_storage: false, raw_response_storage: false, daily_token_budget: 0, daily_token_usage: 0 },
  };

  return (
    <DashboardShell title="Governed AI" eyebrow="Enterprise learning intelligence">
      <GovernedAIWorkspace
        initialStatus={status ?? fallback}
        canManage={canManage}
        initialTelemetry={telemetry}
        initialInteractions={interactionPayload?.interactions ?? []}
      />
    </DashboardShell>
  );
}
