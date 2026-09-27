"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
type Course = { course_id: string; title: string; position: number; is_required: boolean };
type Program = { id: string; title: string; description?: string | null; status: string; is_required: boolean; courses: Course[] };
type CatalogCourse = { id: string; title: string; status: string };
export function ProgramEditor({ initialProgram, catalog }: { initialProgram: Program; catalog: CatalogCourse[] }) {
  const router = useRouter();
  const [courses, setCourses] = useState(initialProgram.courses);
  const [title, setTitle] = useState(initialProgram.title);
  const [description, setDescription] = useState(initialProgram.description ?? "");
  const [required, setRequired] = useState(initialProgram.is_required);
  const [status, setStatus] = useState(initialProgram.status);
  const [courseId, setCourseId] = useState("");
  const [courseRequired, setCourseRequired] = useState(true);
  const [cohortName, setCohortName] = useState("");
  const [cohortCode, setCohortCode] = useState("");
  const [capacity, setCapacity] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [endsAt, setEndsAt] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const nextPosition = Math.max(0, ...courses.map(item => item.position)) + 1;
  const available = catalog.filter(item => !courses.some(course => course.course_id === item.id) && (status !== "published" || item.status === "published"));
  async function request(url: string, method: string, body?: object) {
    const response = await fetch(url, { method, headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Operation failed.");
    return data;
  }
  async function run(action: () => Promise<void>) {
    setBusy(true); setError(""); setMessage("");
    try { await action(); router.refresh(); }
    catch (err) { setError(err instanceof Error ? err.message : "Operation failed."); }
    finally { setBusy(false); }
  }

  function save(event: FormEvent) { event.preventDefault(); void run(async () => {
    const updated = await request(`/api/lms/programs/${initialProgram.id}`, "PATCH", { title: title.trim(), description: description.trim() || null, is_required: required });
    setTitle(updated.title); setMessage("Program details saved.");
  }); }
  function publish() { void run(async () => {
    const updated = await request(`/api/lms/programs/${initialProgram.id}`, "PATCH", { status: status === "published" ? "draft" : "published" });
    setStatus(updated.status); setMessage(updated.status === "published" ? "Program published." : "Program returned to draft.");
  }); }
  function add(event: FormEvent) { event.preventDefault(); if (!courseId) return; const selected = catalog.find(item => item.id === courseId);
    void run(async () => {
      await request(`/api/lms/programs/${initialProgram.id}/courses`, "POST", { course_id: courseId, position: nextPosition, is_required: courseRequired });
      setCourses(current => [...current, { course_id: courseId, title: selected?.title ?? "Course", position: nextPosition, is_required: courseRequired }]);
      setCourseId(""); setMessage("Course added to program.");
    });
  }
  function remove(course: Course) {
    if (!window.confirm(`Remove “${course.title}” from this program?`)) return;
    void run(async () => {
      await request(`/api/lms/programs/${initialProgram.id}/courses/${course.course_id}`, "DELETE");
      setCourses(current => current.filter(item => item.course_id !== course.course_id)); setMessage("Course removed.");
    });
  }
  function createCohort(event: FormEvent) { event.preventDefault(); void run(async () => {
    const result = await request(`/api/lms/programs/${initialProgram.id}/cohorts`, "POST", { name: cohortName.trim(), code: cohortCode.trim(), capacity: capacity ? Number(capacity) : null, starts_at: startsAt ? new Date(startsAt).toISOString() : null, ends_at: endsAt ? new Date(endsAt).toISOString() : null });
    router.push(`/dashboard/programs/cohorts/${result.id}`);
  }); }

  return <section className="data-panel" aria-label="Manage program">
    <div className="section-heading compact"><div><span className="eyebrow">Delivery setup</span><h2>Manage program</h2></div>
      <button type="button" className="button button-secondary" onClick={publish} disabled={busy || (status === "draft" && !courses.length)}>{status === "published" ? "Return to draft" : "Publish program"}</button></div>
    <p>Publish after adding published courses. Create a cohort, add learners, then launch it to assign the program courses.</p>
    {error && <p className="form-error" role="alert">{error}</p>}{message && <p className="form-success" role="status">{message}</p>}
    <form className="studio-form" onSubmit={save}><h3>Program details</h3><div className="form-grid">
      <label>Title<input required minLength={3} value={title} onChange={e => setTitle(e.target.value)} /></label>
      <label className="full-span">Description<textarea rows={3} value={description} onChange={e => setDescription(e.target.value)} /></label>
      <label><input type="checkbox" checked={required} onChange={e => setRequired(e.target.checked)} /> Required program</label></div>
      <button type="submit" className="button button-secondary" disabled={busy || !title.trim()}>Save details</button></form>
    <form className="studio-form" onSubmit={add}><h3>Add course</h3><div className="form-grid">
      <label>Course<select required value={courseId} onChange={e => setCourseId(e.target.value)}><option value="">Choose a course</option>{available.map(item => <option key={item.id} value={item.id}>{item.title}{item.status !== "published" ? " (draft)" : ""}</option>)}</select></label>
      <label><input type="checkbox" checked={courseRequired} onChange={e => setCourseRequired(e.target.checked)} /> Required course</label></div>
      <p className="form-help">The course will be step {nextPosition}.</p><button type="submit" className="button button-primary" disabled={busy || !courseId}>Add course</button></form>
    {!!courses.length && <div className="compact-list">{courses.map(item => <div className="compact-row" key={item.course_id}><div><strong>{item.position}. {item.title}</strong><small>{item.is_required ? "Required" : "Elective"}</small></div><button type="button" className="button button-secondary" disabled={busy} onClick={() => remove(item)}>Remove</button></div>)}</div>}

    <form className="studio-form" onSubmit={createCohort}><h3>Create cohort</h3>
      <div className="form-grid"><label>Name<input required minLength={3} value={cohortName} onChange={e => setCohortName(e.target.value)} /></label>
        <label>Unique code<input required minLength={2} pattern="[A-Za-z0-9_-]+" value={cohortCode} onChange={e => setCohortCode(e.target.value)} /></label>
        <label>Capacity (optional)<input type="number" min={1} value={capacity} onChange={e => setCapacity(e.target.value)} /></label>
        <label>Starts (optional)<input type="datetime-local" value={startsAt} onChange={e => setStartsAt(e.target.value)} /></label>
        <label>Ends (optional)<input type="datetime-local" min={startsAt} value={endsAt} onChange={e => setEndsAt(e.target.value)} /></label></div>
      <button type="submit" className="button button-primary" disabled={busy}>Create cohort</button>
    </form>
  </section>;
}
