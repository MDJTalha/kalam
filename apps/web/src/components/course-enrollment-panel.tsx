"use client";

import { useEffect, useMemo, useState } from "react";
import { CalendarClock, Check, UsersRound } from "lucide-react";
import { Notice, SectionCard } from "./ui";

type Person = { id: string; first_name: string; last_name: string; email: string; is_active: boolean };

type Props = { courseId: string; courseTitle: string };

export function CourseEnrollmentPanel({ courseId, courseTitle }: Props) {
  const [people, setPeople] = useState<Person[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [dueAt, setDueAt] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ kind: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    let active = true;
    fetch("/api/lms/people")
      .then((response) => response.ok ? response.json() : [])
      .then((data) => { if (active && Array.isArray(data)) setPeople(data.filter((item: Person) => item.is_active)); })
      .catch(() => undefined);
    return () => { active = false; };
  }, []);

  const selectedCount = selected.length;
  const allSelected = useMemo(() => people.length > 0 && selectedCount === people.length, [people.length, selectedCount]);

  function toggle(id: string) {
    setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  }

  async function assign() {
    if (!selected.length) return;
    setBusy(true); setMessage(null);
    try {
      const response = await fetch(`/api/lms/courses/${courseId}/enrollments/bulk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_ids: selected, due_at: dueAt ? new Date(dueAt).toISOString() : null }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Bulk assignment could not be completed.");
      setMessage({ kind: "success", text: `${data.length} learner assignment(s) confirmed for ${courseTitle}.` });
      setSelected([]);
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "Assignment failed" });
    } finally { setBusy(false); }
  }
  return (
    <SectionCard eyebrow="Enrollment governance" title="Assign learners" meta="Bulk assignment with optional due date">
      {message && <Notice kind={message.kind}>{message.text}</Notice>}
      <div className="form-grid">
        <label className="form-field">
          <span>Due date and time</span>
          <input type="datetime-local" value={dueAt} onChange={(event) => setDueAt(event.target.value)} />
          <small>Learners receive an in-app reminder as the due date approaches and when overdue.</small>
        </label>
        <div className="form-field">
          <span>Learners</span>
          <div className="inline-form">
            <button type="button" className="button button-secondary" onClick={() => setSelected(allSelected ? [] : people.map((item) => item.id))} disabled={!people.length}>
              <UsersRound size={15} /> {allSelected ? "Clear all" : "Select all"}
            </button>
            <span className="section-meta">{selectedCount} selected</span>
          </div>
          <div className="tag-list enrollment-list">
            {people.map((person) => (
              <label className="tag" key={person.id}>
                <input type="checkbox" checked={selected.includes(person.id)} onChange={() => toggle(person.id)} />
                {person.first_name} {person.last_name} · {person.email}
              </label>
            ))}
            {!people.length && <small>No active learners are available.</small>}
          </div>
        </div>
      </div>
      <div className="form-actions">
        <button type="button" className="button button-primary" onClick={() => void assign()} disabled={busy || !selected.length}>
          {busy ? <><CalendarClock size={15} /> Assigning…</> : <><Check size={15} /> Assign learners</>}
        </button>
      </div>
    </SectionCard>
  );
}
