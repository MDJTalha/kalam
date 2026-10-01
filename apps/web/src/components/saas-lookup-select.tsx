"use client";

import { useEffect, useRef, useState } from "react";
import type { KeyboardEvent } from "react";

type LookupOption = { id: string; label: string; meta?: string | null };

type Props = {
  name: string;
  label: string;
  endpoint: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  defaultOption?: LookupOption | null;
};

export function SaaSLookupSelect({
  name,
  label,
  endpoint,
  placeholder = "Search or select…",
  required = false,
  disabled = false,
  defaultOption = null,
}: Props) {
  const [query, setQuery] = useState(defaultOption?.label ?? "");
  const [selected, setSelected] = useState<LookupOption | null>(defaultOption);
  const [options, setOptions] = useState<LookupOption[]>([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const requestId = useRef(0);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOutside = (event: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, []);

  useEffect(() => {
    if (!open || disabled) return;
    const controller = new AbortController();
    const current = ++requestId.current;
    const timer = window.setTimeout(async () => {
      try {
        const separator = endpoint.includes("?") ? "&" : "?";
        const response = await fetch(endpoint + separator + "q=" + encodeURIComponent(query), {
          headers: { Accept: "application/json" },
          signal: controller.signal,
        });
        const payload = await response.json().catch(() => ({ items: [] }));
        if (current !== requestId.current || !response.ok) return;
        setOptions(Array.isArray(payload.items) ? payload.items : []);
        setActive(0);
      } catch {
        if (!controller.signal.aborted) setOptions([]);
      }
    }, 180);
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [disabled, endpoint, open, query]);
  function choose(option: LookupOption) {
    setSelected(option);
    setQuery(option.label);
    setOpen(false);
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (!open && (event.key === "ArrowDown" || event.key === "Enter")) {
      event.preventDefault();
      setOpen(true);
      return;
    }
    if (!open) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive((value) => Math.min(value + 1, Math.max(options.length - 1, 0)));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((value) => Math.max(value - 1, 0));
    } else if (event.key === "Enter" && options[active]) {
      event.preventDefault();
      choose(options[active]);
    } else if (event.key === "Escape") {
      event.preventDefault();
      setOpen(false);
    }
  }

  return (
    <div ref={rootRef} className="saas-lookup-field">
      <label>
        <span>{label}{required ? " *" : ""}</span>
        <input
          type="text"
          value={query}
          placeholder={placeholder}
          disabled={disabled}
          role="combobox"
          aria-expanded={open}
          aria-controls={name + "-lookup-options"}
          aria-autocomplete="list"
          onFocus={() => setOpen(true)}
          onClick={() => setOpen(true)}
          onKeyDown={onKeyDown}
          onChange={(event) => {
            setSelected(null);
            setQuery(event.target.value);
            setOpen(true);
          }}
        />
      </label>
      <input type="hidden" className="saas-lookup-value" name={name} value={selected?.id ?? ""} readOnly />
      {open && !disabled && (
        <div id={name + "-lookup-options"} className="saas-lookup-menu" role="listbox">
          {options.length ? options.map((option, index) => (
            <button
              key={option.id}
              type="button"
              role="option"
              aria-selected={index === active}
              className={index === active ? "saas-lookup-option active" : "saas-lookup-option"}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => choose(option)}
            >
              <span>{option.label}</span>
              {option.meta && <small>{option.meta}</small>}
            </button>
          )) : <div className="saas-lookup-empty">No matching records.</div>}
        </div>
      )}
    </div>
  );
}
