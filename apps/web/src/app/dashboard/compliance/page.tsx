import Link from "next/link";
import { ShieldCheck } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { ComplianceAssignmentActions } from "@/components/compliance-assignment-actions";
import { Section, StateMessage, StatusBadge } from "@/components/ui";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type Assignment = { id: string; requirement: string; requirement_version?: number; description?: string | null; status: string; due_state?: string; due_at?: string | null; course_id?: string | null; course_title?: string | null; rejection_reason?: string | null };
type Requirement = { id: string; name: string; description?: string | null; recurrence_days?: number | null; due_days?: number | null; active: boolean };

export default async function CompliancePage() {
  const user = await requireUser<{ permissions?: string[] }>();
  const [mineResult, requirementsResult] = await Promise.all([
    apiJsonResult<Assignment[]>("/api/v1/compliance/my"),
    apiJsonResult<Requirement[]>("/api/v1/compliance"),
  ]);
  const mine = mineResult.ok ? mineResult.data : null;
  const requirements = requirementsResult.ok ? requirementsResult.data : null;
  const openItems = mine?.filter((item) => !["completed", "excepted"].includes(item.status)).length ?? "—";
  const overdueItems = mine?.filter((item) => item.due_state === "overdue" && !["completed", "excepted"].includes(item.status)).length ?? "—";
  return (
    <DashboardShell title="Compliance & readiness" eyebrow="Mandatory training, evidence & exceptions">
      <div className="stat-grid">
        <div className="stat-card"><span>My obligations</span><strong>{mine?.length ?? "—"}</strong><small>Assigned to your role</small></div>
        <div className="stat-card"><span>Open actions</span><strong>{openItems}</strong><small>Completion or evidence required</small></div>
        <div className="stat-card"><span>Overdue</span><strong>{overdueItems}</strong><small>Priority attention</small></div>
        <div className="stat-card"><span>Applicable policies</span><strong>{requirements?.length ?? "—"}</strong><small>Relevant active requirements</small></div>
      </div>
      {mine === null || requirements === null ? <StateMessage tone="danger" title="Compliance data is unavailable">The compliance service did not return a complete response. Refresh the page or contact your administrator if the issue continues.</StateMessage> : null}
      <Section eyebrow="Your obligations" title="My compliance actions" action={user.permissions?.includes("compliance.manage") ? <Link className="text-link" href="/dashboard/compliance/admin">Open compliance operations →</Link> : null}>
        <p>Complete assigned learning, submit evidence, or request a time-bound exception. Every action is recorded in the compliance audit trail.</p>
        {mine?.length ? <div className="table-wrap"><table className="data-table"><caption className="sr-only">Compliance obligations assigned to you</caption><thead><tr><th scope="col">Requirement</th><th scope="col">Due</th><th scope="col">Status</th><th scope="col">Actions</th></tr></thead><tbody>{mine.map((item) => <tr key={item.id}><td><strong>{item.requirement}</strong><small>Policy v{item.requirement_version ?? 1} · {item.description || "Mandatory organizational requirement"}{item.course_title ? ` · ${item.course_title}` : " · Evidence workflow"}</small></td><td>{item.due_at ? new Date(item.due_at).toLocaleDateString() : "—"}</td><td><StatusBadge status={item.status} />{item.due_state === "overdue" && item.status !== "overdue" ? <StatusBadge status="overdue" /> : null}</td><td>{item.rejection_reason && ["assigned", "overdue"].includes(item.status) ? <small role="status">Evidence rejected: {item.rejection_reason}</small> : null}<ComplianceAssignmentActions assignment={item} /></td></tr>)}</tbody></table></div> : mine === null ? null : <div className="empty-state"><ShieldCheck size={24}/><h3>No compliance assignments yet</h3><p>Assigned requirements will appear here with their due dates and next actions.</p></div>}
      </Section>
      <Section eyebrow="Policy context" title="Applicable requirements">
        <p>These are active requirements currently applicable to your learner profile. Inactive and unrelated tenant policies are intentionally excluded.</p>
        {requirements?.length ? <div className="compact-list">{requirements.map((item) => <div className="compact-row" key={item.id}><div><strong>{item.name}</strong><small>{item.description || "Organizational compliance requirement"} · due within {item.due_days ?? 30} days{item.recurrence_days ? ` · renews every ${item.recurrence_days} days` : ""}</small></div><ShieldCheck size={17} aria-hidden="true" /></div>)}</div> : requirements === null ? null : <div className="empty-state"><p>No active requirements currently apply to you.</p></div>}
      </Section>
    </DashboardShell>
  );
}
