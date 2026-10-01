"use client";
import { useState } from "react";
import { InquiryConvertButton } from "@/components/saas-crm-forms";
import styles from "./queue.module.css";

export type Inquiry = {
  id: string; name: string; work_email: string; organization: string;
  job_title: string | null; message: string | null;
  request_type: "demo" | "sales" | "trial"; plan_code?: string | null; source?: string | null;
  country_code?: string | null; country_name?: string | null; organization_size?: string | null;
  business_phone?: string | null; primary_objective?: string | null; evaluation_timeline?: string | null;
  utm_source?: string | null; utm_medium?: string | null; utm_campaign?: string | null; landing_path?: string | null;
  status: "new" | "contacted" | "closed"; created_at: string;
  crm_account_id?: string | null; converted_at?: string | null;
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
    {items.length === 0 ? <p>No inbound inquiries yet.</p> : items.map(item => <article className={styles.card} key={item.id}>
      <div className={styles.heading}><div><h2>{item.name}</h2><p>{item.organization}{item.job_title ? ` · ${item.job_title}` : ""}</p></div>
        <time dateTime={item.created_at}>{new Date(item.created_at).toLocaleString()}</time></div>
      <p><a href={`mailto:${item.work_email}`}>{item.work_email}</a></p>
      <p><strong>{item.request_type === "trial" ? "Guided evaluation" : item.request_type === "sales" ? "Sales inquiry" : "Conversation request"}</strong>{item.plan_code ? ` · Plan: ${item.plan_code}` : ""}{item.source ? ` · Source: ${item.source}` : ""}</p>
      <p>{[item.country_name, item.organization_size, item.business_phone].filter(Boolean).join(" · ") || "Qualification details not supplied"}</p>
      {(item.primary_objective || item.evaluation_timeline) && <p><strong>{item.primary_objective || "Objective not specified"}</strong>{item.evaluation_timeline ? ` · ${item.evaluation_timeline}` : ""}</p>}
      {(item.utm_source || item.utm_campaign || item.landing_path) && <p><small>Attribution: {[item.utm_source, item.utm_medium, item.utm_campaign, item.landing_path].filter(Boolean).join(" · ")}</small></p>}
      {item.message && <p className={styles.message}>{item.message}</p>}
      <div className={styles.actions}><label>Status <select value={item.status} disabled={busy === item.id} onChange={event => update(item.id, event.target.value as Inquiry["status"])}>
        <option value="new">New</option><option value="contacted">Contacted</option><option value="closed">Closed</option>
      </select></label><InquiryConvertButton id={item.id} accountId={item.crm_account_id} requestType={item.request_type}/></div>
    </article>)}
  </div>;
}
