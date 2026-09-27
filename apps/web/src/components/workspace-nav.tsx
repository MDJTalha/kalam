"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity, Award, BarChart3, BookOpenCheck, BrainCircuit, ClipboardCheck, FileText,
  FolderOpen, GitBranch, Layers3, LogOut, Network, Route, Search,
  Settings2, ShieldCheck, Target, UserRoundCog, UsersRound,
} from "lucide-react";

type Props = { roles: string[]; permissions: string[] };
type NavIcon = typeof BarChart3;
type NavItem = readonly [string, string, NavIcon, string?];

const allowed = (permissions: string[], permission?: string) =>
  !permission || permissions.includes(permission);

const groups: Array<{ label: string; items: readonly NavItem[]; roles?: string[] }> = [
  { label: "Workspace", items: [["/dashboard", "Overview", BarChart3]] },
  { label: "People & Organization", items: [
    ["/dashboard/people", "People", UsersRound],
    ["/dashboard/team", "Teams", UsersRound],
    ["/dashboard/organization", "Organization", Network],
    ["/dashboard/people/admin", "User Administration", UserRoundCog, "users.read"],
  ] },
  { label: "Learning", items: [
    ["/dashboard/catalog", "Learning Catalog", BookOpenCheck],
    ["/dashboard/learning-paths", "Learning Paths", GitBranch],
    ["/dashboard/programs", "Programs & Cohorts", Route],
    ["/dashboard/course-studio", "Course Studio", BookOpenCheck],
    ["/dashboard/ld-operations", "L&D Operations", Activity],
  ] },  { label: "Capability", items: [
    ["/dashboard/skills", "Skills & Capabilities", Layers3],
    ["/dashboard/skills/admin", "Capability Framework", GitBranch, "skills.manage"],
    ["/dashboard/development", "Development Plans", Target],
  ] },
  { label: "Assessment & Credentials", items: [
    ["/dashboard/assessments", "Assessments", ClipboardCheck],
    ["/dashboard/certificates", "Certificates", Award],
    ["/dashboard/certificates/admin", "Certificate Administration", Award, "certificates.manage"],
  ] },
  { label: "Risk & Evidence", items: [
    ["/dashboard/compliance", "Compliance & Readiness", ShieldCheck],
    ["/dashboard/compliance/admin", "Compliance Operations", ShieldCheck, "compliance.manage"],
    ["/dashboard/files", "Evidence Repository", FolderOpen, "files.read"],
  ] },
  { label: "Insights", items: [
    ["/dashboard/analytics", "Analytics", BarChart3],
    ["/dashboard/reports", "Reports", FileText],
    ["/dashboard/ai", "Governed AI", BrainCircuit, "learning.access"],
  ] },
  { label: "Administration", roles: ["Tenant Admin", "HR/L&D Admin", "Compliance Admin", "Auditor"], items: [
    ["/dashboard/admin", "Roles & Permissions", UserRoundCog, "tenant.manage"],
    ["/dashboard/audit", "Audit Log", FileText, "audit.read"],
    ["/dashboard/integrations", "Integrations", Network],
    ["/dashboard/webhooks", "Webhooks", Network],
  ] },
];function hasRoleAccess(roles: string[], wanted?: string[]) {
  if (!wanted) return true;
  return roles.includes("Tenant Admin") || wanted.some((role) => roles.includes(role));
}

export function WorkspaceNav({ roles, permissions }: Props) {
  const pathname = usePathname();
  const isActive = (href: string) =>
    href === "/dashboard" || href === "/dashboard/skills" || href === "/dashboard/compliance" ? pathname === href : pathname === href || pathname.startsWith(`${href}/`);

  return (
    <nav className="sidebar-nav" aria-label="Primary navigation">
      {groups.map((group) => {
        if (!hasRoleAccess(roles, group.roles)) return null;
        const items = group.items.filter(([, , , permission]) => allowed(permissions, permission));
        if (!items.length) return null;

        return (
          <div className="nav-group" key={group.label}>
            <span className="nav-label">{group.label}</span>
            {items.map(([href, label, Icon]) => {
              const active = isActive(href);
              return (
                <Link className={`nav-item ${active ? "active" : ""}`} href={href} key={`${href}-${label}`} aria-current={active ? "page" : undefined} aria-label={label} title={label}>
                  <Icon size={16} aria-hidden="true" />
                  <span>{label}</span>
                </Link>
              );
            })}
          </div>
        );
      })}      <div className="nav-group nav-account">
        <span className="nav-label">Account</span>
        <Link className={`nav-item ${isActive("/dashboard/search") ? "active" : ""}`} href="/dashboard/search" aria-label="Global Search" title="Global Search">
          <Search size={16} aria-hidden="true" /><span>Global Search</span>
        </Link>
        <Link className={`nav-item ${isActive("/dashboard/notifications") ? "active" : ""}`} href="/dashboard/notifications" aria-label="Notifications" title="Notifications">
          <Activity size={16} aria-hidden="true" /><span>Notifications</span>
        </Link>
        <Link className={`nav-item ${isActive("/dashboard/sessions") ? "active" : ""}`} href="/dashboard/sessions" aria-label="Security Sessions" title="Security Sessions">
          <ShieldCheck size={16} aria-hidden="true" /><span>Security Sessions</span>
        </Link>
        <Link className={`nav-item ${isActive("/dashboard/settings") ? "active" : ""}`} href="/dashboard/settings" aria-label="Settings" title="Settings">
          <Settings2 size={16} aria-hidden="true" /><span>Settings</span>
        </Link>
        <form action="/api/auth/logout" method="post">
          <button className="nav-item nav-signout" type="submit" aria-label="Sign out" title="Sign out">
            <LogOut size={16} aria-hidden="true" /><span>Sign out</span>
          </button>
        </form>
      </div>
    </nav>
  );
}
