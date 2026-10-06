"use client";

import { useEffect, useMemo, useState } from "react";

export type LookupPerson = {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  job_title?: string | null;
};

type Props = {
  value: string;
  onChange: (id: string) => void;
  initialPeople: LookupPerson[];
  label: string;
  disabled?: boolean;
  activeOnly?: boolean;
  optional?: boolean;
  excludeIds?: string[];
};

const displayName = (person: LookupPerson) =>
  `${[person.first_name, person.last_name].filter(Boolean).join(" ") || person.email} · ${person.job_title || person.email}`;

export function PeopleLookupSelect({ value, onChange, initialPeople, label, disabled = false, activeOnly = true, optional = false, excludeIds = [] }: Props) {
  const [query, setQuery] = useState("");
  const [matches, setMatches] = useState(initialPeople);
  const [loading, setLoading] = useState(false);
  const [lookupError, setLookupError] = useState("");
  const people = useMemo(() => {
    const merged = new Map<string, LookupPerson>();
    for (const person of initialPeople) merged.set(person.id, person);
    for (const person of matches) merged.set(person.id, person);
    return [...merged.values()].filter(person => !excludeIds.includes(person.id) || person.id === value);
  }, [initialPeople, matches, excludeIds, value]);

  useEffect(() => {
    const term = query.trim();
    const timer = window.setTimeout(async () => {
      setLoading(true);
      setLookupError("");
      try {
        const params = new URLSearchParams({ page: "1", page_size: "20", status: activeOnly ? "active" : "all" });
        if (term) params.set("q", term);
        const response = await fetch(`/api/v1/people/page?${params}`, { cache: "no-store" });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "People lookup is unavailable.");
        setMatches(Array.isArray(data.items) ? data.items : []);
      } catch (error) {
        setLookupError(error instanceof Error ? error.message : "People lookup is unavailable.");
      } finally {
        setLoading(false);
      }
    }, 200);
    return () => window.clearTimeout(timer);
  }, [query, activeOnly]);

  return <div className="form-field">
    <span>{label}</span>
    <input type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Search name, email, employee ID…" aria-label={`${label} search`} disabled={disabled} />
    <select value={value} onChange={event => onChange(event.target.value)} required={!optional} disabled={disabled || loading}>
      <option value="">{loading ? "Loading people…" : optional ? "All people" : people.length ? "Select a person" : "No matching people"}</option>
      {people.map(person => <option key={person.id} value={person.id}>{displayName(person)}</option>)}
    </select>
    {lookupError ? <small className="form-error" role="alert">{lookupError}</small> : null}
  </div>;
}
