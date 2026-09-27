"use client";
import { useState, type FormEvent } from "react";
import styles from "./landing.module.css";

export function DemoInquiryForm() {
  const [state, setState] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (state === "sending") return;
    const form = event.currentTarget;
    const data = new FormData(form);
    setState("sending");
    setError("");
    try {
      const response = await fetch("/api/marketing/inquiries", {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({
          name: data.get("name"), work_email: data.get("work_email"),
          organization: data.get("organization"), job_title: data.get("job_title"),
          message: data.get("message"), consent: data.get("consent") === "on",
          website: data.get("website"),
        }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(response.status === 429 ? "Too many requests. Please try again later." :
          response.status === 503 ? "Requests are temporarily unavailable. Please try again later." :
          typeof body.detail === "string" ? body.detail : "We could not send your request. Please check the fields and try again.");
      }
      form.reset();
      setState("sent");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "We could not send your request. Please try again.");
      setState("error");
    }
  }
  return <form className={styles.inquiryForm} onSubmit={submit}>
    <div className={styles.formGrid}>
      <label>Full name <input name="name" autoComplete="name" minLength={2} maxLength={160} required /></label>
      <label>Work email <input name="work_email" type="email" autoComplete="email" maxLength={320} required /></label>
      <label>Organization <input name="organization" autoComplete="organization" minLength={2} maxLength={200} required /></label>
      <label>Job title <input name="job_title" autoComplete="organization-title" maxLength={160} /></label>
    </div>
    <label>What would you like to explore? <textarea name="message" rows={3} maxLength={1200} placeholder="A few details about your team or goals (optional)" /></label>
    <div className={styles.honeypot} aria-hidden="true"><label>Website <input name="website" tabIndex={-1} autoComplete="off" /></label></div>
    <label className={styles.consent}><input name="consent" type="checkbox" required />
      <span>I agree that Kognivon may use these details to respond to my request. Please do not include sensitive personal data.</span>
    </label>
    <button className={styles.primaryButton} disabled={state === "sending"} type="submit">
      {state === "sending" ? "Sending request…" : "Request a conversation"}
    </button>
    <p className={styles.formStatus} role="status" aria-live="polite">
      {state === "sent" ? "Your request was received. The Kognivon team can now review it." : error}
    </p>
  </form>;
}
