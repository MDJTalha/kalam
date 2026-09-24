import { BarChart3, FileText } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJson, requireUser } from "@/lib/server-api";

type Summary = { users: number; courses: number; enrollments: number; completed_enrollments: number; certificates: number; compliance_assignments: number };

export default async function ReportsPage() {
  await requireUser();
  const summary = await apiJson<Summary>("/api/v1/reports/summary");
  return (
    <DashboardShell title="Reports & analytics" eyebrow="Decision-ready reporting">
      {summary ? (
        <>
          <div className="stat-grid">
            <div className="stat-card"><span>People</span><strong>{summary.users}</strong><small>Tenant users</small></div>
            <div className="stat-card"><span>Courses</span><strong>{summary.courses}</strong><small>Learning catalog</small></div>
            <div className="stat-card"><span>Enrollments</span><strong>{summary.enrollments}</strong><small>Total recorded</small></div>
            <div className="stat-card"><span>Certificates</span><strong>{summary.certificates}</strong><small>Issued credentials</small></div>
          </div>
          <div className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Executive snapshot</span><h2>Learning health</h2></div></div><div className="metric-strip"><span><b>{summary.completed_enrollments}</b> completions</span><span><b>{summary.compliance_assignments}</b> compliance assignments</span><span><b>{summary.enrollments ? Math.round(summary.completed_enrollments/summary.enrollments*100) : 0}%</b> completion ratio</span><span><b>{summary.users ? Math.round(summary.enrollments/summary.users*10)/10 : 0}</b> enrollments / user</span></div></div>
        </>
      ) : (
        <div className="data-panel"><div className="empty-state"><FileText size={28}/><h2>Report access is restricted</h2><p>Your current role does not include the reporting permission required for this workspace.</p></div></div>
      )}
      <div className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Exports</span><h2>Operational datasets</h2></div><FileText size={20}/></div><div className="module-grid">{/* API CSV download endpoint; native anchor is intentional. */}
          {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
          <a className="module-card" href="/api/reports/export/people"><div className="module-icon"><FileText size={19}/></div><div><h3>People CSV</h3><p>Tenant-scoped employee identity and job data.</p></div></a>
          {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
          <a className="module-card" href="/api/reports/export/enrollments"><div className="module-icon"><FileText size={19}/></div><div><h3>Enrollment CSV</h3><p>Learning registrations, statuses and completion dates.</p></div></a></div></div>
      <div className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Reporting architecture</span><h2>Evidence boundaries</h2></div></div><div className="compact-list"><div className="compact-row"><div><strong>Persisted records</strong><small>Counts come from tenant-scoped database records.</small></div><BarChart3 size={17}/></div><div className="compact-row"><div><strong>Derived metrics</strong><small>Ratios are calculated from the persisted summary fields.</small></div><BarChart3 size={17}/></div><div className="compact-row"><div><strong>AI narratives</strong><small>Future generated summaries will remain clearly distinguished from authoritative metrics.</small></div><BarChart3 size={17}/></div></div></div>
    </DashboardShell>
  );
}
