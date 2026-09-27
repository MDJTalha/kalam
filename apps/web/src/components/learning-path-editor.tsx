"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

type Item = { course_id: string; title: string; position: number; prerequisite_item_id?: string | null };
type Path = { id: string; title: string; description?: string | null; status: string; items: Item[] };
type Course = { id: string; title: string; status: string };

export function LearningPathEditor({ initialPath, courses }: { initialPath: Path; courses: Course[] }) {
  const router = useRouter();
  const [items, setItems] = useState(initialPath.items);
  const [title, setTitle] = useState(initialPath.title);
  const [description, setDescription] = useState(initialPath.description ?? "");
  const [status, setStatus] = useState(initialPath.status);
  const [courseId, setCourseId] = useState("");
  const [prerequisiteId, setPrerequisiteId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const available = courses.filter(course => !items.some(item => item.course_id === course.id));
  const nextPosition = Math.max(0, ...items.map(item => item.position)) + 1;

  async function request(url: string, method: string, body?: object) {
    const response = await fetch(url, { method, headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "The path could not be updated.");
    return data;
  }
  async function run(action: () => Promise<void>) {
    setBusy(true); setError(""); setMessage("");
    try { await action(); router.refresh(); }
    catch (err) { setError(err instanceof Error ? err.message : "The path could not be updated."); }
    finally { setBusy(false); }
  }

  function save(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      const result = await request(`/api/lms/programs/paths/${initialPath.id}`, "PATCH", { title: title.trim(), description: description.trim() || null });
      setTitle(result.title); setMessage("Path details saved.");
    });
  }
  function add(event: FormEvent) {
    event.preventDefault();
    if (!courseId) return;
    const course = courses.find(item => item.id === courseId);
    void run(async () => {
      await request(`/api/lms/programs/paths/${initialPath.id}/courses`, "POST", { course_id: courseId, position: nextPosition, prerequisite_item_id: prerequisiteId || null });
      setItems(current => [...current, { course_id: courseId, title: course?.title ?? "Course", position: nextPosition, prerequisite_item_id: prerequisiteId || null }]);
      setCourseId(""); setPrerequisiteId(""); setMessage("Course added to path.");
    });
  }
  function remove(item: Item) {
    if (!window.confirm(`Remove “${item.title}” from this learning path?`)) return;
    void run(async () => {
      await request(`/api/lms/programs/paths/${initialPath.id}/courses/${item.course_id}`, "DELETE");
      setItems(current => current.filter(entry => entry.course_id !== item.course_id));
      setMessage("Course removed from path.");
    });
  }
  function changeStatus(next: "draft" | "published") {
    void run(async () => {
      const result = await request(`/api/lms/programs/paths/${initialPath.id}`, "PATCH", { status: next });
      setStatus(result.status); setMessage(next === "published" ? "Path published for learners." : "Path returned to draft.");
    });
  }

  return <section className="data-panel" aria-label="Manage learning path">
    <div className="section-heading compact"><div><span className="eyebrow">Course management</span><h2>Manage this path</h2></div>
      <button className="button button-secondary" type="button" disabled={busy || (status === "draft" && !items.length)} onClick={() => changeStatus(status === "published" ? "draft" : "published")}>{status === "published" ? "Return to draft" : "Publish path"}</button></div>
    <p>Publish after adding at least one published course. Learners can see published paths.</p>
    {error && <div className="form-error" role="alert">{error}</div>}
    {message && <div className="form-success" role="status">{message}</div>}
    <form className="studio-form" onSubmit={save}>
      <div className="form-grid"><label>Path title<input required minLength={3} value={title} onChange={event => setTitle(event.target.value)} /></label>
        <label className="full-span">Description<textarea rows={3} value={description} onChange={event => setDescription(event.target.value)} /></label></div>
      <button className="button button-secondary" type="submit" disabled={busy || !title.trim()}>Save details</button>
    </form>
    <form className="studio-form" onSubmit={add}>
      <h3>Add a course</h3>
      <div className="form-grid"><label>Course<select required value={courseId} onChange={event => setCourseId(event.target.value)}>
        <option value="">Choose a course</option>{available.filter(course => status !== "published" || course.status === "published").map(course => <option key={course.id} value={course.id}>{course.title}{course.status !== "published" ? " (draft)" : ""}</option>)}</select></label>
        <label>Prerequisite course<select value={prerequisiteId} onChange={event => setPrerequisiteId(event.target.value)}><option value="">None</option>{items.map(item => <option key={item.course_id} value={item.course_id}>{item.title}</option>)}</select></label></div>
      <p className="form-help">New course will be step {nextPosition}. A prerequisite must be an earlier step in this path.</p>
      <button className="button button-primary" type="submit" disabled={busy || !courseId}>Add course</button>
    </form>
    {!!items.length && <div className="compact-list">{items.map(item => <div className="compact-row" key={item.course_id}>
      <div><strong>{item.position}. {item.title}</strong><small>{item.prerequisite_item_id ? "Requires " + (items.find(entry => entry.course_id === item.prerequisite_item_id)?.title ?? "earlier course") : "No prerequisite"}</small></div>
      <button className="button button-secondary" type="button" disabled={busy} onClick={() => remove(item)}>Remove</button>
    </div>)}</div>}
  </section>;
}
