"use client";

import { useState } from "react";
import { CheckCircle2, Circle, LogIn, PlayCircle } from "lucide-react";

type Course = {
  id: string;
  title: string;
  description?: string | null;
  estimated_minutes?: number | null;
  modules: Array<{
    id: string;
    title: string;
    lessons: Array<{ id: string; title: string; content_type: string; content: Record<string, unknown> }>;
  }>;
  enrollment?: { id: string; status: string } | null;
};

export function CoursePlayer({ course }: { course: Course }) {
  const [enrollmentId, setEnrollmentId] = useState(course.enrollment?.id ?? null);
  const [status, setStatus] = useState(course.enrollment?.status ?? "not_enrolled");
  const [completedLessons, setCompletedLessons] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function enroll() {
    setBusy(true);
    setMessage("");
    try {
      const origin = process.env.NEXT_PUBLIC_API_ORIGIN || "http://localhost:8000";
      const response = await fetch(`${origin}/api/v1/courses/${course.id}/enroll`, {
        method: "POST",
        credentials: "include",
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Enrollment failed");
      setEnrollmentId(data.id);
      setStatus(data.status);
      setMessage("Enrollment confirmed. You can now work through the lessons.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Enrollment failed");
    } finally {
      setBusy(false);
    }
  }

  async function complete(lessonId: string) {
    if (!enrollmentId) return;
    setBusy(true);
    setMessage("");
    try {
      const origin = process.env.NEXT_PUBLIC_API_ORIGIN || "http://localhost:8000";
      const response = await fetch(
        `${origin}/api/v1/courses/my/enrollments/${enrollmentId}/lessons/${lessonId}/complete`,
        { method: "POST", credentials: "include" },
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to save progress");
      setCompletedLessons((items) => items.includes(lessonId) ? items : [...items, lessonId]);
      setStatus(data.course_status || data.status || status);
      setMessage(data.status === "completed" ? "Course completed. Your learning record is now complete." : "Lesson completion saved.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to save progress");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="data-panel">
      <div className="player-toolbar">
        <div><span className="eyebrow">Learner player</span><h2>{status === "not_enrolled" ? "Start this course" : "Continue learning"}</h2></div>
        {status === "not_enrolled" ? (
          <button className="button button-primary" onClick={enroll} disabled={busy}><LogIn size={15}/>{busy ? "Enrolling…" : "Enroll now"}</button>
        ) : <span className="status-badge success">{status}</span>}
      </div>
      {message && <div className="form-success" role="status">{message}</div>}
      <div className="curriculum-list">
        {course.modules.map((module, index) => (
          <section className="curriculum-module" key={module.id}>
            <div className="curriculum-heading"><span>{String(index + 1).padStart(2,"0")}</span><div><strong>{module.title}</strong><small>{module.lessons.length} lesson(s)</small></div></div>
            <div className="compact-list">
              {module.lessons.map((lesson) => {
                const done = completedLessons.includes(lesson.id);
                return (
                  <div className="compact-row" key={lesson.id}>
                    <div><strong>{lesson.title}</strong><small>{lesson.content_type}</small></div>
                    {done ? <CheckCircle2 className="success-icon" size={18}/> : status !== "not_enrolled" ? <button className="icon-text-button" onClick={() => complete(lesson.id)} disabled={busy}><PlayCircle size={16}/> Complete</button> : <Circle size={17}/>}
                  </div>
                );
              })}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
