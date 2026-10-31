import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { SaaSRoleManagement } from "@/components/saas-role-management";
import { EmptyState } from "@/components/ui";
import { apiJson, requireUser } from "@/lib/server-api";

type TenantOption = { id: string; name: string; slug: string; status: string };
type PermissionOption = { id: string; key: string; description?: string | null };
type CurrentUser = { permissions?: string[] };

export default async function SaaSRolesPage() {
  const currentUser = await requireUser<CurrentUser>();
  if (!(currentUser.permissions ?? []).includes("saas.roles.manage")) {
    return (
      <DashboardShell title="Tenant Role Management" eyebrow="SaaS governance">
        <EmptyState
          title="SaaS Super Admin access required"
          description="Only authorized SaaS Super Admins and Platform Developers can create or govern customer-tenant roles."
        />
      </DashboardShell>
    );
  }

  const [tenants, permissions] = await Promise.all([
    apiJson<TenantOption[]>("/api/v1/saas/crm/tenants"),
    apiJson<PermissionOption[]>("/api/v1/admin/permissions"),
  ]);

  if (!tenants || !permissions) {
    return (
      <DashboardShell title="Tenant Role Management" eyebrow="SaaS governance">
        <EmptyState
          title="Role administration data is unavailable"
          description="Verify SaaS operations access and the tenant permission catalogue, then reload this page."
        />
      </DashboardShell>
    );
  }

  return (
    <DashboardShell
      title="Tenant Role Management"
      eyebrow="SaaS governance"
      breadcrumbs={[
        { label: "SaaS Operations", href: "/dashboard/saas" },
        { label: "Tenant Role Management" },
      ]}
    >
      <SaaSCrmNav />
      <SaaSRoleManagement tenants={tenants} permissions={permissions} />
    </DashboardShell>
  );
}
