"use client";
import { useState } from "react";
import styles from "./queue.module.css";

export type Inquiry = {
  id: string; name: string; work_email: string; organization: string;
  job_title: string | null; message: string | null;
  status: "new" | "contacted" | "closed"; created_at: string;
};

export function InquiryQueue({ initial }: { initial: Inquiry[] }) {
  const [items, setItems] = useState(initial);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  async function update(id: string, status: Inquiry["status"]) {
    setBusy(id); setError("");
    try {
      const response = await fetch(`/api/lms/marketing/inquiries/${id}`, {
        method: "PATCH", headers: { "content-type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (!response.ok) throw new Error("Could not update this request. Please try again.");
      setItems(list => list.map(item => item.id === id ? { ...item, status } : item));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Update failed."); }
    finally { setBusy(null); }
  }
  return <div className={styles.queue}>
    <p role="status" aria-live="polite">{error}</p>
    {items.length === 0 ? <p>No demo requests yet.</p> : items.map(item => <article className={styles.card} key={item.id}>
      <div className={styles.heading}><div><h2>{item.name}</h2><p>{item.organization}{item.job_title ? ` · ${item.job_title}` : ""}</p></div>
        <time dateTime={item.created_at}>{new Date(item.created_at).toLocaleString()}</time></div>
      <p><a href={`mailto:${item.work_email}`}>{item.work_email}</a></p>
      {item.message && <p className={styles.message}>{item.message}</p>}
      <label>Status <select value={item.status} disabled={busy === item.id} onChange={event => update(item.id, event.target.value as Inquiry["status"])}>
        <option value="new">New</option><option value="contacted">Contacted</option><option value="closed">Closed</option>
      </select></label>
    </article>)}
  </div>;
}
