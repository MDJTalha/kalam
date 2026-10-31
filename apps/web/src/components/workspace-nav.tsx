"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity, Award, BadgeCheck, BarChart3, Bell, BookOpenCheck, BrainCircuit, Building2, ChevronDown, ChevronLeft, ChevronRight,
  ClipboardCheck, CreditCard, FileText, FolderOpen, GitBranch, GraduationCap, KeyRound, Layers3, LibraryBig, LifeBuoy, LogOut, Menu,
  MessageSquare, Network, Plug, RefreshCcw, Settings2, ShieldAlert, ShieldCheck, Target, UserPlus, UserRoundCog, UsersRound, Workflow, X,
} from "lucide-react";

type Props = { roles: string[]; permissions: string[] };
type NavIcon = typeof BarChart3;
type NavItem = {
  href: string;
  label: string;
  icon: NavIcon;
  permission?: string | string[];
  exact?: boolean;
};
type NavGroup = { label: string; items: NavItem[] };

const allowed = (permissions: string[], permission?: string | string[]) =>
  !permission || (Array.isArray(permission) ? permission.some(key => permissions.includes(key)) : permissions.includes(permission));

const item = (href: string, label: string, icon: NavIcon, permission?: string, exact = false): NavItem =>
  ({ href, label, icon, permission, exact });
const baseGroups: NavGroup[] = [
  { label: "Workspace", items: [item("/dashboard", "Overview", BarChart3, undefined, true)] },
  { label: "People & Organization", items: [
    item("/dashboard/people", "People", UsersRound, "users.read", true),
    item("/dashboard/team", "Teams", UsersRound, "team.read"),
    item("/dashboard/organization", "Organization", Network, "users.read"),
    item("/dashboard/people/admin", "People Administration", UserRoundCog, "users.manage"),
  ] },
  { label: "Learning", items: [
    item("/dashboard/catalog", "Learning Catalog", LibraryBig, "learning.access"),
    item("/dashboard/learning-paths", "Learning Paths", GitBranch, "learning.access"),
    item("/dashboard/programs", "Programs & Cohorts", GraduationCap, "learning.access"),
    item("/dashboard/sessions", "Live Sessions", Activity, "learning.access"),
    item("/dashboard/course-studio", "Course Studio", BookOpenCheck, "courses.manage"),
    item("/dashboard/ld-operations", "L&D Operations", Workflow, "courses.manage"),
  ] },
  { label: "Capability", items: [
    item("/dashboard/skills", "Skills & Capabilities", Layers3, "learning.access", true),
    item("/dashboard/skills/admin", "Capability Framework", GitBranch, "skills.manage"),
    item("/dashboard/development", "My Development", Target, "learning.access"),
    item("/dashboard/development/team", "Team Development Review", UsersRound, ["team.read", "users.read"]),
    item("/dashboard/capability-gaps", "Capability Gaps", ShieldCheck, "capability_gaps.read"),
    item("/dashboard/capability-risk", "Capability Risk", ShieldAlert, "capability_risk.read"),
  ] },
  { label: "Assessment & Credentials", items: [
    item("/dashboard/assessments", "Assessments", ClipboardCheck, "learning.access", true),
    item("/dashboard/assessments/admin", "Assessment Administration", ClipboardCheck, "assessments.manage"),
    item("/dashboard/capability-assessments", "Capability Assessments", Target, "capability_assessments.read"),
    item("/dashboard/certificates", "Credentials", Award, "learning.access", true),
    item("/dashboard/certificates/admin", "Certificate Administration", BadgeCheck, "certificates.manage"),
  ] },
  { label: "Risk & Evidence", items: [
    item("/dashboard/compliance", "Compliance & Readiness", ShieldCheck, "learning.access", true),
    item("/dashboard/compliance/admin", "Compliance Operations", ShieldCheck, "compliance.manage"),
    item("/dashboard/files", "Evidence Repository", FolderOpen, "files.read"),
    item("/dashboard/evidence/admin", "Capability Evidence", FolderOpen, "evidence.read"),
  ] },
  { label: "Insights", items: [
    item("/dashboard/analytics", "Analytics", BarChart3, "reports.read"),
    item("/dashboard/reports", "Reports", FileText, "reports.read"),
    item("/dashboard/ai", "Kalam AI", BrainCircuit, "learning.access"),
  ] },
  { label: "Commercial Operations", items: [
    item("/dashboard/saas", "Commercial CRM", Building2, "saas.crm.read", true),
    item("/dashboard/saas/roles", "Tenant Role Management", KeyRound, "saas.roles.manage"),
    item("/dashboard/saas/clients", "Clients", UsersRound, "saas.crm.read"),
    item("/dashboard/saas/tenants", "Tenants", Building2, "saas.crm.read"),
    item("/dashboard/saas/pipeline", "Pipeline", Workflow, "saas.crm.read"),
    item("/dashboard/saas/pricing", "Pricing & Offers", CreditCard, "saas.crm.read"),
    item("/dashboard/saas/trials", "Trials", Activity, "saas.crm.read"),
    item("/dashboard/saas/tasks", "Tasks", ClipboardCheck, "saas.crm.read"),
    item("/dashboard/saas/forecast", "Forecast", BarChart3, "saas.crm.read"),
    item("/dashboard/saas/subscriptions", "Subscriptions", Layers3, "saas.crm.read"),
    item("/dashboard/saas/contracts", "Contracts", FileText, "saas.crm.read"),
    item("/dashboard/saas/billing", "Billing", CreditCard, "saas.crm.read"),
    item("/dashboard/saas/renewals", "Renewals", RefreshCcw, "saas.crm.read"),
    item("/dashboard/saas/onboarding", "Onboarding", UserPlus, "saas.crm.read"),
    item("/dashboard/saas/certifications", "Certifications", BadgeCheck, "saas.crm.read"),
    item("/dashboard/saas/inquiries", "Leads & Inquiries", MessageSquare, "saas.crm.read"),
    item("/dashboard/saas/team", "Sales Team", UsersRound, "saas.crm.read"),
  ] },
  { label: "Platform Administration", items: [
    item("/dashboard/admin", "Roles & Permissions", UserRoundCog, "tenant.manage"),
    item("/dashboard/admin/support", "Support Operations", LifeBuoy, "tenant.manage"),
    item("/dashboard/audit", "Audit Log", FileText, "audit.read"),
    item("/dashboard/integrations", "Integrations", Plug, "integrations.manage"),
    item("/dashboard/webhooks", "Webhooks", Network, "integrations.manage"),
  ] },
];

const accountItems: NavItem[] = [
  item("/dashboard/notifications", "Notifications", Bell),
  item("/dashboard/settings/sessions", "Active Sessions", KeyRound),
  item("/dashboard/settings", "Settings", Settings2, undefined, true),
  item("/dashboard/help", "Help & Support", LifeBuoy),
];

export function WorkspaceNav({ roles, permissions }: Props) {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sidebarMinimized, setSidebarMinimized] = useState(false);
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const navRef = useRef<HTMLElement | null>(null);
  const prefetchedRoutes = useRef<Set<string>>(new Set());
  const [navCounts, setNavCounts] = useState({ unread: 0, overdue: 0, approvals: 0 });

  useEffect(() => {
    let active = true;
    try {
      const minimized = window.localStorage.getItem("kalam.nav.minimized");
      if (minimized === "true") queueMicrotask(() => { if (active) setSidebarMinimized(true); });
      const stored = window.localStorage.getItem("kalam.nav.collapsed");
      if (stored) queueMicrotask(() => {
        if (active) setCollapsed(JSON.parse(stored) as Record<string, boolean>);
      });
    } catch { /* local storage is an enhancement only */ }
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    if (!permissions.includes("learning.access")) return () => { active = false; };
    const cacheKey = "kalam.nav.counts";
    const cacheTtl = 30_000;
    try {
      const cached = window.sessionStorage.getItem(cacheKey);
      if (cached) {
        const parsed = JSON.parse(cached) as { at?: number; counts?: { unread:number; overdue:number; approvals:number } };
        if (parsed.at && parsed.counts && Date.now() - parsed.at < cacheTtl) {
          queueMicrotask(() => { if (active) setNavCounts(parsed.counts!); });
          return () => { active = false; };
        }
      }
    } catch { /* session storage is optional */ }

    void Promise.all([
      fetch("/api/lms/notifications", { cache: "no-store" }).then((response) => response.ok ? response.json() : []),
      fetch("/api/lms/compliance/my", { cache: "no-store" }).then((response) => response.ok ? response.json() : []),
      fetch("/api/lms/courses/operations/enrollment-queue?page=1&page_size=1&status=all&q=", { cache: "no-store" }).then((response) => response.ok ? response.json() : null),
    ]).then(([notices, obligations, queue]: [unknown, unknown, unknown]) => {
      if (!active) return;
      const unread = Array.isArray(notices) ? notices.filter((notice) => notice && typeof notice === "object" && !("read_at" in notice && notice.read_at)).length : 0;
      const overdue = Array.isArray(obligations) ? obligations.filter((obligation) => obligation && typeof obligation === "object" && "due_state" in obligation && obligation.due_state === "overdue" && (!("status" in obligation) || !["completed", "excepted"].includes(String(obligation.status)))).length : 0;
      const approvals = queue && typeof queue === "object" && "pending_approval" in queue ? Number(queue.pending_approval) || 0 : 0;
      const counts = { unread, overdue, approvals };
      setNavCounts(counts);
      try { window.sessionStorage.setItem(cacheKey, JSON.stringify({ at: Date.now(), counts })); } catch { /* session storage is optional */ }
    }).catch(() => undefined);
    return () => { active = false; };
  }, [permissions]);

  const isPlatformDeveloper = roles.some((role) => role.trim().toLowerCase() === "platform developer");

  const visibleGroups = useMemo(
    () => baseGroups
      .map((group) => ({ ...group, items: group.items.filter((navItem) =>
        allowed(permissions, navItem.permission) &&
        (navItem.href !== "/dashboard/admin/support" || isPlatformDeveloper)
      ) }))
      .filter((group) => group.items.length > 0),
    [permissions, isPlatformDeveloper],
  );

  const isActive = (navItem: NavItem) =>
    navItem.exact ? pathname === navItem.href : pathname === navItem.href || pathname.startsWith(`${navItem.href}/`);

  const toggleGroup = (label: string) => {
    setCollapsed((current) => {
      const next = { ...current, [label]: !current[label] };
      try { window.localStorage.setItem("kalam.nav.collapsed", JSON.stringify(next)); } catch { /* local storage is an enhancement only */ }
      return next;
    });
  };

  const persistScrollPosition = () => {
    const nav = navRef.current;
    if (!nav) return;
    try { window.sessionStorage.setItem("kalam.nav.scrollTop", String(nav.scrollTop)); } catch { /* session storage is an enhancement only */ }
  };

  const prefetchRoute = (href: string) => {
    if (prefetchedRoutes.current.has(href)) return;
    prefetchedRoutes.current.add(href);
    router.prefetch(href);
  };

  const closeMobile = () => {
    persistScrollPosition();
    setMobileOpen(false);
  };

  const toggleSidebar = () => {
    setSidebarMinimized((current) => {
      const next = !current;
      try { window.localStorage.setItem("kalam.nav.minimized", String(next)); } catch { /* local storage is optional */ }
      return next;
    });
  };

  useEffect(() => {
    const nav = navRef.current;
    if (!nav) return;
    try {
      const stored = window.sessionStorage.getItem("kalam.nav.scrollTop");
      if (stored !== null) nav.scrollTop = Number(stored) || 0;
    } catch { /* session storage is an enhancement only */ }
  }, []);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      const nav = navRef.current;
      const activeItem = nav?.querySelector<HTMLElement>('[aria-current="page"]');
      if (!nav || !activeItem) return;

      const navRect = nav.getBoundingClientRect();
      const itemRect = activeItem.getBoundingClientRect();
      const edgePadding = 28;
      const above = itemRect.top < navRect.top + edgePadding;
      const below = itemRect.bottom > navRect.bottom - edgePadding;

      if (above || below) {
        activeItem.scrollIntoView({ block: "center", inline: "nearest", behavior: "auto" });
      }
      try { window.sessionStorage.setItem("kalam.nav.scrollTop", String(nav.scrollTop)); } catch { /* session storage is an enhancement only */ }
    });

    return () => window.cancelAnimationFrame(frame);
  }, [pathname, visibleGroups]);


  return (
    <>
      <button className="sidebar-mobile-toggle" type="button" onClick={() => setMobileOpen((value) => !value)}
        aria-expanded={mobileOpen} aria-controls="workspace-navigation">
        {mobileOpen ? <X size={18} aria-hidden="true" /> : <Menu size={18} aria-hidden="true" />}
        <span>{mobileOpen ? "Close navigation" : "Menu"}</span>
      </button>
      <nav ref={navRef} id="workspace-navigation" className={`sidebar-nav ${mobileOpen ? "mobile-open" : ""} ${sidebarMinimized ? "sidebar-minimized" : ""}`} aria-label="Primary navigation" onScroll={persistScrollPosition}>
        <button className="sidebar-collapse-toggle" type="button" onClick={toggleSidebar} aria-label={sidebarMinimized ? "Expand sidebar" : "Minimize sidebar"} aria-pressed={sidebarMinimized} title={sidebarMinimized ? "Expand sidebar" : "Minimize sidebar"}>
          {sidebarMinimized ? <ChevronRight size={17} aria-hidden="true" /> : <ChevronLeft size={17} aria-hidden="true" />}
          <span>{sidebarMinimized ? "Expand" : "Minimize"}</span>
        </button>
        {visibleGroups.map((group) => {
          const groupHasActiveItem = group.items.some((navItem) => isActive(navItem));
          const groupCollapsed = (collapsed[group.label] ?? false) && !groupHasActiveItem;
          return (
            <section className={`nav-group ${groupCollapsed ? "collapsed" : ""}`} key={group.label}>
              <button className="nav-group-toggle" type="button" onClick={() => toggleGroup(group.label)}
                aria-expanded={!groupCollapsed}>
                <span className="nav-label">{group.label}</span>
                <ChevronDown size={14} aria-hidden="true" />
              </button>
              <div className="nav-group-items" hidden={groupCollapsed}>
                {group.items.map((navItem) => {
                  const Icon = navItem.icon;
                  const active = isActive(navItem);
                  return (
                    <Link className={`nav-item ${active ? "active" : ""}`} href={navItem.href}
                      key={navItem.href} aria-current={active ? "page" : undefined}
                      aria-label={navItem.label} title={navItem.label} onPointerEnter={() => prefetchRoute(navItem.href)}
                      onFocus={() => prefetchRoute(navItem.href)} onClick={closeMobile}>
                      <Icon size={16} aria-hidden="true" />
                      <span>{navItem.label}</span>
                      {navItem.href === "/dashboard/compliance" && navCounts.overdue > 0 ? <b className="nav-badge" aria-label={`${navCounts.overdue} overdue compliance items`}>{navCounts.overdue > 99 ? "99+" : navCounts.overdue}</b> : null}
                      {navItem.href === "/dashboard/ld-operations" && navCounts.approvals > 0 ? <b className="nav-badge" aria-label={`${navCounts.approvals} enrollment approvals pending`}>{navCounts.approvals > 99 ? "99+" : navCounts.approvals}</b> : null}
                    </Link>
                  );
                })}
              </div>
            </section>
          );
        })}
        <section className="nav-group nav-account">
          <div className="nav-group-toggle static">
            <span className="nav-label">Account</span>
          </div>
          <div className="nav-group-items">
            {accountItems.map((navItem) => {
              const Icon = navItem.icon;
              const active = isActive(navItem);
              return (
                <Link className={`nav-item ${active ? "active" : ""}`} href={navItem.href}
                  key={navItem.href} aria-current={active ? "page" : undefined}
                  aria-label={navItem.label} title={navItem.label} onPointerEnter={() => prefetchRoute(navItem.href)}
                  onFocus={() => prefetchRoute(navItem.href)} onClick={closeMobile}>
                  <Icon size={16} aria-hidden="true" />
                  <span>{navItem.label}</span>
                  {navItem.href === "/dashboard/notifications" && navCounts.unread > 0 ? <b className="nav-badge" aria-label={`${navCounts.unread} unread notifications`}>{navCounts.unread > 99 ? "99+" : navCounts.unread}</b> : null}
                </Link>
              );
            })}
            <form action="/api/auth/logout" method="post">
              <button className="nav-item nav-signout" type="submit" aria-label="Sign out" title="Sign out">
                <LogOut size={16} aria-hidden="true" /><span>Sign out</span>
              </button>
            </form>
          </div>
        </section>
      </nav>
    </>
  );
}
