"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export function ApiActionButton({
  endpoint,
  label,
  method = "POST",
  body,
  confirmText,
}: {
  endpoint: string;
  label: string;
  method?: "POST" | "PATCH" | "DELETE";
  body?: Record<string, unknown>;
  confirmText?: string;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function run() {
    if (confirmText && !window.confirm(confirmText)) return;
    setBusy(true); setError("");
    try {
      const response = await fetch(endpoint, {
        method,
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "Action failed.");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed.");
    } finally {
      setBusy(false);
    }
  }
  return <span className="action-stack"><button className="button button-secondary" type="button" disabled={busy} onClick={run}>{busy ? "Working…" : label}</button>{error ? <small className="form-error" role="alert">{error}</small> : null}</span>;
}
