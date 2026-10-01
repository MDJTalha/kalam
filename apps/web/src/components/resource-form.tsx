"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, CheckCircle2, Loader2 } from "lucide-react";

type Field = { name: string; label: string; type?: "text"|"number"|"email"|"select"|"multi-select"|"lookup-multi"|"textarea"|"date"; placeholder?: string; required?: boolean; options?: Array<{ value: string; label: string }>; endpoint?: string; help?: string; defaultValue?: string|number };

type FormValues = Record<string, string>;

type LookupOption = { id: string; label: string; meta?: string | null };

function LookupMultiField({ value, onChange, label, endpoint, required }: {
  value: string;
  onChange: (value: string) => void;
  label: string;
  endpoint: string;
  required?: boolean;
}) {
  const [query, setQuery] = useState("");
  const [options, setOptions] = useState<LookupOption[]>([]);
  const selectedIds = value.split(",").map((item) => item.trim()).filter(Boolean);
  const selected = selectedIds.map((id) => options.find((item) => item.id === id) ?? { id, label: id });

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      try {
        const separator = endpoint.includes("?") ? "&" : "?";
        const selectedIds = value.split(",").map((item) => item.trim()).filter(Boolean);
        const lookupParameter = query.trim()
          ? "q=" + encodeURIComponent(query)
          : selectedIds.length
            ? "ids=" + encodeURIComponent(selectedIds.join(","))
            : "q=";
        const response = await fetch(endpoint + separator + lookupParameter, {
          headers: { Accept: "application/json" }, signal: controller.signal,
        });
        const payload = await response.json().catch(() => ({ items: [] }));
        const next = Array.isArray(payload.items) ? payload.items : Array.isArray(payload) ? payload : [];
        if (response.ok) setOptions(next);
      } catch { /* Keep current options on transient lookup failures. */ }
    }, 180);
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, [endpoint, query, value]);

  function toggle(option: LookupOption) {
    const next = selectedIds.includes(option.id)
      ? selectedIds.filter((id) => id !== option.id)
      : [...selectedIds, option.id];
    onChange(next.join(","));
  }

  return <div className="lookup-multi-field">
    <label><span>{label}{required ? " *" : ""}</span><input value={query} placeholder="Search people…" onChange={(event) => setQuery(event.target.value)} aria-label={label + " search"} /></label>
    {selected.length ? <div className="lookup-multi-chips" aria-label="Selected records">{selected.map((item) => <button type="button" key={item.id} onClick={() => toggle(item)}>{item.label} ×</button>)}</div> : null}
    <div className="lookup-multi-options" role={options.length ? "listbox" : undefined} aria-label={options.length ? label + " results" : undefined}>
      {options.slice(0, 8).map((option) => <button type="button" role="option" aria-selected={selectedIds.includes(option.id)} className={selectedIds.includes(option.id) ? "lookup-multi-option selected" : "lookup-multi-option"} key={option.id} onClick={() => toggle(option)}><span>{option.label}</span>{option.meta ? <small>{option.meta}</small> : null}</button>)}
      {!options.length ? <small className="lookup-multi-empty">Search by name, email or employee number.</small> : null}
    </div>
  </div>;
}

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
  const dirty = fields.some((field) => values[field.name] !== String(field.defaultValue ?? ""));
  useEffect(() => {
    if (!dirty || busy) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ""; };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty, busy]);
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


  function renderField(field: Field) {
    if (field.type === "lookup-multi" && field.endpoint) {
      return <LookupMultiField key={field.name} value={values[field.name]} onChange={(value) => update(field.name, value)} label={field.label} endpoint={field.endpoint} required={field.required} />;
    }
    if (field.type === "multi-select") {
      const selected = values[field.name].split(",").filter(Boolean);
      return <label className="form-field"><span>{field.label}{field.required ? " *" : ""}</span><select multiple required={field.required && selected.length === 0} aria-required={field.required} value={selected} onChange={(event) => update(field.name, Array.from(event.target.selectedOptions).map((option) => option.value).join(","))}>{field.options?.map((option) => <option value={option.value} key={option.value}>{option.label}</option>)}</select>{field.help ? <small>{field.help}</small> : null}</label>;
    }
    return <label className={field.type === "textarea" ? "form-field full" : "form-field"} key={field.name}><span>{field.label}{field.required ? " *" : ""}</span>{field.type === "select" ? <select required={field.required} aria-required={field.required} value={values[field.name]} onChange={(event) => update(field.name, event.target.value)}><option value="">Select…</option>{field.options?.map((option) => <option value={option.value} key={option.value}>{option.label}</option>)}</select> : field.type === "textarea" ? <textarea required={field.required} aria-required={field.required} value={values[field.name]} placeholder={field.placeholder} onChange={(event) => update(field.name, event.target.value)} /> : <input type={field.type || "text"} required={field.required} aria-required={field.required} value={values[field.name]} placeholder={field.placeholder} onChange={(event) => update(field.name, event.target.value)} />}</label>;
  }


  return <form className="resource-form" onSubmit={submit} aria-busy={busy || testing}>
    <div className="section-heading compact"><div><span className="eyebrow">Workspace action</span><h2>{title}</h2>{description && <p>{description}</p>}</div></div>
    <div className="form-grid">{fields.map(renderField)}</div>
    {error && <div className="form-error" role="alert">{error}</div>}{message && <div className="form-success" role="status"><CheckCircle2 size={14}/> {message}</div>}
    <div className="form-actions">
      {testEndpoint && <button className="button button-secondary" type="button" disabled={busy || testing} onClick={testConnection}>{testing ? <><Loader2 size={15}/> Testing…</> : "Test connection"}</button>}
      <button className="button button-primary" disabled={busy || testing}>{busy ? <><Loader2 size={15}/> Saving…</> : <>{submitLabel} <ArrowRight size={15}/></>}</button>
    </div>
  </form>;
}
