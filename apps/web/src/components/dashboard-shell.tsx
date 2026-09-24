import Link from "next/link";
import {
  Award,
  BarChart3,
  BookOpenCheck,
  ClipboardCheck,
  FileText,
  Layers3,
  LogOut,
  Settings2,
  ShieldCheck,
  UsersRound,
  Route,
  Target,
  Search,
} from "lucide-react";

const navigation = [
  ["/dashboard", "Overview", BarChart3],
  ["/dashboard/catalog", "Learning", BookOpenCheck],
  ["/dashboard/people", "People", UsersRound],
  ["/dashboard/compliance", "Compliance", ShieldCheck],
  ["/dashboard/skills", "Skills", Layers3],
  ["/dashboard/development", "Development", Target],
  ["/dashboard/programs", "Programs", Route],
  ["/dashboard/search", "Search", Search],
  ["/dashboard/assessments", "Assessments", ClipboardCheck],
  ["/dashboard/certificates", "Credentials", Award],
  ["/dashboard/reports", "Reports", FileText],
] as const;

export function DashboardShell({
  children,
  title,
  eyebrow = "Corporate learning",
}: {
  children: React.ReactNode;
  title: string;
  eyebrow?: string;
}) {
  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <span className="brand-mark"><ShieldCheck size={18} /></span>
          <span>Corporate LMS</span>
        </div>
        <nav className="sidebar-nav" aria-label="Primary">
          <span className="nav-label">Workspace</span>
          {navigation.map(([href, label, Icon]) => (
            <Link className="nav-item" href={href} key={href}>
              <Icon size={17} />
              {label}
            </Link>
          ))}
          <span className="nav-label nav-label-spaced">Administration</span>
          <Link className="nav-item" href="/dashboard/settings">
            <Settings2 size={17} />
            Settings
          </Link>
          <Link className="nav-item" href="/logout">
            <LogOut size={17} />
            Sign out
          </Link>
        </nav>
        <div className="sidebar-footer">
          <div className="system-status"><i /> API-connected workspace</div>
          <small>Controlled enterprise foundation · v0.1</small>
        </div>
      </aside>
      <section className="workspace">
        <header className="workspace-header">
          <div>
            <span className="eyebrow">{eyebrow}</span>
            <h1>{title}</h1>
          </div>
        </header>
        {children}
      </section>
    </main>
  );
}
