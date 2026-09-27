"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { ArrowRight, CheckCircle2, FileCheck2, ShieldAlert } from "lucide-react";

type Assignment = {
  id: string;
  requirement: string;
  description?: string | null;
  status: string;
  due_state?: string;
  due_at?: string | null;
  course_id?: string | null;
  course_title?: string | null;
};

async function postAction(path: string, body: Record<string, unknown>) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || "The compliance action could not be completed.");
  return payload;
}

export function ComplianceAssignmentActions({ assignment }: { assignment: Assignment }) {
  const [mode, setMode] = useState<"evidence" | "exception" | null>(null);
  const [evidenceType, setEvidenceType] = useState("document");
  const [reference, setReference] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [notes, setNotes] = useState("");
  const [reason, setReason] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const isClosed = assignment.status === "completed" || assignment.status === "excepted";
  const isUnderReview = assignment.status === "exception_requested";

  async function run(event: FormEvent, path: string, body: Record<string, unknown>, success: string) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await postAction(path, body);
      setMessage(success);
      setMode(null);
      setReference("");
      setNotes("");
      setReason("");
      window.location.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "The compliance action could not be completed.");
    } finally {
      setBusy(false);
    }
  }

  async function submitEvidence(event: FormEvent) {
    if (evidenceType !== "document") {
      await run(event, `/api/lms/compliance/my/${assignment.id}/evidence`,
        { evidence_type: evidenceType, reference, notes: notes || null }, "Evidence submitted for review.");
      return;
    }
    event.preventDefault();
    if (!file) return;
    setBusy(true); setError("");
    try {
      const form = new FormData();
      form.set("upload", file);
      if (notes) form.set("notes", notes);
      const response = await fetch(`/api/lms/compliance/my/${assignment.id}/upload`, { method: "POST", body: form });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "Document upload failed.");
      window.location.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Document upload failed.");
    } finally {
      setBusy(false);
    }
  }

  async function completeAssignment() {
    setBusy(true);
    setError("");
    try {
      await postAction(`/api/lms/compliance/my/${assignment.id}/complete`, {});
      window.location.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to complete requirement.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="action-stack compliance-actions">
      <div className="button-row">
        {assignment.course_id ? <Link className="button button-secondary" href={`/dashboard/catalog/${assignment.course_id}`}><ArrowRight size={14} /> Open learning</Link> : null}
        {!isClosed && !isUnderReview && assignment.course_id ? <button className="button button-secondary" type="button" disabled={busy} onClick={() => void completeAssignment()}> <CheckCircle2 size={14} /> {busy ? "Completing…" : "Mark complete"}</button> : null}
        {!isClosed && !isUnderReview && !assignment.course_id && assignment.status !== "evidence_submitted" ? <button className="button button-ghost" type="button" disabled={busy} onClick={() => { setMode(mode === "evidence" ? null : "evidence"); setError(""); setMessage(""); }}><FileCheck2 size={14} /> Submit evidence</button> : null}
        {!isClosed && !isUnderReview && assignment.status !== "evidence_submitted" ? <button className="button button-ghost" type="button" disabled={busy} onClick={() => { setMode(mode === "exception" ? null : "exception"); setError(""); setMessage(""); }}><ShieldAlert size={14} /> Request exception</button> : null}
      </div>
      {assignment.due_at ? <small>Due {new Date(assignment.due_at).toLocaleString()}</small> : null}
      {isUnderReview ? <small>Exception request is under compliance review.</small> : null}
      {assignment.status === "evidence_submitted" ? <small>Evidence is awaiting compliance review.</small> : null}
      {mode === "evidence" ? <form className="inline-form" onSubmit={(event) => void submitEvidence(event)}>
        <label><span>Evidence type</span><select value={evidenceType} onChange={(event) => setEvidenceType(event.target.value)}><option value="document">Document</option><option value="url">URL</option><option value="attestation">Attestation</option><option value="reference">Reference</option></select></label>
        {evidenceType === "document" ? <label><span>Document</span><input type="file" required accept=".pdf,.txt,.csv,.zip,.docx,.xlsx,.png,.jpg,.jpeg" onChange={(event) => setFile(event.target.files?.[0] || null)} /></label> : <label><span>Reference</span><input required value={reference} onChange={(event) => setReference(event.target.value)} placeholder="URL, attestation or system reference" /></label>}
        <label><span>Notes</span><textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={2} placeholder="Add context for the reviewer" /></label>
        <button className="button button-primary" disabled={busy}>{busy ? "Submitting…" : "Submit evidence"}</button>
      </form> : null}
      {mode === "exception" ? <form className="inline-form" onSubmit={(event) => void run(event, `/api/lms/compliance/${assignment.id}/exceptions`, { reason, expires_at: new Date(`${expiresAt}T23:59:59`).toISOString() }, "Exception request submitted.")}>
        <label><span>Reason</span><textarea required minLength={5} value={reason} onChange={(event) => setReason(event.target.value)} rows={3} placeholder="Explain why the obligation cannot be completed on time" /></label>
        <label><span>Requested expiry</span><input type="date" required min={new Date().toLocaleDateString("en-CA")} value={expiresAt} onChange={(event) => setExpiresAt(event.target.value)} /></label>
        <button className="button button-primary" disabled={busy}>{busy ? "Submitting…" : "Submit request"}</button>
      </form> : null}
      {message ? <small className="form-success" role="status">{message}</small> : null}
      {error ? <small className="form-error" role="alert">{error}</small> : null}
    </div>
  );
}
