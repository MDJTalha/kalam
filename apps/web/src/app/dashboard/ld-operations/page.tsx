import Link from "next/link";
import { DashboardShell } from "@/components/dashboard-shell";
import { LdQueueActions } from "@/components/ld-queue-actions";
import { LdRemindersButton } from "@/components/ld-reminders-button";
import { apiJson, requireUser } from "@/lib/server-api";
type Item = { id: string; course_id: string; course_title: string; learner_id: string; learner_name: string; learner_email: string; status: string; requested_at: string; source: string };
type Queue = { pending_approval: number; waitlisted: number; total: number; page: number; page_size: number; items: Item[] };

export default async function LdOperationsPage({ searchParams }: { searchParams: Promise<{ page?: string; status?: string; q?: string }> }) {
  const user = await requireUser<{ permissions?: string[] }>();
  if (!user.permissions?.includes("courses.manage")) {
    return <DashboardShell title="L&D operations" eyebrow="Learning delivery"><section className="data-panel" role="alert"><h2>Access restricted</h2><p>Enrollment decisions require course management permission.</p></section></DashboardShell>;
  }
  const params = await searchParams;
  const page = Math.max(1, Number.parseInt(params.page ?? "1", 10) || 1);
  const status = ["all", "pending_approval", "waitlisted"].includes(params.status ?? "") ? params.status! : "all";
  const query = (params.q ?? "").trim().slice(0, 100);
  const url = `/api/v1/courses/operations/enrollment-queue?page=${page}&page_size=25&status=${status}&q=${encodeURIComponent(query)}`;
  const queue = await apiJson<Queue>(url);
  const link = (target: number) => `/dashboard/ld-operations?page=${target}&status=${status}&q=${encodeURIComponent(query)}`;
  return <DashboardShell title="L&D operations" eyebrow="Learning delivery">
    <div className="stat-grid">
      <div className="stat-card"><span>Approval requests</span><strong>{queue?.pending_approval ?? "—"}</strong><small>Awaiting a decision</small></div>
      <div className="stat-card"><span>Waitlisted</span><strong>{queue?.waitlisted ?? "—"}</strong><small>Waiting for capacity</small></div>
      <div className="stat-card"><span>Matching queue items</span><strong>{queue?.total ?? "—"}</strong><small>Across this tenant</small></div>
    </div>
    <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Daily operations</span><h2>Enrollment decisions</h2></div>
      <Link className="text-link" href="/dashboard/ld-operations/equivalencies">Course equivalencies →</Link></div>
      <p>Review requests in arrival order. Approval admits a learner when capacity is available; a full course keeps them waitlisted.</p>
      <form className="form-grid" method="get" action="/dashboard/ld-operations">
        <label className="form-field"><span>Search learner or course</span><input name="q" type="search" maxLength={100} defaultValue={query} placeholder="Name, email, or course" /></label>
        <label className="form-field"><span>Status</span><select name="status" defaultValue={status}><option value="all">All open items</option><option value="pending_approval">Approval requests</option><option value="waitlisted">Waitlisted</option></select></label>
        <div className="form-actions"><button type="submit" className="button button-secondary">Apply filters</button></div>
      </form>

      {queue ? queue.items.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th scope="col">Learner</th><th scope="col">Course</th><th scope="col">Request</th><th scope="col">Status</th><th scope="col">Decision</th></tr></thead><tbody>
        {queue.items.map(item => <tr key={item.id}>
          <td><strong>{item.learner_name}</strong><small>{item.learner_email}</small></td>
          <td><Link className="text-link" href={`/dashboard/course-studio/${item.course_id}`}>{item.course_title}</Link></td>
          <td><time dateTime={item.requested_at}>{new Date(item.requested_at).toLocaleDateString()}</time><small>{item.source}</small></td>
          <td><span className="status-badge">{item.status.replaceAll("_", " ")}</span></td>
          <td><LdQueueActions courseId={item.course_id} enrollmentId={item.id} status={item.status} /></td>
        </tr>)}</tbody></table></div> : <div className="empty-state"><h3>No matching open requests</h3><p>Try another filter or check back when learners request enrollment.</p></div>
        : <div className="empty-state" role="alert"><h3>Queue unavailable</h3><p>Check the service and try again.</p></div>}
      {queue && <div className="form-actions"><span className="section-meta">Page {queue.page} · {queue.total} matching items</span>
        {queue.page > 1 && <Link className="button button-secondary" href={link(queue.page - 1)}>Previous</Link>}
        {queue.page * queue.page_size < queue.total && <Link className="button button-secondary" href={link(queue.page + 1)}>Next</Link>}</div>}
    </section>
    <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Assignment follow-up</span><h2>Due date reminders</h2></div></div>
      <p>Run the tenant reminder check for assignments approaching their due date or newly overdue. Repeated runs do not create duplicate notices for the same reminder window.</p>
      <LdRemindersButton />
    </section>
  </DashboardShell>;
}
