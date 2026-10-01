"use client";

import { useEffect, useRef } from "react";
import intlTelInput, { type Iti } from "intl-tel-input";
import type { CountryCode } from "libphonenumber-js";

type Props = {
  country?: CountryCode | null;
  value: string;
  onChange: (value: string, countryCode: string | null) => void;
  id?: string;
  invalid?: boolean;
  errorId?: string;
};

export function InternationalPhoneInput({ country, value, onChange, id = "business-phone", invalid, errorId }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const instanceRef = useRef<Iti | null>(null);

  useEffect(() => {
    const input = inputRef.current;
    if (!input) return;

    const iti = intlTelInput(input, {
      initialCountry: "us",
      separateDialCode: true,
      countrySearch: true,
      showFlags: true,
      strictMode: true,
      nationalMode: false,
      formatAsYouType: true,
      loadUtils: () => import("intl-tel-input/utils"),
    });
    instanceRef.current = iti;

    const publish = () => {
      const selected = iti.getSelectedCountryData();
      onChange(iti.getNumber() || input.value, "iso2" in selected ? selected.iso2.toUpperCase() : null);
    };
    input.addEventListener("input", publish);
    input.addEventListener("countrychange", publish);

    return () => {
      input.removeEventListener("input", publish);
      input.removeEventListener("countrychange", publish);
      iti.destroy();
      instanceRef.current = null;
    };
  }, [onChange]);

  useEffect(() => {
    if (country && instanceRef.current) instanceRef.current.setCountry(country.toLowerCase() as never);
  }, [country]);

  useEffect(() => {
    const input = inputRef.current;
    if (!input || document.activeElement === input) return;
    if (value !== input.value) input.value = value;
  }, [value]);

  return (
    <div style={{ width: "100%" }}>
      <input
        ref={inputRef}
        id={id}
        name="phone_local"
        type="tel"
        inputMode="tel"
        autoComplete="tel"
        placeholder="Business phone"
        aria-label="Business phone number"
        aria-invalid={invalid || undefined}
        aria-describedby={errorId}
      />
    </div>
  );
}
