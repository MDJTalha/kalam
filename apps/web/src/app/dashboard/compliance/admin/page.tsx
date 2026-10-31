/* eslint-disable @next/next/no-html-link-for-pages -- The compliance CSV endpoint returns a file download. */
import Link from "next/link";
import { ClipboardCheck, FileCheck2, ShieldAlert } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { ApiActionButton } from "@/components/api-action-button";
import { ResourceForm } from "@/components/resource-form";
import { EmptyState, Section, StateMessage, StatusBadge } from "@/components/ui";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type Requirement = { id: string; name: string; description?: string | null; due_days?: number | null; recurrence_days?: number | null; active: boolean; rules?: Record<string, unknown>; version?: number };
type RequirementPage = { items: Requirement[]; total: number; page: number; page_size: number };
type RequirementVersion = { version: number; snapshot: { name: string; description?: string | null; due_days?: number | null; recurrence_days?: number | null; active: boolean }; changed_by?: string | null; created_at: string };
type Report = { requirements: number; active_requirements: number; assignments: number; overdue: number; completed: number; exceptions: number; approved_exceptions: number; requested_exceptions?: number; pending_evidence?: number };
type Assignment = { id: string; requirement: string; requirement_version?: number; user_name: string; user_email: string; status: string; due_state?: string; due_at?: string | null };
type Evidence = { id: string; user_id: string; requirement: string; user_name: string; user_email: string; evidence_type: string; reference: string; attachment_status?: string | null; notes?: string | null; created_at: string };
type EvidencePage = { total: number; items: Evidence[] };
type ComplianceCourse = { id: string; title: string };
type CoursePage = { items: ComplianceCourse[]; total: number; page: number; page_size: number };
type RoleOption = { id: string; name: string };
type UnitOption = { id: string; name: string; unit_type: string };
type AudiencePreview = { active_learners: number; matching: number; already_open: number; eligible: number };
type OperationsSummary = { generated_at: string; open_assignments: number; overdue: number; evidence_review: number; exception_review: number; expiring_exceptions_7d: number };
type ExceptionItem = { id: string; requirement: string; user_name: string; user_email: string; reason: string; status: string; expires_at?: string | null; created_at: string };

export default async function ComplianceAdminPage({ searchParams }: { searchParams: Promise<{ page?: string; evidence_page?: string; status?: string; edit?: string }> }) {
  const query = await searchParams;
  const page = Math.max(1, Number.parseInt(query.page || "1", 10) || 1);
  const evidencePage = Math.max(1, Number.parseInt(query.evidence_page || "1", 10) || 1);
  const allowedStatuses = ["all", "assigned", "due_soon", "overdue", "evidence_submitted", "exception_requested", "completed", "excepted"];
  const status = allowedStatuses.includes(query.status || "") ? query.status! : "all";
  const params = new URLSearchParams({ limit: "50", offset: String((page - 1) * 50) });
  if (status !== "all") params.set("status", status);
  const user = await requireUser<{ id: string; permissions?: string[] }>();
  if (!user.permissions?.includes("compliance.manage")) {
    return <DashboardShell title="Compliance operations" eyebrow="Controlled obligations"><Section eyebrow="Access" title="Restricted workspace"><p>This workspace requires compliance administration permission.</p></Section></DashboardShell>;
  }
  const [requirementsResult, reportResult, assignmentsResult, evidenceResult, exceptionsResult, coursesResult, operationsResult, roleOptionsResult, unitOptionsResult] = await Promise.all([
    apiJsonResult<RequirementPage>("/api/v1/compliance/page?page=1&page_size=100"),
    apiJsonResult<Report>("/api/v1/compliance/reports"),
    apiJsonResult<{ total: number; items: Assignment[] }>(`/api/v1/compliance/assignments?${params}`),
    apiJsonResult<EvidencePage>(`/api/v1/compliance/evidence?limit=50&offset=${(evidencePage - 1) * 50}`),
    apiJsonResult<ExceptionItem[]>("/api/v1/compliance/exceptions?status=requested"),
    apiJsonResult<CoursePage>("/api/v1/compliance/courses/page?page=1&page_size=100"),
    apiJsonResult<OperationsSummary>("/api/v1/compliance/operations/summary"),
    user.permissions?.includes("users.read") ? apiJsonResult<RoleOption[]>("/api/v1/organization/roles") : Promise.resolve({ok:true,status:200,data:[] as RoleOption[],error:null}),
    user.permissions?.includes("users.read") ? apiJsonResult<UnitOption[]>("/api/v1/organization/units") : Promise.resolve({ok:true,status:200,data:[] as UnitOption[],error:null}),
  ]);
  const results = [requirementsResult, reportResult, assignmentsResult, evidenceResult, exceptionsResult, coursesResult, operationsResult];
  const failed = results.filter((item) => !item.ok);
  const requirementsPage = requirementsResult.data;
  const requirements = requirementsPage?.items ?? [];
  const report = reportResult.data;
  const assignments = assignmentsResult.data;
  const evidence = evidenceResult.data;
  const exceptions = exceptionsResult.data;
  const coursesPage = coursesResult.data;
  const courses = coursesPage?.items ?? [];
  const operations = operationsResult.data;
  const roleOptions = roleOptionsResult.data ?? [];
  const unitOptions = unitOptionsResult.data ?? [];
  const serviceUnavailable = failed.length > 0 || (requirementsPage ? requirementsPage.total > requirementsPage.items.length : false) || (coursesPage ? coursesPage.total > coursesPage.items.length : false);
  const editing = requirements.find((item) => item.id === query.edit);
  const [previewResult, versionsResult] = editing ? await Promise.all([
    apiJsonResult<AudiencePreview>(`/api/v1/compliance/${editing.id}/preview`),
    apiJsonResult<RequirementVersion[]>(`/api/v1/compliance/${editing.id}/versions`),
  ]) : [{ok:false,status:0,data:null,error:""}, {ok:false,status:0,data:null,error:""}];
  return (
    <DashboardShell title="Compliance operations" eyebrow="Policy governance, evidence review & readiness">
      <div className="stat-grid">
        <div className="stat-card"><span>Requirements</span><strong>{report?.requirements ?? 0}</strong><small>{report?.active_requirements ?? 0} active</small></div>
        <div className="stat-card"><span>Assignments</span><strong>{report?.assignments ?? 0}</strong><small>{report?.completed ?? 0} completed</small></div>
        <div className="stat-card"><span>Overdue</span><strong>{report?.overdue ?? 0}</strong><small>Priority intervention</small></div>
        <div className="stat-card"><span>Review queue</span><strong>{(report?.pending_evidence ?? 0) + (report?.requested_exceptions ?? 0)}</strong><small>{report?.pending_evidence ?? 0} evidence · {report?.requested_exceptions ?? 0} exceptions</small></div>
      </div>
      <nav className="button-row" aria-label="Related workspaces"><a className="button button-secondary" href="/api/lms/compliance/reports/export">Export assignments CSV</a>{user.permissions?.includes("courses.manage") ? <Link className="button button-secondary" href="/dashboard/course-studio">Course studio</Link> : null}{user.permissions?.includes("files.read") ? <Link className="button button-secondary" href="/dashboard/files">Evidence repository</Link> : null}{user.permissions?.includes("reports.read") ? <Link className="button button-secondary" href="/dashboard/reports">Reports</Link> : null}{user.permissions?.includes("audit.read") ? <Link className="button button-secondary" href="/dashboard/audit">Audit log</Link> : null}</nav>
      {serviceUnavailable ? <StateMessage tone="danger" title="Compliance operations data is incomplete">{failed.map((item) => `HTTP ${item.status} — ${item.error || "request failed"}`).join(" · ")} No governance action should be taken until the workspace is refreshed successfully.</StateMessage> : null}
      <Section eyebrow="Operations engine" title="Readiness control loop" action={<ApiActionButton endpoint="/api/lms/compliance/operations/run" label="Run compliance operations" body={{}} confirmText="Run overdue normalization, exception expiry, recurrence and escalation processing now?" />}>
        {operations ? <div className="metric-strip"><span><b>{operations.open_assignments}</b> open obligations</span><span><b>{operations.overdue}</b> overdue</span><span><b>{operations.evidence_review}</b> evidence review</span><span><b>{operations.exception_review}</b> exception review</span><span><b>{operations.expiring_exceptions_7d}</b> exceptions expiring in 7 days</span></div> : <StateMessage tone="warning" title="Operations summary unavailable">The compliance control-loop summary could not be loaded.</StateMessage>}
        <p className="form-help">The operations runner normalizes overdue states, expires approved exceptions, creates due recurring obligations, and sends idempotent escalation notifications.</p>
      </Section>
      <Section eyebrow="Policy definition" title="Create a controlled requirement">
        <ResourceForm title="Add compliance requirement" description="Define the obligation, timing and controlled applicability audience before assigning learning." transformProfile="compliance_rules" endpoint="/api/lms/compliance" fields={[
          { name: "name", label: "Requirement name", required: true, placeholder: "Annual information security training" },
          { name: "description", label: "Policy description", type: "textarea", placeholder: "State the control objective, evidence expectation and accountable owner." },
          { name: "due_days", label: "Due within days", type: "number", defaultValue: 30, required: true },
          { name: "recurrence_days", label: "Renew every days", type: "number", placeholder: "Optional" },
          { name: "role_names", label: "Roles", type: "multi-select", options: roleOptions.map((item) => ({ value: item.name, label: item.name })) || [], help: "Select any role that should be included." },
          { name: "job_titles", label: "Job titles", placeholder: "One or more titles, separated by commas or lines." },
          { name: "org_unit_ids", label: "Organization units", type: "multi-select", options: unitOptions.map((item) => ({ value: item.id, label: item.name + " · " + item.unit_type })) || [], help: "Select any unit that should be included." },
          { name: "exclude_user_ids", label: "Exclude specific people", type: "lookup-multi", endpoint: "/api/v1/people/page?status=active&page_size=20" },
          { name: "escalation_days", label: "Escalate after days", type: "number", defaultValue: 7, required: true },
        ]} />
        <div className="callout saas-spaced-callout-lg"><ShieldAlert size={16} /><div><strong>Controlled audience rules</strong><p>Use role_names, job_titles, org_unit_ids and exclude_user_ids. Leave the object empty to apply to all active learners. Escalation days controls manager follow-up after the due date.</p></div></div>
      </Section>
      <Section eyebrow="Policy library" title="Govern active obligations">
        {requirements?.length ? <div className="compact-list">{requirements.map((item) => <div className="compact-row" key={item.id}><div><strong>{item.name}</strong><small>Version {item.version ?? 1} · {item.description || "Organizational compliance requirement"} · due within {item.due_days ?? 30} days{item.recurrence_days ? ` · renews every ${item.recurrence_days} days` : ""}</small></div><div className="button-row"><StatusBadge status={item.active ? "active" : "inactive"} />{item.active ? <ApiActionButton endpoint={`/api/lms/compliance/${item.id}/assign-applicable`} label="Assign evidence obligation" body={{}} confirmText={`Assign ${item.name} as an evidence obligation to all matching active learners? Existing open assignments will be skipped.`} /> : null}<Link className="button button-secondary" href={`/dashboard/compliance/admin?edit=${item.id}#edit-requirement`}>Configure / assign course</Link><ApiActionButton endpoint={`/api/lms/compliance/${item.id}`} method="PATCH" label={item.active ? "Deactivate" : "Activate"} body={{ active: !item.active }} confirmText={`${item.active ? "Deactivate" : "Activate"} ${item.name}?`} /></div></div>)}</div> : <EmptyState title="No requirements configured" description="Create the first controlled compliance obligation for this tenant." />}
      </Section>
      {editing ? <section id="edit-requirement" className="data-panel">
        {previewResult.ok && previewResult.data ? <p><strong>Current audience:</strong> {previewResult.data.matching} of {previewResult.data.active_learners} active learners match · {previewResult.data.already_open} already assigned · {previewResult.data.eligible} eligible for a new assignment. This preview uses the saved rules.</p> : <StateMessage tone="warning" title="Audience preview unavailable">Check the applicability rules before assigning.</StateMessage>}
        <ResourceForm key={editing.id} title={`Edit ${editing.name}`} description="Updates to timing and audience apply to future assignments; existing obligations retain their assigned due dates." transformProfile="compliance_rules" endpoint={`/api/lms/compliance/${editing.id}`} method="PATCH" submitLabel="Save requirement" fields={[
          { name: "name", label: "Requirement name", required: true, defaultValue: editing.name },
          { name: "description", label: "Policy description", type: "textarea", defaultValue: editing.description || "" },
          { name: "due_days", label: "Due within days", type: "number", required: true, defaultValue: editing.due_days ?? 30 },
          { name: "recurrence_days", label: "Renew every days", type: "number", defaultValue: editing.recurrence_days ?? "" },
          { name: "role_names", label: "Roles", type: "multi-select", options: roleOptions.map((item) => ({ value: item.name, label: item.name })) || [], defaultValue: Array.isArray(editing.rules?.role_names) ? (editing.rules.role_names as string[]).join(",") : "" },
          { name: "job_titles", label: "Job titles", defaultValue: Array.isArray(editing.rules?.job_titles) ? (editing.rules.job_titles as string[]).join(", ") : "" },
          { name: "org_unit_ids", label: "Organization units", type: "multi-select", options: unitOptions.map((item) => ({ value: item.id, label: item.name + " · " + item.unit_type })) || [], defaultValue: Array.isArray(editing.rules?.org_unit_ids) ? (editing.rules.org_unit_ids as string[]).join(",") : "" },
          { name: "exclude_user_ids", label: "Exclude specific people", type: "lookup-multi", endpoint: "/api/v1/people/page?status=active&page_size=20", defaultValue: Array.isArray(editing.rules?.exclude_user_ids) ? (editing.rules.exclude_user_ids as string[]).join(",") : "" },
          { name: "escalation_days", label: "Escalate after days", type: "number", required: true, defaultValue: typeof editing.rules?.escalation_days === "number" ? editing.rules.escalation_days : 7 },
        ]} includeEmptyFields={["description", "recurrence_days"]} />
        {versionsResult.ok && versionsResult.data?.length ? <details><summary>Policy history ({versionsResult.data.length} versions)</summary><div className="compact-list">{versionsResult.data.map((entry) => <div className="compact-row" key={entry.version}><div><strong>Version {entry.version} · {entry.snapshot.name}</strong><small>{new Date(entry.created_at).toLocaleString()} · {entry.snapshot.active ? "Active" : "Inactive"} · due within {entry.snapshot.due_days ?? 30} days{entry.snapshot.recurrence_days ? ` · renews every ${entry.snapshot.recurrence_days} days` : ""}</small></div></div>)}</div></details> : null}
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
        {evidence?.items.length ? <div className="compact-list">{evidence.items.map((item) => <div className="compact-row" key={item.id}><div><strong>{item.requirement} · {item.user_name}</strong><small>{item.evidence_type}: {item.evidence_type === "document" && item.reference.startsWith("file:") ? (item.attachment_status === "available" ? <a className="text-link" href={`/api/lms/compliance/evidence/${item.id}/download`}>Download document</a> : "Attachment awaiting scan") : item.evidence_type === "url" && /^https?:\/\//i.test(item.reference) ? <a className="text-link" href={item.reference} target="_blank" rel="noopener noreferrer">{item.reference}</a> : item.reference}{item.notes ? ` · ${item.notes}` : ""}</small></div><div className="button-row"><StatusBadge status={item.attachment_status === "pending_scan" ? "pending scan" : "pending review"} />{user.id !== item.user_id ? <>{item.attachment_status === "pending_scan" ? <small>Security scan clearance required</small> : <ApiActionButton endpoint={`/api/lms/compliance/evidence/${item.id}/verify`} label="Verify evidence" body={{}} />}<details><summary>Reject evidence</summary><ResourceForm title="Request corrected evidence" endpoint={`/api/lms/compliance/evidence/${item.id}/reject`} fields={[{ name: "reason", label: "Reason for rejection", type: "textarea", required: true }]} submitLabel="Reject and reopen" /></details></> : <small>A different reviewer must decide</small>}</div></div>)}</div> : <EmptyState title="Evidence queue is clear" description="Unverified learner evidence will appear here for review." icon={FileCheck2} />}
        {evidence && evidence.total > 50 ? <nav className="button-row" aria-label="Evidence review pages"><span>Page {evidencePage} of {Math.ceil(evidence.total / 50)} · {evidence.total} submissions</span>{evidencePage > 1 ? <Link className="button button-secondary" href={`/dashboard/compliance/admin?${new URLSearchParams({ status, page: String(page), evidence_page: String(evidencePage - 1) })}`}>Previous</Link> : null}{evidencePage * 50 < evidence.total ? <Link className="button button-secondary" href={`/dashboard/compliance/admin?${new URLSearchParams({ status, page: String(page), evidence_page: String(evidencePage + 1) })}`}>Next</Link> : null}</nav> : null}
      </Section>
      <Section eyebrow="Exception governance" title="Review exception requests">
        {exceptions?.length ? <div className="compact-list">{exceptions.map((item) => <div className="compact-row" key={item.id}><div><strong>{item.requirement} · {item.user_name}</strong><small>{item.reason}{item.expires_at ? ` · requested through ${new Date(item.expires_at).toLocaleDateString()}` : " · no expiry requested"}</small></div><div className="button-row"><StatusBadge status="requested" /><ApiActionButton endpoint={`/api/lms/compliance/exceptions/${item.id}/approve`} label="Approve" body={{}} confirmText="Approve this time-bound compliance exception?" /><ApiActionButton endpoint={`/api/lms/compliance/exceptions/${item.id}/reject`} label="Reject" body={{}} confirmText="Reject this compliance exception request?" /></div></div>)}</div> : <EmptyState title="No exception requests" description="New requests will remain pending here until an authorized reviewer decides." icon={ClipboardCheck} />}
      </Section>
    </DashboardShell>
  );
}
