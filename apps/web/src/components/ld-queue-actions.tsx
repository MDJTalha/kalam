"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Check, Loader2, X } from "lucide-react";
type Props = { courseId: string; enrollmentId: string; status: string };
export function LdQueueActions({ courseId, enrollmentId, status }: Props) {
  const router = useRouter();
  const [busy, setBusy] = useState<"approve" | "reject" | null>(null);
  const [reasonOpen, setReasonOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  async function act(action: "approve" | "reject") {
    if (action === "approve" && !window.confirm("Approve this learner's enrollment?")) return;
    if (action === "reject" && reason.trim().length < 10) { setError("Give a reason of at least 10 characters."); return; }
    setBusy(action); setError(""); setMessage("");
    try {
      const response = await fetch(`/api/lms/courses/${courseId}/enrollments/${enrollmentId}/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: action === "reject" ? JSON.stringify({ reason: reason.trim() }) : undefined,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Queue action failed.");
      setMessage(data.status === "waitlisted" ? "No seat available. Learner remains on the waitlist." : action === "approve" ? "Enrollment approved." : "Request declined and learner notified.");
      if (action === "reject") { setReasonOpen(false); setReason(""); }
      router.refresh();
    } catch (err) { setError(err instanceof Error ? err.message : "Queue action failed."); }
    finally { setBusy(null); }
  }

  if (!["pending_approval", "waitlisted"].includes(status)) return <span className="section-meta">No action required</span>;
  return <div className="stack" aria-label={`Queue actions for ${status}`}>
    <div className="inline-actions">
      <button className="button button-secondary" type="button" disabled={busy !== null} onClick={() => void act("approve")} title={status === "waitlisted" ? "Admit if a seat is available" : "Approve enrollment"}>
        {busy === "approve" ? <Loader2 size={14} className="spin" /> : <Check size={14} />} Approve
      </button>
      <button className="button button-secondary" type="button" disabled={busy !== null} onClick={() => { setReasonOpen(value => !value); setError(""); }}>
        <X size={14} /> Decline
      </button>
    </div>
    {reasonOpen && <div className="soft-panel"><label className="form-field"><span>Reason for declining</span><textarea rows={2} maxLength={1000} value={reason} onChange={event => setReason(event.target.value)} placeholder="Explain the decision for the learner and audit record." /></label>
      <button className="button button-secondary" type="button" disabled={busy !== null || reason.trim().length < 10} onClick={() => void act("reject")}>{busy === "reject" ? "Sending…" : "Confirm decline"}</button></div>}
    {error && <span className="form-error" role="alert">{error}</span>}
    {message && <span className="form-success" role="status">{message}</span>}
  </div>;
}
