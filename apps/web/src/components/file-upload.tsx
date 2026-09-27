"use client";

import { ChangeEvent, useState } from "react";
import { useRouter } from "next/navigation";

export function FileUpload() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true); setMessage("");
    const data = new FormData();
    data.append("upload", file);
    try {
      const response = await fetch("/api/lms/files", { method: "POST", body: data });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "Upload failed.");
      setMessage("Upload scanned and saved.");
      router.refresh();
      event.target.value = "";
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }
  return <div className="resource-form"><label className="form-field"><span>Upload learning file</span><input type="file" disabled={busy} onChange={upload}/></label>{message ? <div className="form-success" role="status">{message}</div> : null}</div>;
}
