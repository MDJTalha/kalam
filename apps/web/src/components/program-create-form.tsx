"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export function ProgramCreateForm() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [required, setRequired] = useState(false);
  const [slugEdited, setSlugEdited] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const response = await fetch("/api/lms/programs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title: title.trim(), slug, description: description.trim() || null, is_required: required }) });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Could not create program.");
      router.push("/dashboard/programs/" + data.id);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not create program."); }
    finally { setBusy(false); }
  }
  return <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Program builder</span><h2>Create program</h2></div></div>
    <p>Create a draft, add courses, then publish it before launching a cohort.</p>
    <form className="studio-form" onSubmit={submit}><div className="form-grid">
      <label>Program title<input required minLength={3} value={title} onChange={event => { setTitle(event.target.value); if (!slugEdited) setSlug(event.target.value.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")); }} /></label>
      <label>Slug<input required minLength={3} pattern="[a-z0-9]+(-[a-z0-9]+)*" value={slug} onChange={event => { setSlugEdited(true); setSlug(event.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "-")); }} /></label>
      <label className="full-span">Description<textarea rows={3} value={description} onChange={event => setDescription(event.target.value)} /></label>
      <label><input type="checkbox" checked={required} onChange={event => setRequired(event.target.checked)} /> Required program</label>
    </div>{error && <p className="form-error" role="alert">{error}</p>}<button className="button button-primary" disabled={busy} type="submit">{busy ? "Creating…" : "Create program"}</button></form>
  </section>;
}
