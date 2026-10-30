import { Activity, Building2, LifeBuoy, ShieldCheck } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { PlatformIncidentWorkspace } from "@/components/platform-incident-workspace";
import { DeveloperSupportControl, DeveloperTenantStatusControl } from "@/components/saas-crm-forms";
import { DataTable, EmptyState, MetricCard, SectionCard, StatusBadge } from "@/components/ui";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type TenantRow = { id: string; name: string; slug: string; status: string };
type HealthResult = { status: string; checks: Record<string, string>; checked_at: string };
type AuditRow = { id: string; action: string; entity_type: string; entity_id: string | null; summary: string | null; created_at: string };
type IncidentRow = { id: string; incident_number: string; title: string; severity: string; status: string; impact: string | null; detected_at: string };

export default async function PlatformOperationsPage() {
  const user = await requireUser<{ roles?: Array<{ name: string }>; permissions?: string[] }>();
  const roleNames = (user.roles ?? []).map((role) => role.name.trim().toLowerCase());
  if (!roleNames.includes("platform developer") || !user.permissions?.includes("platform.tenants.read")) {
    return (
      <DashboardShell title="Platform operations" eyebrow="Kalam control centre">
        <EmptyState title="Platform operations access is restricted" description="This workspace is reserved for authorized Kalam Platform Developers." />
      </DashboardShell>
    );
  }

  const [result, healthResult, auditResult, incidentResult] = await Promise.all([
    apiJsonResult<TenantRow[]>("/api/v1/support/developer/tenants"),
    apiJsonResult<HealthResult>("/api/v1/support/developer/health"),
    apiJsonResult<AuditRow[]>("/api/v1/support/developer/audit?limit=50"),
    apiJsonResult<IncidentRow[]>("/api/v1/support/developer/incidents?limit=100"),
  ]);
  if (!result.ok || result.data === null) {
    return (
      <DashboardShell title="Platform operations" eyebrow="Kalam control centre">
        <EmptyState title="Tenant registry unavailable" description={result.status === 403 ? "Your account does not have platform tenant-read permission." : `Tenant registry could not be loaded (HTTP ${result.status}).`} />
      </DashboardShell>
    );
  }

  const tenants = result.data;
  const active = tenants.filter((tenant) => tenant.status === "active").length;
  const suspended = tenants.length - active;

  return (
    <DashboardShell title="Platform operations" eyebrow="Kalam technical control centre" breadcrumbs={[{ label: "Platform Operations" }]}>
      <div className="stat-grid">
        <MetricCard label="Customer tenants" value={tenants.length} detail="Customer workspaces in the registry" icon={Building2} />
        <MetricCard label="Active tenants" value={active} detail="Tenant authentication is enabled" icon={ShieldCheck} />
        <MetricCard label="Suspended tenants" value={suspended} detail="Access is blocked; records are retained" icon={Activity} />
        <MetricCard label="Support access" value="Audited" detail="Reasoned, time-limited support sessions" icon={LifeBuoy} />
      </div>
      <SectionCard eyebrow="Infrastructure" title="Platform service health" meta={healthResult.ok && healthResult.data ? `Checked ${new Date(healthResult.data.checked_at).toLocaleString()}` : "Health data unavailable"}>
        {healthResult.ok && healthResult.data ? (
          <div className="stat-grid">
            {Object.entries(healthResult.data.checks).map(([service, status]) => (
              <MetricCard key={service} label={service.replaceAll("_", " ")} value={status} detail="Live dependency check" icon={Activity} />
            ))}
          </div>
        ) : (
          <EmptyState title="Health status unavailable" description={healthResult.status === 403 ? "Your account does not have platform health-read permission." : `The health check could not be loaded (HTTP ${healthResult.status}).`} />
        )}
      </SectionCard>
      <SectionCard eyebrow="Incident management" title="Platform incident lifecycle" meta="SEV1–SEV4 · audited changes">
        {incidentResult.ok && incidentResult.data ? (
          <PlatformIncidentWorkspace initialIncidents={incidentResult.data} />
        ) : (
          <EmptyState title="Incident management unavailable" description={incidentResult.status === 403 ? "Your account does not have platform incident-management permission." : `Incident records could not be loaded (HTTP ${incidentResult.status}).`} />
        )}
      </SectionCard>
      <SectionCard eyebrow="Governance" title="Platform audit trail" meta="Latest 50 internal operations events">
        {auditResult.ok && auditResult.data ? (
          <DataTable
            columns={["Action", "Entity", "Summary", "Recorded"]}
            empty={<EmptyState title="No platform audit events" description="Platform operations events will appear here as they are recorded." />}
            rows={auditResult.data.map((event) => [
              <strong key="action">{event.action}</strong>,
              <span key="entity">{event.entity_type}{event.entity_id ? ` · ${event.entity_id}` : ""}</span>,
              <span key="summary">{event.summary || "—"}</span>,
              <time key="created" dateTime={event.created_at}>{new Date(event.created_at).toLocaleString()}</time>,
            ])}
          />
        ) : (
          <EmptyState title="Audit trail unavailable" description={auditResult.status === 403 ? "Your account does not have platform audit-read permission." : `The audit trail could not be loaded (HTTP ${auditResult.status}).`} />
        )}
      </SectionCard>
      <SectionCard eyebrow="Tenant lifecycle" title="Customer tenant registry" meta={`${tenants.length} workspaces`}>
        <p className="muted">Tenant suspension blocks authentication and revokes existing sessions. It does not delete customer users, training records, assessments or certificates.</p>
        <DataTable
          columns={["Customer tenant", "Organization ID", "Lifecycle", "Access control"]}
          empty={<EmptyState title="No customer tenants found" description="Customer workspaces will appear here after authorized provisioning." />}
          rows={tenants.map((tenant) => [
            <span key="name"><strong>{tenant.name}</strong></span>,
            <code key="slug">{tenant.slug}</code>,
            <StatusBadge key="status" status={tenant.status} />,
            <DeveloperTenantStatusControl key="action" id={tenant.id} status={tenant.status} />,
          ])}
        />
      </SectionCard>
      <SectionCard eyebrow="Engineering support" title="Time-limited customer support access" meta="Platform Developer only">
        <p className="muted">Enter a customer workspace only when there is a documented support reason. The session is bound to your authenticated login, expires automatically and is recorded in the audit trail.</p>
        <DeveloperSupportControl tenants={tenants} />
      </SectionCard>
    </DashboardShell>
  );
}
