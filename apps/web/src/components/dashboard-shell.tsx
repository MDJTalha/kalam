import Link from "next/link";
import { Building2, ChevronRight, Search } from "lucide-react";
import { apiJson, requireUser } from "@/lib/server-api";
import { AccountMenu } from "./account-menu";
import { NotificationsCenter } from "./notifications-center";
import { WorkspaceNav } from "./workspace-nav";
import { KalamBrand } from "./kalam-brand";
import { GlobalSearchShortcut } from "./global-search-shortcut";
import { SupportModeBanner } from "./saas-crm-forms";

export async function DashboardShell({ children, title, eyebrow = "Kalam Enterprise Workforce Capability", breadcrumbs = [] }: { children: React.ReactNode; title: string; eyebrow?: string; breadcrumbs?: Array<{ label: string; href?: string }> }) {
  const user = await requireUser<{ first_name: string; last_name: string; email: string; roles?: Array<{ name: string }>; permissions?: string[]; preferences?: { preferred_name?: string | null; density?: string; reduce_motion?: boolean } }>();
  const roles = user?.roles?.map((item) => item.name) ?? [];
  const permissions = user?.permissions ?? [];
  const support = roles.some((role) => role.toLowerCase() === "platform developer")
    ? await apiJson<{active:boolean;tenant_name?:string;expires_at?:string}>("/api/v1/support/developer/support/current")
    : null;
  const preferredName = user?.preferences?.preferred_name?.trim() || user?.first_name || "Account";
  const initials = `${preferredName[0] ?? "A"}${user?.last_name?.[0] ?? "I"}`.toUpperCase();
  const preferenceClasses = [user?.preferences?.density === "compact" ? "density-compact" : "", user?.preferences?.reduce_motion ? "motion-reduced" : ""].filter(Boolean).join(" ");

  return <div className={`app-shell ${preferenceClasses}`}>
    <GlobalSearchShortcut />
    <a className="skip-link" href="#main-content">Skip to main content</a>
    <aside className="sidebar">
      <KalamBrand dark compact className="brand-lockup" />
      <WorkspaceNav roles={roles} permissions={permissions}/>
      <div className="sidebar-footer"><div className="system-status"><i/> Kalam secure workspace</div><small>{roles.length ? roles.join(" · ") : "Enterprise Workforce Capability Platform"}</small></div>
    </aside>
    <main className="workspace" id="main-content" tabIndex={-1}>
      <header className="workspace-header">
        <div className="header-context">
          {breadcrumbs.length > 0 && <nav className="breadcrumbs" aria-label="Breadcrumb">{breadcrumbs.map((item, index) => <span key={`${item.label}-${index}`}>{index > 0 && <ChevronRight size={11} aria-hidden="true"/>} {item.href ? <Link href={item.href}>{item.label}</Link> : <strong aria-current="page">{item.label}</strong>}</span>)}</nav>}
          <div className="page-title-row"><span className="eyebrow">{eyebrow}</span><h1>{title}</h1></div>
        </div>
        <div className="workspace-actions">
          {permissions.includes("users.read") && <Link className="workspace-selector" href="/dashboard/organization" aria-label="Open organization workspace"><Building2 size={15} aria-hidden="true"/><span>Organization</span><small>Tenant workspace</small></Link>}
          <Link className="global-search" href="/dashboard/search" aria-label="Global search"><Search size={16} aria-hidden="true"/><span>Search</span></Link>
          <NotificationsCenter/>
          <AccountMenu displayName={`${preferredName} ${user?.last_name ?? ""}`.trim() || "Workspace user"} email={user?.email ?? ""} role={roles[0] ?? "Administrator"} initials={initials}/>
        </div>
      </header>
      {support?.active && support.tenant_name && support.expires_at && <SupportModeBanner tenantName={support.tenant_name} expiresAt={support.expires_at}/>}      {children}
    </main>
  </div>;
}
