"use client";

import { useState } from "react";
import { Check, RefreshCw } from "lucide-react";

type LearnerRow = {
  user_id: string;
  learner: string;
  email: string;
  enrollment_status: string;
  attendance_status: "present" | "absent" | "late" | "excused" | null;
};

export function SessionAttendanceRoster({ sessionId, initialRows }: { sessionId: string; initialRows: LearnerRow[] }) {
  const [rows, setRows] = useState(initialRows);
  const [busyId, setBusyId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function update(userId: string, status: LearnerRow["attendance_status"]) {
    if (!status || busyId) return;
    setBusyId(userId);
    setError("");
    setMessage("");
    try {
      const response = await fetch(`/api/lms/sessions/${sessionId}/attendance`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ user_id: userId, status }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(typeof payload.detail === "string" ? payload.detail : "Attendance could not be saved.");
      }
      setRows(current => current.map(row => row.user_id === userId ? { ...row, attendance_status: status } : row));
      setMessage("Attendance saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Attendance could not be saved.");
    } finally {
      setBusyId("");
    }
  }

  const marked = rows.filter(row => row.attendance_status !== null).length;
  return (
    <section className="soft-panel">
      <div className="section-heading compact">
        <div><span className="eyebrow">Session register</span><h3>Mark learner attendance</h3><p className="muted">{marked} of {rows.length} enrolled learners marked. Changes are saved immediately and audited.</p></div>
        <RefreshCw size={18}/>
      </div>
      {rows.length ? (
        <div className="table-wrap">
          <table className="data-table">
            <thead><tr><th>Learner</th><th>Enrollment</th><th>Attendance</th><th>Save</th></tr></thead>
            <tbody>
              {rows.map(row => (
                <tr key={row.user_id}>
                  <td><strong>{row.learner}</strong><small>{row.email}</small></td>
                  <td>{row.enrollment_status.replaceAll("_"," ")}</td>
                  <td>
                    <select
                      aria-label={`Attendance for ${row.learner}`}
                      value={row.attendance_status ?? ""}
                      disabled={busyId === row.user_id}
                      onChange={event => {
                        const next = event.target.value as LearnerRow["attendance_status"] | "";
                        if (next) void update(row.user_id, next);
                      }}
                    >
                      <option value="">Not marked</option>
                      <option value="present">Present</option>
                      <option value="late">Late</option>
                      <option value="absent">Absent</option>
                      <option value="excused">Excused</option>
                    </select>
                  </td>
                  <td>{busyId === row.user_id ? <span className="muted">Saving…</span> : row.attendance_status ? <span className="status-badge status-active"><Check size={12}/> Saved</span> : <span className="muted">Pending</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : <div className="empty-state"><p>No active or completed enrollments exist for this session&apos;s course.</p></div>}
      {error&&<p className="form-error" role="alert">{error}</p>}
      {message&&<p className="form-success" role="status">{message}</p>}
    </section>
  );
}
