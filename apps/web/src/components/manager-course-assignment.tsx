"use client";
import { FormEvent, useState } from "react";
type Course = { id: string; title: string; status: string };
export function ManagerCourseAssignment({ learnerId, courses }: { learnerId: string; courses: Course[] }) {
  const available = courses.filter(course => course.status === "published");
  const [courseId, setCourseId] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  async function assign(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setMessage(""); setError("");
    try {
      const dueAt = dueDate ? new Date(`${dueDate}T23:59:59`).toISOString() : null;
      const response = await fetch(`/api/lms/courses/${courseId}/manager-assignment`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ user_id: learnerId, due_at: dueAt }) });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Assignment failed.");
      setMessage(data.status === "waitlisted" ? "Learner added to the course waitlist." : "Course assigned to the learner.");
      setCourseId(""); setDueDate("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Assignment failed."); }
    finally { setBusy(false); }
  }
  if (!available.length) return <div className="empty-state"><p>No published courses are available for assignment.</p></div>;
  return <form className="studio-form" onSubmit={assign}><div className="form-grid">
    <label>Published course<select required value={courseId} onChange={event => setCourseId(event.target.value)}><option value="">Select a course</option>{available.map(course => <option key={course.id} value={course.id}>{course.title}</option>)}</select></label>
    <label>Due date (optional)<input type="date" value={dueDate} onChange={event => setDueDate(event.target.value)} /></label>
  </div><button className="button button-primary" type="submit" disabled={busy || !courseId}>{busy ? "Assigning…" : "Assign course"}</button>
    {message && <p className="form-success" role="status">{message}</p>}{error && <p className="form-error" role="alert">{error}</p>}
  </form>;
}
