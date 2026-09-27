"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, CheckCircle2, Loader2 } from "lucide-react";

type Field = { name: string; label: string; type?: "text"|"number"|"email"|"select"|"textarea"|"date"; placeholder?: string; required?: boolean; options?: Array<{ value: string; label: string }>; defaultValue?: string|number };

type FormValues = Record<string, string>;
type ResourceSuccess = { id?: string; [key: string]: unknown };
type TransformProfile = "webhook_events" | "assessment_question" | "compliance_rules";
type Props = { title: string; endpoint: string; method?: "POST"|"PATCH"|"PUT"; fields: Field[]; submitLabel?: string; description?: string; transformProfile?: TransformProfile; jsonFields?: string[]; includeEmptyFields?: string[]; onSuccess?: (payload: ResourceSuccess) => void; successRedirect?: string; testEndpoint?: string };

export function ResourceForm({ title, endpoint, method="POST", fields, submitLabel="Save", description, transformProfile, jsonFields = [], includeEmptyFields = [], onSuccess, successRedirect, testEndpoint }: Props) {
  const router = useRouter();
  const initial = Object.fromEntries(fields.map((field) => [field.name, String(field.defaultValue ?? "")])) as FormValues;
  const [values, setValues] = useState<FormValues>(initial);
  const [busy, setBusy] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const update = (name: string, value: string) => setValues((current) => ({ ...current, [name]: value }));
  const resolveEndpoint = (template: string) => template.replace(/:([a-zA-Z_][a-zA-Z0-9_]*)/g, (_match, key: string) => encodeURIComponent(values[key] ?? ""));
  const buildPayload = () => Object.fromEntries(
    Object.entries(values)
      .filter(([key, value]) => value !== "" || includeEmptyFields.includes(key))
      .map(([key, value]) => [key, value === "" ? null : jsonFields.includes(key) ? JSON.parse(value) : value]),
  );

  const buildRequestPayload = () => {
    if (transformProfile === "webhook_events") {
      return { url: values.url, event_types: values.event_types.split(",").map((item) => item.trim()).filter(Boolean) };
    }
    if (transformProfile === "compliance_rules") {
      const payload = buildPayload();
      const rules: Record<string, string[] | number> = {};
      for (const key of ["role_names", "job_titles", "org_unit_ids", "exclude_user_ids"]) {
        const entries = (values[key] || "").split(/[,\n]/).map((entry) => entry.trim()).filter(Boolean);
        if (entries.length) rules[key] = entries;
        delete payload[key];
      }
      if (values.escalation_days) rules.escalation_days = Number(values.escalation_days);
      delete payload.escalation_days;
      return { ...payload, rules };
    }
    if (transformProfile === "assessment_question") {
      const options = values.options.split(/\r?\n/).map((item) => item.trim()).filter(Boolean);
      const correct = values.question_type === "multiple_choice"
        ? values.correct.split("|").map((item) => item.trim()).filter(Boolean)
        : values.correct.trim();
      return { question_type: values.question_type, prompt: values.prompt, options, answer_key: { correct }, points: Number(values.points), position: Number(values.position) };
    }
    return buildPayload();
  };

  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      const requestPayload = buildRequestPayload();
      const resolvedEndpoint = resolveEndpoint(endpoint);
      const response = await fetch(resolvedEndpoint, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(requestPayload) });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "The action could not be completed.");
      setMessage("Saved successfully.");
      const payload = data as ResourceSuccess;
      onSuccess?.(payload);
      if (successRedirect && typeof payload.id === "string") router.push(successRedirect.replace(":id", payload.id));
      else router.refresh();
      if (method === "POST") setValues(initial);
    } catch (err) { setError(err instanceof Error ? err.message : "The action failed."); }
    finally { setBusy(false); }
  }

  async function testConnection() {
    if (!testEndpoint) return;
    setTesting(true);
    setError("");
    setMessage("");
    try {
      const payload = buildRequestPayload();
      const response = await fetch(resolveEndpoint(testEndpoint), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Connection test failed.");
      setMessage(data.message ? "Connection verified: " + data.message : "Connection verified.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection test failed.");
    } finally {
      setTesting(false);
    }
  }

  return <form className="resource-form" onSubmit={submit}>
    <div className="section-heading compact"><div><span className="eyebrow">Workspace action</span><h2>{title}</h2>{description && <p>{description}</p>}</div></div>
    <div className="form-grid">{fields.map((field) => <label className={field.type === "textarea" ? "form-field full" : "form-field"} key={field.name}><span>{field.label}</span>{field.type === "select" ? <select required={field.required} value={values[field.name]} onChange={(e) => update(field.name,e.target.value)}><option value="">Select…</option>{field.options?.map((option)=><option value={option.value} key={option.value}>{option.label}</option>)}</select> : field.type === "textarea" ? <textarea required={field.required} value={values[field.name]} placeholder={field.placeholder} onChange={(e)=>update(field.name,e.target.value)}/> : <input type={field.type || "text"} required={field.required} value={values[field.name]} placeholder={field.placeholder} onChange={(e)=>update(field.name,e.target.value)}/>}</label>)}</div>
    {error && <div className="form-error" role="alert">{error}</div>}{message && <div className="form-success" role="status"><CheckCircle2 size={14}/> {message}</div>}
    <div className="form-actions">
      {testEndpoint && <button className="button button-secondary" type="button" disabled={busy || testing} onClick={testConnection}>{testing ? <><Loader2 size={15}/> Testing…</> : "Test connection"}</button>}
      <button className="button button-primary" disabled={busy || testing}>{busy ? <><Loader2 size={15}/> Saving…</> : <>{submitLabel} <ArrowRight size={15}/></>}</button>
    </div>
  </form>;
}
