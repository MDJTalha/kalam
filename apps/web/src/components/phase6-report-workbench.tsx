"use client";

/* CSV download endpoints intentionally use native anchors. */
 /* eslint-disable @next/next/no-html-link-for-pages */
import { useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  CalendarClock,
  ChevronLeft,
  ChevronRight,
  ClipboardCheck,
  Download,
  FileText,
  Layers3,
  Network,
  Play,
  Save,
  Search,
  UsersRound,
} from "lucide-react";

type CourseRow = { course_id: string; course: string; status: string; enrollments: number; completions: number; completion_rate: number };
type Performance = { courses: CourseRow[]; total: number; offset?: number; limit?: number };
type Effectiveness = { completed: number; in_progress: number; completion_rate: number; average_days_to_complete: number | null; measured_completions: number; evidence_model: string };
type Manager = { manager_id: string; manager: string; team_members: number; enrollments: number; completions: number; completion_rate: number };
type Risk = { total: number; open: number; overdue: number; risk_band: string };
type Assessment = { assessment_id: string; assessment: string; passing_score: number; attempts: number; submitted_attempts: number; passed_attempts: number; failed_attempts: number; average_score: number; pass_rate: number };
type Engagement = { enrolled_learners: number; active_learners: number; learners_with_completion: number; learner_activation_rate: number; learner_completion_reach: number; enrollment_records: number };
type OrgUnit = { org_unit_id: string; org_unit: string; people: number; enrollments: number; completions: number; completion_rate: number };
type Skill = { skill_id: string; skill: string; required_proficiency: number; average_proficiency: number; evidence_count: number; coverage_rate: number; requirement_met_rate: number; gap_to_requirement: number };
type SavedReport = { id: string; name: string; report_type: string; definition: Record<string, unknown>; visibility: "private" | "tenant"; enabled: boolean; owner_id: string };
type Schedule = { id: string; saved_report_id: string; frequency: string; next_run_at: string; recipients: string[]; status: string };
type RunResult = { id: string; name: string; report_type: string; generated_at: string; data: Record<string, unknown> };

const PAGE_SIZE = 25;

export function Phase6ReportWorkbench({
  performance,
  effectiveness,
  managers,
  risk,
  assessments,
  engagement,
  organization,
  skills,
  saved,
  schedules,
  canManage,
}: {
  performance: Performance | null;
  effectiveness: Effectiveness | null;
  managers: Manager[];
  risk: Risk | null;
  assessments: Assessment[];
  engagement: Engagement | null;
  organization: OrgUnit[];
  skills: Skill[];
  saved: SavedReport[];
  schedules: Schedule[];
  canManage: boolean;
}) {
  const [courseRows, setCourseRows] = useState<CourseRow[]>(performance?.courses ?? []);
  const [courseTotal, setCourseTotal] = useState(performance?.total ?? performance?.courses?.length ?? 0);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [sort, setSort] = useState<"course" | "enrollments" | "completions" | "completion_rate">("enrollments");
  const [direction, setDirection] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [courseLoading, setCourseLoading] = useState(false);
  const [courseError, setCourseError] = useState("");
  const [savedItems, setSavedItems] = useState(saved);
  const [scheduleItems, setScheduleItems] = useState(schedules);
  const [reportName, setReportName] = useState("");
  const [reportType, setReportType] = useState("course_performance");
  const [visibility, setVisibility] = useState<"private" | "tenant">("private");
  const [scheduleId, setScheduleId] = useState(saved[0]?.id ?? "");
  const [frequency, setFrequency] = useState("weekly");
  const [nextRun, setNextRun] = useState("");
  const [recipients, setRecipients] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [runResults, setRunResults] = useState<Record<string, RunResult>>({});
  const [runningId, setRunningId] = useState<string | null>(null);

  const totalPages = Math.max(1, Math.ceil(courseTotal / PAGE_SIZE));

  useEffect(() => {
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      setCourseLoading(true);
      setCourseError("");
      try {
        const query = new URLSearchParams({
          offset: String((page - 1) * PAGE_SIZE),
          limit: String(PAGE_SIZE),
          sort,
          direction,
        });
        if (search.trim()) query.set("search", search.trim());
        if (status !== "all") query.set("status", status);
        const response = await fetch("/api/lms/reports/course-performance?" + query.toString(), {
          method: "GET",
          headers: { Accept: "application/json" },
          cache: "no-store",
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload.detail || "Course performance could not be loaded.");
        if (!cancelled) {
          setCourseRows(payload.courses ?? []);
          setCourseTotal(payload.total ?? 0);
        }
      } catch (err) {
        if (!cancelled) setCourseError(err instanceof Error ? err.message : "Course performance could not be loaded.");
      } finally {
        if (!cancelled) setCourseLoading(false);
      }
    }, 220);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [direction, page, search, sort, status]);

  const pageSummary = useMemo(() => {
    if (!courseTotal) return "0 records";
    const start = (page - 1) * PAGE_SIZE + 1;
    const end = Math.min(page * PAGE_SIZE, courseTotal);
    return start + "–" + end + " of " + courseTotal;
  }, [courseTotal, page]);

  async function createSavedReport() {
    setError("");
    setMessage("");
    try {
      const response = await fetch("/api/lms/reports/saved", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: reportName.trim(),
          report_type: reportType,
          visibility,
          enabled: true,
          definition: { search, status, sort, direction, page_size: PAGE_SIZE },
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Saved report could not be created.");
      const savedItem: SavedReport = {
        id: data.id,
        name: data.name,
        report_type: data.report_type,
        definition: { search, status, sort, direction, page_size: PAGE_SIZE },
        visibility,
        enabled: true,
        owner_id: data.owner_id ?? "",
      };
      setSavedItems((items) => [savedItem, ...items]);
      setScheduleId(data.id);
      setReportName("");
      setMessage("Report definition saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save report.");
    }
  }

  async function runSavedReport(item: SavedReport) {
    setError("");
    setMessage("");
    setRunningId(item.id);
    try {
      const response = await fetch("/api/lms/reports/saved/" + item.id + "/run", { method: "POST" });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Report could not be executed.");
      setRunResults((results) => ({ ...results, [item.id]: data }));
      setMessage("Report executed from its saved definition.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to execute report.");
    } finally {
      setRunningId(null);
    }
  }

  async function createSchedule() {
    setError("");
    setMessage("");
    if (!scheduleId || !nextRun || !recipients.trim()) {
      setError("Select a saved report, future run time, and at least one recipient.");
      return;
    }
    try {
      const recipientList = recipients.split(",").map((item) => item.trim()).filter(Boolean);
      const response = await fetch("/api/lms/reports/saved/" + scheduleId + "/schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          frequency,
          next_run_at: new Date(nextRun).toISOString(),
          recipients: recipientList,
          status: "active",
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Schedule could not be created.");
      setScheduleItems((items) => [
        ...items,
        { ...data, id: data.id, saved_report_id: scheduleId, recipients: recipientList, status: data.status ?? "active" },
      ]);
      setNextRun("");
      setRecipients("");
      setMessage("Report schedule created.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to schedule report.");
    }
  }

  function summarizeRun(data: Record<string, unknown>) {
    return Object.entries(data).slice(0, 5).map(([key, value]) => {
      const label = key.replaceAll("_", " ");
      const display = Array.isArray(value) ? value.length + " records" : String(value);
      return label.charAt(0).toUpperCase() + label.slice(1) + ": " + display;
    });
  }

  return (
    <div className="phase6-report-stack">
      {(error || message) && (
        <div className={error ? "form-error" : "form-success"} role={error ? "alert" : "status"} aria-live="polite">
          {error || message}
        </div>
      )}

      <section className="data-panel phase6-filter-panel" aria-labelledby="phase6-course-performance">
        <div className="section-heading compact">
          <div>
            <span className="eyebrow">Advanced reporting</span>
            <h2 id="phase6-course-performance">Course performance workbench</h2>
          </div>
          <span className="section-meta">{pageSummary}</span>
        </div>
        <div className="filter-bar phase6-report-filters">
          <label className="filter-control">
            <span>Search</span>
            <div className="phase6-search">
              <Search size={14} aria-hidden="true" />
              <input aria-label="Search courses" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="Course name" />
            </div>
          </label>
          <label className="filter-control">
            <span>Status</span>
            <select value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}>
              <option value="all">All statuses</option>
              <option value="published">Published</option>
              <option value="draft">Draft</option>
              <option value="review">Review</option>
              <option value="archived">Archived</option>
            </select>
          </label>
          <label className="filter-control">
            <span>Sort</span>
            <select value={sort} onChange={(event) => { setSort(event.target.value as typeof sort); setPage(1); }}>
              <option value="enrollments">Enrollments</option>
              <option value="completions">Completions</option>
              <option value="completion_rate">Completion rate</option>
              <option value="course">Course</option>
            </select>
          </label>
          <button className="button button-secondary" type="button" onClick={() => { setDirection((value) => value === "desc" ? "asc" : "desc"); setPage(1); }} aria-label={"Sort " + (direction === "desc" ? "ascending" : "descending")}>
            {direction === "desc" ? "Descending" : "Ascending"}
          </button>
        </div>
        {courseError && <div className="form-error" role="alert">{courseError}</div>}
        {courseLoading ? (
          <div className="loading-state" aria-live="polite">Loading course performance…</div>
        ) : courseRows.length ? (
          <div className="table-wrap" aria-live="polite">
            <table className="data-table">
              <thead><tr><th scope="col">Course</th><th scope="col">Status</th><th scope="col">Enrollments</th><th scope="col">Completions</th><th scope="col">Rate</th></tr></thead>
              <tbody>
                {courseRows.map((item) => (
                  <tr key={item.course_id}>
                    <td><strong>{item.course}</strong></td>
                    <td>{item.status}</td>
                    <td>{item.enrollments}</td>
                    <td>{item.completions}</td>
                    <td><strong>{item.completion_rate}%</strong></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state"><BarChart3 size={26} /><h3>No matching course data</h3><p>Adjust the filters or record learning activity to populate this report.</p></div>
        )}
        <div className="report-pagination" aria-label="Course performance pagination">
          <span className="section-meta">Page {page} of {totalPages}</span>
          <div className="modal-actions">
            <button className="button button-secondary" type="button" disabled={page <= 1 || courseLoading} onClick={() => setPage((value) => Math.max(1, value - 1))}><ChevronLeft size={14} /> Previous</button>
            <button className="button button-secondary" type="button" disabled={page >= totalPages || courseLoading} onClick={() => setPage((value) => Math.min(totalPages, value + 1))}>Next <ChevronRight size={14} /></button>
          </div>
        </div>
      </section>

      <div className="two-column">
        <section className="data-panel">
          <div className="section-heading compact"><div><span className="eyebrow">Learning effectiveness</span><h2>Outcome efficiency</h2></div><BarChart3 size={20} /></div>
          <div className="metric-strip">
            <span><b>{effectiveness?.completed ?? 0}</b> completed</span>
            <span><b>{effectiveness?.completion_rate ?? 0}%</b> completion</span>
            <span><b>{effectiveness?.average_days_to_complete ?? "—"}</b> avg days</span>
            <span><b>{effectiveness?.in_progress ?? 0}</b> in progress</span>
          </div>
          <div className="callout" style={{ marginTop: 12 }}>Average completion time is calculated only from persisted enrollment and completion timestamps ({effectiveness?.measured_completions ?? 0} measured completions).</div>
        </section>
        <section className="data-panel">
          <div className="section-heading compact"><div><span className="eyebrow">Compliance intelligence</span><h2>Exposure</h2></div></div>
          <div className="metric-strip">
            <span><b>{risk?.total ?? 0}</b> total</span>
            <span><b>{risk?.open ?? 0}</b> open</span>
            <span><b>{risk?.overdue ?? 0}</b> overdue</span>
            <span><b>{risk?.risk_band ?? "—"}</b> derived band</span>
          </div>
          <div className="callout" style={{ marginTop: 12 }}>This band is a deterministic reporting classification from persisted assignment status and due dates.</div>
        </section>
      </div>

      <div className="two-column">
        <section className="data-panel">
          <div className="section-heading compact"><div><span className="eyebrow">Assessment intelligence</span><h2>Assessment performance</h2></div><ClipboardCheck size={20} /></div>
          {assessments.length ? (
            <div className="table-wrap"><table className="data-table"><thead><tr><th scope="col">Assessment</th><th scope="col">Attempts</th><th scope="col">Avg score</th><th scope="col">Pass rate</th></tr></thead><tbody>
              {assessments.slice(0, 12).map((item) => <tr key={item.assessment_id}><td><strong>{item.assessment}</strong></td><td>{item.submitted_attempts}/{item.attempts}</td><td>{item.average_score}%</td><td><strong>{item.pass_rate}%</strong></td></tr>)}
            </tbody></table></div>
          ) : <div className="empty-state"><ClipboardCheck size={24} /><h3>No assessment evidence</h3><p>Assessment results will populate as attempts are submitted.</p></div>}
        </section>
        <section className="data-panel">
          <div className="section-heading compact"><div><span className="eyebrow">Learner engagement</span><h2>Participation reach</h2></div><UsersRound size={20} /></div>
          <div className="metric-strip">
            <span><b>{engagement?.enrolled_learners ?? 0}</b> enrolled learners</span>
            <span><b>{engagement?.active_learners ?? 0}</b> active</span>
            <span><b>{engagement?.learner_activation_rate ?? 0}%</b> activation</span>
            <span><b>{engagement?.learner_completion_reach ?? 0}%</b> completion reach</span>
          </div>
          <div className="callout" style={{ marginTop: 12 }}>Engagement is reported from persisted enrollment status records.</div>
        </section>
      </div>

      <section className="data-panel">
        <div className="section-heading compact"><div><span className="eyebrow">Manager & team intelligence</span><h2>Team learning performance</h2></div><span className="section-meta">{managers.length} managers</span></div>
        {managers.length ? (
          <div className="table-wrap"><table className="data-table"><thead><tr><th scope="col">Manager</th><th scope="col">Team members</th><th scope="col">Enrollments</th><th scope="col">Completions</th><th scope="col">Rate</th></tr></thead><tbody>
            {managers.map((item) => <tr key={item.manager_id}><td><strong>{item.manager}</strong></td><td>{item.team_members}</td><td>{item.enrollments}</td><td>{item.completions}</td><td><strong>{item.completion_rate}%</strong></td></tr>)}
          </tbody></table></div>
        ) : <div className="empty-state"><UsersRound size={24} /><h3>No manager-linked learning data</h3><p>Team reporting will populate when learners have reporting relationships and learning records.</p></div>}
      </section>

      <div className="two-column">
        <section className="data-panel">
          <div className="section-heading compact"><div><span className="eyebrow">Organizational analytics</span><h2>Learning by org unit</h2></div><Network size={20} /></div>
          {organization.length ? <div className="compact-list">{organization.slice(0, 12).map((item) => <div className="compact-row" key={item.org_unit_id}><div><strong>{item.org_unit}</strong><small>{item.people} people · {item.enrollments} enrollments · {item.completions} completions</small></div><span className="proficiency">{item.completion_rate}%</span></div>)}</div> : <div className="empty-state"><Network size={24} /><h3>No organizational learning data</h3><p>Org-unit analytics will populate when workforce records have organizational placement.</p></div>}
        </section>
        <section className="data-panel">
          <div className="section-heading compact"><div><span className="eyebrow">Skill intelligence</span><h2>Capability coverage</h2></div><Layers3 size={20} /></div>
          {skills.length ? <div className="compact-list">{skills.slice(0, 10).map((item) => <div className="compact-row" key={item.skill_id}><div><strong>{item.skill}</strong><small>Evidence {item.coverage_rate}% · met {item.requirement_met_rate}% · required {item.required_proficiency}</small></div><span className="proficiency">gap {item.gap_to_requirement}</span></div>)}</div> : <div className="empty-state"><Layers3 size={24} /><h3>No role-skill reporting data</h3><p>Skill intelligence will populate when role requirements and learner evidence are mapped.</p></div>}
        </section>
      </div>

      <section className="data-panel">
        <div className="section-heading compact"><div><span className="eyebrow">Data export & evidence</span><h2>Operational datasets</h2></div><Download size={20} /></div>
        <div className="module-grid">
          <a className="module-card" href="/api/reports/export/people"><div className="module-icon"><FileText size={19} /></div><div><h3>People CSV</h3><p>Tenant-scoped workforce identity and job data.</p></div></a>
          <a className="module-card" href="/api/reports/export/enrollments"><div className="module-icon"><FileText size={19} /></div><div><h3>Enrollment CSV</h3><p>Registrations, statuses, sources and completion dates.</p></div></a>
          <a className="module-card" href="/api/reports/export/course-performance"><div className="module-icon"><FileText size={19} /></div><div><h3>Course performance CSV</h3><p>Course-level enrollment, completion and completion-rate evidence.</p></div></a>
          <a className="module-card" href="/api/reports/export/compliance"><div className="module-icon"><FileText size={19} /></div><div><h3>Compliance CSV</h3><p>Requirement assignments, status and due-date evidence.</p></div></a>
        </div>
      </section>

      {canManage && (
        <div className="two-column">
          <section className="data-panel">
            <div className="section-heading compact"><div><span className="eyebrow">Saved reports</span><h2>Report library</h2></div><Save size={20} /></div>
            <div className="form-grid">
              <label className="form-field full"><span>Name</span><input value={reportName} onChange={(event) => setReportName(event.target.value)} placeholder="Monthly learning effectiveness" /></label>
              <label className="form-field"><span>Report type</span><select value={reportType} onChange={(event) => setReportType(event.target.value)}><option value="course_performance">Course performance</option><option value="learning_effectiveness">Learning effectiveness</option><option value="compliance_risk">Compliance risk</option><option value="executive_summary">Executive summary</option></select></label>
              <label className="form-field"><span>Visibility</span><select value={visibility} onChange={(event) => setVisibility(event.target.value as typeof visibility)}><option value="private">Private</option><option value="tenant">Tenant</option></select></label>
            </div>
            <button className="button button-primary" type="button" disabled={!reportName.trim()} onClick={createSavedReport}><Save size={15} /> Save report definition</button>
            <div className="compact-list phase6-saved-list">
              {savedItems.map((item) => (
                <div className="compact-row" key={item.id}>
                  <div><strong>{item.name}</strong><small>{item.report_type} · {item.visibility}{runResults[item.id] ? " · Last run " + new Date(runResults[item.id].generated_at).toLocaleString() : ""}</small>
                  {runResults[item.id] && <div className="phase6-run-summary">{summarizeRun(runResults[item.id].data).slice(0, 4).map((line) => <span key={line}>{line}</span>)}</div>}</div>
                  <button type="button" className="button button-secondary" disabled={runningId === item.id || !item.enabled} onClick={() => runSavedReport(item)}><Play size={14} />{runningId === item.id ? "Running…" : "Run report"}</button>
                </div>
              ))}
              {!savedItems.length && <div className="empty-state"><Save size={24} /><h3>No saved reports yet</h3><p>Save a report definition to reuse its filters and run it again later.</p></div>}
            </div>
          </section>

          <section className="data-panel">
            <div className="section-heading compact"><div><span className="eyebrow">Scheduled reporting</span><h2>Delivery calendar</h2></div><CalendarClock size={20} /></div>
            <div className="form-grid">
              <label className="form-field full"><span>Saved report</span><select value={scheduleId} onChange={(event) => setScheduleId(event.target.value)}><option value="">Select report</option>{savedItems.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
              <label className="form-field"><span>Frequency</span><select value={frequency} onChange={(event) => setFrequency(event.target.value)}><option value="daily">Daily</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option></select></label>
              <label className="form-field"><span>Next run</span><input type="datetime-local" value={nextRun} onChange={(event) => setNextRun(event.target.value)} /></label>
              <label className="form-field full"><span>Recipients</span><input value={recipients} onChange={(event) => setRecipients(event.target.value)} placeholder="hr@example.com, ld@example.com" /></label>
            </div>
            <button className="button button-secondary" type="button" onClick={createSchedule} disabled={!scheduleId || !nextRun || !recipients.trim()}><CalendarClock size={15} /> Schedule delivery</button>
            <div className="compact-list phase6-saved-list">{scheduleItems.map((item) => <div className="compact-row" key={item.id}><div><strong>{item.frequency} · {new Date(item.next_run_at).toLocaleString()}</strong><small>{item.recipients.join(", ")} · {item.status}</small></div></div>)}</div>
            <div className="callout" style={{ marginTop: 12 }}>Scheduling persists a validated delivery plan and the background worker executes due reports with persisted run history. External SMTP delivery remains deployment-dependent.</div>
          </section>
        </div>
      )}
    </div>
  );
}
