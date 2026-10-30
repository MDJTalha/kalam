import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { DataTable, EmptyState, SectionCard, StatusBadge } from "@/components/ui";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type TenantRow = {
  id: string;
  name: string;
  slug: string;
  status: string;
  user_count: number;
  created_at: string;
  crm_account_id?: string | null;
  crm_account_name?: string | null;
  lifecycle_stage?: string | null;
};

export default async function SaaSTenantsPage() {
  const user = await requireUser<{ roles?: Array<{ name: string }> }>();
  const roleNames = (user.roles ?? []).map((role) => role.name.trim().toLowerCase());
  const readOnly = roleNames.some((role) => ["saas owner", "sales viewer"].includes(role));
  const tenantsResult = await apiJsonResult<TenantRow[]>("/api/v1/saas/crm/tenants");
  if (tenantsResult.status === 403) {
    return <DashboardShell title="Client portfolio" eyebrow="SaaS CRM"><EmptyState title="Client portfolio access is restricted" description="This page requires authorized commercial CRM access." /></DashboardShell>;
  }
  if (!tenantsResult.ok || tenantsResult.data === null) {
    return <DashboardShell title="Client portfolio" eyebrow="SaaS CRM"><EmptyState title="Client portfolio unavailable" description={tenantsResult.status === 0 ? "The API service could not be reached. Try again when it is available." : `Client portfolio could not be loaded (HTTP ${tenantsResult.status}). Refresh or contact an administrator if the problem continues.`} /></DashboardShell>;
  }

  const tenants = tenantsResult.data;
  return (
    <DashboardShell title="Client portfolio" eyebrow="SaaS commercial workspace" breadcrumbs={[{ label: "Commercial CRM", href: "/dashboard/saas" }, { label: "Client portfolio" }]}>
      <SaaSCrmNav readOnly={readOnly} />
      <SectionCard eyebrow="Commercial client portfolio" title="Customer organizations" meta={`${tenants.length} linked workspaces`}>
        <p className="muted">This view is for commercial relationship and customer lifecycle oversight. Technical tenant controls and customer support access are managed separately in Platform Operations.</p>
        <DataTable
          columns={["Customer", "CRM account", "Lifecycle", "Users", "Created", "Workspace status"]}
          empty={<EmptyState title="No customer tenants provisioned" description="Customer workspaces appear here after the approved provisioning process." />}
          rows={tenants.map((tenant) => [
            <span key="tenant"><strong>{tenant.name}</strong><small>{tenant.slug}</small></span>,
            <span key="account">{tenant.crm_account_name || "Not linked"}</span>,
            tenant.lifecycle_stage ? <StatusBadge key="lifecycle" status={tenant.lifecycle_stage} /> : <span key="lifecycle">—</span>,
            <span key="users">{tenant.user_count}</span>,
            <span key="created">{new Date(tenant.created_at).toLocaleDateString()}</span>,
            <StatusBadge key="status" status={tenant.status} />,
          ])}
        />
      </SectionCard>
    </DashboardShell>
  );
}
