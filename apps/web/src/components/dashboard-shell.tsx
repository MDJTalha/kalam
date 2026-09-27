import Link from "next/link";
import { Building2, ChevronRight, CircleHelp, Command, Search, ShieldCheck } from "lucide-react";
import { requireUser } from "@/lib/server-api";
import { NotificationsCenter } from "./notifications-center";
import { WorkspaceNav } from "./workspace-nav";

export async function DashboardShell({ children, title, eyebrow = "Kognivon Learning Intelligence", breadcrumbs = [] }: { children: React.ReactNode; title: string; eyebrow?: string; breadcrumbs?: Array<{ label: string; href?: string }> }) {
  const user = await requireUser<{ first_name: string; last_name: string; email: string; roles?: Array<{ name: string }>; permissions?: string[] }>();
  const roles = user?.roles?.map((item) => item.name) ?? [];
  const permissions = user?.permissions ?? [];
  const initials = `${user?.first_name?.[0] ?? "A"}${user?.last_name?.[0] ?? "I"}`.toUpperCase();

  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Skip to main content</a>
    <aside className="sidebar">
      <div className="brand-lockup"><span className="brand-mark"><ShieldCheck size={18}/></span><div><strong>Kognivon</strong><small>Learning intelligence</small></div></div>
      <WorkspaceNav roles={roles} permissions={permissions}/>
      <div className="sidebar-footer"><div className="system-status"><i/> Secure workspace</div><small>{roles.length ? roles.join(" · ") : "Enterprise learning platform"}</small></div>
    </aside>
    <main className="workspace" id="main-content" tabIndex={-1}>
      <header className="workspace-header">
        <div className="header-context">
          {breadcrumbs.length > 0 && <nav className="breadcrumbs" aria-label="Breadcrumb">{breadcrumbs.map((item, index) => <span key={`${item.label}-${index}`}>{index > 0 && <ChevronRight size={11} aria-hidden="true"/>} {item.href ? <Link href={item.href}>{item.label}</Link> : <strong aria-current="page">{item.label}</strong>}</span>)}</nav>}
          <div className="page-title-row"><span className="eyebrow">{eyebrow}</span><h1>{title}</h1></div>
        </div>
        <div className="workspace-actions">
          <Link className="workspace-selector" href="/dashboard/organization" aria-label="Open organization workspace"><Building2 size={15}/><span>Organization</span><small>Default workspace</small></Link>
          <Link className="global-search" href="/dashboard/search" aria-label="Global search"><Search size={16}/><span>Search</span><kbd><Command size={10}/>K</kbd></Link>
          <Link className="header-icon-button" href="/dashboard/search" aria-label="Help and guidance. Open global search to find guidance and resources"><CircleHelp size={17}/></Link>
          <NotificationsCenter/>
          <Link className="profile-chip" href="/dashboard/settings" title={user ? `${user.first_name} ${user.last_name} · ${user.email}` : "Profile"} aria-label="Open profile and settings"><span>{initials}</span><div><strong>{user ? `${user.first_name} ${user.last_name}` : "Workspace user"}</strong><small>{roles[0] ?? "Administrator"}</small></div></Link>
        </div>
      </header>
      {children}
    </main>
  </div>;
}
