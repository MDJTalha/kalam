/* eslint-disable @next/next/no-html-link-for-pages -- The compliance CSV endpoint returns a file download. */
import Link from "next/link";
import { ClipboardCheck, FileCheck2, ShieldAlert } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { ApiActionButton } from "@/components/api-action-button";
import { ResourceForm } from "@/components/resource-form";
import { EmptyState, Section, StateMessage, StatusBadge } from "@/components/ui";
import { apiJson, requireUser } from "@/lib/server-api";

type Requirement = { id: string; name: string; description?: string | null; due_days?: number | null; recurrence_days?: number | null; active: boolean; rules?: Record<string, unknown>; version?: number };
type RequirementVersion = { version: number; snapshot: { name: string; description?: string | null; due_days?: number | null; recurrence_days?: number | null; active: boolean }; changed_by?: string | null; created_at: string };
type Report = { requirements: number; active_requirements: number; assignments: number; overdue: number; completed: number; exceptions: number; approved_exceptions: number; requested_exceptions?: number; pending_evidence?: number };
type Assignment = { id: string; requirement: string; requirement_version?: number; user_name: string; user_email: string; status: string; due_state?: string; due_at?: string | null };
type Evidence = { id: string; user_id: string; requirement: string; user_name: string; user_email: string; evidence_type: string; reference: string; attachment_status?: string | null; notes?: string | null; created_at: string };
type ComplianceCourse = { id: string; title: string };
type AudiencePreview = { active_learners: number; matching: number; already_open: number; eligible: number };
type ExceptionItem = { id: string; requirement: string; user_name: string; user_email: string; reason: string; status: string; expires_at?: string | null; created_at: string };

export default async function ComplianceAdminPage({ searchParams }: { searchParams: Promise<{ page?: string; status?: string; edit?: string }> }) {
  const query = await searchParams;
  const page = Math.max(1, Number.parseInt(query.page || "1", 10) || 1);
  const allowedStatuses = ["all", "assigned", "due_soon", "overdue", "evidence_submitted", "exception_requested", "completed", "excepted"];
  const status = allowedStatuses.includes(query.status || "") ? query.status! : "all";
  const params = new URLSearchParams({ limit: "50", offset: String((page - 1) * 50) });
  if (status !== "all") params.set("status", status);
  const user = await requireUser<{ id: string; permissions?: string[] }>();
  if (!user.permissions?.includes("compliance.manage")) {
    return <DashboardShell title="Compliance operations" eyebrow="Controlled obligations"><Section eyebrow="Access" title="Restricted workspace"><p>This workspace requires compliance administration permission.</p></Section></DashboardShell>;
  }
  const [requirements, report, assignments, evidence, exceptions, courses] = await Promise.all([
    apiJson<Requirement[]>("/api/v1/compliance"),
    apiJson<Report>("/api/v1/compliance/reports"),
    apiJson<{ total: number; items: Assignment[] }>(`/api/v1/compliance/assignments?${params}`),
    apiJson<Evidence[]>("/api/v1/compliance/evidence"),
    apiJson<ExceptionItem[]>("/api/v1/compliance/exceptions?status=requested"),
    apiJson<ComplianceCourse[]>("/api/v1/compliance/courses"),
  ]);
  const serviceUnavailable = [requirements, report, assignments, evidence, exceptions, courses].some((item) => item === null);
  const editing = requirements?.find((item) => item.id === query.edit);
  const [preview, versions] = editing ? await Promise.all([
    apiJson<AudiencePreview>(`/api/v1/compliance/${editing.id}/preview`),
    apiJson<RequirementVersion[]>(`/api/v1/compliance/${editing.id}/versions`),
  ]) : [null, null];
  return (
    <DashboardShell title="Compliance operations" eyebrow="Policy governance, evidence review & readiness">
      <div className="stat-grid">
        <div className="stat-card"><span>Requirements</span><strong>{report?.requirements ?? 0}</strong><small>{report?.active_requirements ?? 0} active</small></div>
        <div className="stat-card"><span>Assignments</span><strong>{report?.assignments ?? 0}</strong><small>{report?.completed ?? 0} completed</small></div>
        <div className="stat-card"><span>Overdue</span><strong>{report?.overdue ?? 0}</strong><small>Priority intervention</small></div>
        <div className="stat-card"><span>Review queue</span><strong>{(report?.pending_evidence ?? 0) + (report?.requested_exceptions ?? 0)}</strong><small>{report?.pending_evidence ?? 0} evidence · {report?.requested_exceptions ?? 0} exceptions</small></div>
      </div>
      <nav className="button-row" aria-label="Related workspaces"><a className="button button-secondary" href="/api/lms/compliance/reports/export">Export assignments CSV</a>{user.permissions?.includes("courses.manage") ? <Link className="button button-secondary" href="/dashboard/course-studio">Course studio</Link> : null}{user.permissions?.includes("files.read") ? <Link className="button button-secondary" href="/dashboard/files">Evidence repository</Link> : null}{user.permissions?.includes("reports.read") ? <Link className="button button-secondary" href="/dashboard/reports">Reports</Link> : null}{user.permissions?.includes("audit.read") ? <Link className="button button-secondary" href="/dashboard/audit">Audit log</Link> : null}</nav>
      {serviceUnavailable ? <StateMessage tone="danger" title="Compliance operations data is incomplete">One or more management datasets could not be loaded. No governance action should be taken until the workspace is refreshed successfully.</StateMessage> : null}
      <Section eyebrow="Policy definition" title="Create a controlled requirement">
        <ResourceForm title="Add compliance requirement" description="Define the obligation, timing and controlled applicability audience before assigning learning." endpoint="/api/lms/compliance" fields={[
          { name: "name", label: "Requirement name", required: true, placeholder: "Annual information security training" },
          { name: "description", label: "Policy description", type: "textarea", placeholder: "State the control objective, evidence expectation and accountable owner." },
          { name: "due_days", label: "Due within days", type: "number", defaultValue: 30, required: true },
          { name: "recurrence_days", label: "Renew every days", type: "number", placeholder: "Optional" },
          { name: "rules", label: "Applicability rules (JSON)", type: "textarea", placeholder: '{"role_names":["Learner"],"job_titles":[],"org_unit_ids":[],"exclude_user_ids":[],"escalation_days":7}' },
        ]} jsonFields={["rules"]} />
        <div className="callout" style={{ marginTop: 14 }}><ShieldAlert size={16} /><div><strong>Controlled audience rules</strong><p>Use role_names, job_titles, org_unit_ids and exclude_user_ids. Leave the object empty to apply to all active learners. Escalation days controls manager follow-up after the due date.</p></div></div>
      </Section>
      <Section eyebrow="Policy library" title="Govern active obligations">
        {requirements?.length ? <div className="compact-list">{requirements.map((item) => <div className="compact-row" key={item.id}><div><strong>{item.name}</strong><small>Version {item.version ?? 1} · {item.description || "Organizational compliance requirement"} · due within {item.due_days ?? 30} days{item.recurrence_days ? ` · renews every ${item.recurrence_days} days` : ""}</small></div><div className="button-row"><StatusBadge status={item.active ? "active" : "inactive"} />{item.active ? <ApiActionButton endpoint={`/api/lms/compliance/${item.id}/assign-applicable`} label="Assign evidence obligation" body={{}} confirmText={`Assign ${item.name} as an evidence obligation to all matching active learners? Existing open assignments will be skipped.`} /> : null}<Link className="button button-secondary" href={`/dashboard/compliance/admin?edit=${item.id}#edit-requirement`}>Configure / assign course</Link><ApiActionButton endpoint={`/api/lms/compliance/${item.id}`} method="PATCH" label={item.active ? "Deactivate" : "Activate"} body={{ active: !item.active }} confirmText={`${item.active ? "Deactivate" : "Activate"} ${item.name}?`} /></div></div>)}</div> : <EmptyState title="No requirements configured" description="Create the first controlled compliance obligation for this tenant." />}
      </Section>
      {editing ? <section id="edit-requirement" className="data-panel">
        {preview ? <p><strong>Current audience:</strong> {preview.matching} of {preview.active_learners} active learners match · {preview.already_open} already assigned · {preview.eligible} eligible for a new assignment. This preview uses the saved rules.</p> : <StateMessage tone="warning" title="Audience preview unavailable">Check the applicability rules before assigning.</StateMessage>}
        <ResourceForm key={editing.id} title={`Edit ${editing.name}`} description="Updates to timing and audience apply to future assignments; existing obligations retain their assigned due dates." endpoint={`/api/lms/compliance/${editing.id}`} method="PATCH" submitLabel="Save requirement" fields={[
          { name: "name", label: "Requirement name", required: true, defaultValue: editing.name },
          { name: "description", label: "Policy description", type: "textarea", defaultValue: editing.description || "" },
          { name: "due_days", label: "Due within days", type: "number", required: true, defaultValue: editing.due_days ?? 30 },
          { name: "recurrence_days", label: "Renew every days", type: "number", defaultValue: editing.recurrence_days ?? "" },
          { name: "rules", label: "Applicability rules (JSON)", type: "textarea", defaultValue: JSON.stringify(editing.rules || {}, null, 2) },
        ]} jsonFields={["rules"]} includeEmptyFields={["description", "recurrence_days"]} />
        {versions?.length ? <details><summary>Policy history ({versions.length} versions)</summary><div className="compact-list">{versions.map((entry) => <div className="compact-row" key={entry.version}><div><strong>Version {entry.version} · {entry.snapshot.name}</strong><small>{new Date(entry.created_at).toLocaleString()} · {entry.snapshot.active ? "Active" : "Inactive"} · due within {entry.snapshot.due_days ?? 30} days{entry.snapshot.recurrence_days ? ` · renews every ${entry.snapshot.recurrence_days} days` : ""}</small></div></div>)}</div></details> : null}
        {courses?.length ? <ResourceForm title="Assign a learning course" description="Enroll matching active learners in a published course. Existing open obligations are skipped." endpoint={`/api/lms/compliance/${editing.id}/assign-applicable`} fields={[
          { name: "course_id", label: "Published course", type: "select", required: true, options: courses.map((course) => ({ value: course.id, label: course.title })) },
        ]} submitLabel="Assign course to applicable learners" /> : <p>No published courses are available for assignment.</p>}
      </section> : null}
      <Section eyebrow="Assignment coverage" title="Monitor learner obligations">
        <div className="button-row" aria-label="Filter assignments">{allowedStatuses.map((value) => <Link key={value} className={`button ${status === value ? "button-primary" : "button-ghost"}`} href={`/dashboard/compliance/admin?status=${value}`}>{value.replaceAll("_", " ")}</Link>)}</div>
        {assignments?.items.length ? <div className="table-wrap" role="region" aria-label="Compliance assignment coverage" tabIndex={0}><table className="data-table"><caption className="sr-only">Compliance assignment coverage</caption><thead><tr><th scope="col">Learner</th><th scope="col">Requirement</th><th scope="col">Due</th><th scope="col">Status</th></tr></thead><tbody>{assignments.items.map((item) => <tr key={item.id}><td><strong>{item.user_name}</strong><small>{item.user_email}</small></td><td>{item.requirement}<small>Policy v{item.requirement_version ?? 1}</small></td><td>{item.due_at ? new Date(item.due_at).toLocaleDateString() : "—"}</td><td><StatusBadge status={item.status} />{item.due_state === "overdue" && item.status !== "overdue" ? <StatusBadge status="overdue" /> : null}</td></tr>)}</tbody></table></div> : <EmptyState title="No assignments" description="Applicable learners will appear here after a requirement is assigned." />}
        {assignments && assignments.total > 50 ? <nav className="button-row" aria-label="Assignment pages"><span>Page {page} of {Math.ceil(assignments.total / 50)} · {assignments.total} assignments</span>{page > 1 ? <Link className="button button-secondary" href={`/dashboard/compliance/admin?status=${status}&page=${page - 1}`}>Previous</Link> : null}{page * 50 < assignments.total ? <Link className="button button-secondary" href={`/dashboard/compliance/admin?status=${status}&page=${page + 1}`}>Next</Link> : null}</nav> : null}
      </Section>
      <Section eyebrow="Evidence review" title="Verify submitted evidence">
        {evidence?.length ? <div className="compact-list">{evidence.map((item) => <div className="compact-row" key={item.id}><div><strong>{item.requirement} · {item.user_name}</strong><small>{item.evidence_type}: {item.evidence_type === "document" && item.reference.startsWith("file:") ? (item.attachment_status === "available" ? <a className="text-link" href={`/api/lms/compliance/evidence/${item.id}/download`}>Download document</a> : "Attachment awaiting scan") : item.evidence_type === "url" && /^https?:\/\//i.test(item.reference) ? <a className="text-link" href={item.reference} target="_blank" rel="noopener noreferrer">{item.reference}</a> : item.reference}{item.notes ? ` · ${item.notes}` : ""}</small></div><div className="button-row"><StatusBadge status={item.attachment_status === "pending_scan" ? "pending scan" : "pending review"} />{user.id !== item.user_id ? <>{item.attachment_status === "pending_scan" ? <small>Security scan clearance required</small> : <ApiActionButton endpoint={`/api/lms/compliance/evidence/${item.id}/verify`} label="Verify evidence" body={{}} />}<details><summary>Reject evidence</summary><ResourceForm title="Request corrected evidence" endpoint={`/api/lms/compliance/evidence/${item.id}/reject`} fields={[{ name: "reason", label: "Reason for rejection", type: "textarea", required: true }]} submitLabel="Reject and reopen" /></details></> : <small>A different reviewer must decide</small>}</div></div>)}</div> : <EmptyState title="Evidence queue is clear" description="Unverified learner evidence will appear here for review." icon={FileCheck2} />}
      </Section>
      <Section eyebrow="Exception governance" title="Review exception requests">
        {exceptions?.length ? <div className="compact-list">{exceptions.map((item) => <div className="compact-row" key={item.id}><div><strong>{item.requirement} · {item.user_name}</strong><small>{item.reason}{item.expires_at ? ` · requested through ${new Date(item.expires_at).toLocaleDateString()}` : " · no expiry requested"}</small></div><div className="button-row"><StatusBadge status="requested" /><ApiActionButton endpoint={`/api/lms/compliance/exceptions/${item.id}/approve`} label="Approve" body={{}} confirmText="Approve this time-bound compliance exception?" /><ApiActionButton endpoint={`/api/lms/compliance/exceptions/${item.id}/reject`} label="Reject" body={{}} confirmText="Reject this compliance exception request?" /></div></div>)}</div> : <EmptyState title="No exception requests" description="New requests will remain pending here until an authorized reviewer decides." icon={ClipboardCheck} />}
      </Section>
    </DashboardShell>
  );
}
