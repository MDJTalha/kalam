"use client";

import { useCallback, useMemo, useState, type FormEvent } from "react";
import { ArrowRight, CheckCircle2, Globe2, LockKeyhole, MailCheck } from "lucide-react";
import Select, { type SingleValue } from "react-select";
import { getCountries, getCountryCallingCode, isValidPhoneNumber, type CountryCode } from "libphonenumber-js";
import { InternationalPhoneInput } from "@/components/international-phone-input";
import { PublicButton } from "@/components/public-button";
import styles from "./landing.module.css";

type CountryOption = { value: CountryCode; label: string; dialCode: string };

const PERSONAL_EMAIL_DOMAINS = new Set([
  "gmail.com","googlemail.com","yahoo.com","yahoo.co.uk","hotmail.com","outlook.com","live.com","msn.com",
  "icloud.com","me.com","aol.com","proton.me","protonmail.com","gmx.com","mail.com","yandex.com","zoho.com"
]);

const OBJECTIVES = [
  "Skills & capability management",
  "Enterprise learning platform",
  "Compliance & readiness",
  "Leadership & development",
  "Workforce intelligence & analytics",
  "LMS / platform replacement",
  "Global rollout",
  "Other",
];

function isOfficialWorkEmail(email: string) {
  const domain = email.trim().toLowerCase().split("@")[1] || "";
  return Boolean(domain && !PERSONAL_EMAIL_DOMAINS.has(domain));
}

export function DemoInquiryForm() {
  const [state, setState] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [error, setError] = useState("");
  const [country, setCountry] = useState<CountryOption | null>(null);
  const [phoneNumber, setPhoneNumber] = useState("");
  const [emailError, setEmailError] = useState("");
  const [countryError, setCountryError] = useState("");
  const [phoneError, setPhoneError] = useState("");

  const countryOptions = useMemo<CountryOption[]>(() => {
    const displayNames = new Intl.DisplayNames(["en"], { type: "region" });
    return getCountries()
      .map(code => ({ value: code, label: displayNames.of(code) || code, dialCode: "+" + getCountryCallingCode(code) }))
      .sort((a, b) => a.label.localeCompare(b.label));
  }, []);

  const handlePhoneChange = useCallback((value: string, countryCode: string | null) => {
    setPhoneNumber(value);
    setPhoneError("");
    if (countryCode) {
      const match = countryOptions.find(option => option.value === countryCode as CountryCode);
      if (match) {
        setCountry(match);
        setCountryError("");
      }
    }
  }, [countryOptions]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (state === "sending") return;
    const form = event.currentTarget;
    const data = new FormData(form);
    const workEmail = String(data.get("work_email") || "").trim().toLowerCase();

    if (!isOfficialWorkEmail(workEmail)) {
      setState("error");
      setEmailError("Use your official organization email address.");
      setError("Please review the highlighted field.");
      return;
    }
    setEmailError("");
    if (!country) {
      setState("error");
      setCountryError("Select your country.");
      setError("Please review the highlighted field.");
      document.getElementById("landing-country-input")?.focus();
      return;
    }
    setCountryError("");
    if (phoneNumber.trim() && !isValidPhoneNumber(phoneNumber)) {
      setState("error");
      setPhoneError("Enter a valid international phone number or leave this field blank.");
      setError("Please review the highlighted field.");
      document.getElementById("landing-business-phone")?.focus();
      return;
    }
    setPhoneError("");

    setState("sending");
    setError("");
    const context = String(data.get("message") || "").trim();
    const attribution = new URLSearchParams(window.location.search);

    try {
      const response = await fetch("/api/marketing/inquiries", {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({
          name: data.get("name"), work_email: workEmail,
          organization: data.get("organization"), job_title: null,
          message: context.slice(0, 1200) || null,
          country_code: country.value,
          country_name: country.label,
          business_phone: phoneNumber.trim() || null,
          primary_objective: data.get("objective"),
          utm_source: attribution.get("utm_source"),
          utm_medium: attribution.get("utm_medium"),
          utm_campaign: attribution.get("utm_campaign"),
          landing_path: window.location.pathname,
          consent: data.get("consent") === "on",
          source: "landing-page", request_type: "demo", website: data.get("website"),
        }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(response.status === 429 ? "Too many requests. Please try again later." :
          response.status === 503 ? "Requests are temporarily unavailable. Please try again later." :
          typeof body.detail === "string" ? body.detail : "We could not send your request. Please check the fields and try again.");
      }
      form.reset();
      setCountry(null);
      setPhoneNumber("");
      setEmailError("");
      setCountryError("");
      setPhoneError("");
      setState("sent");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "We could not send your request. Please try again.");
      setState("error");
    }
  }

  if (state === "sent") {
    return <section className={`${styles.inquiryForm} ${styles.inquirySuccess}`} role="status" aria-live="polite">
      <span className={styles.inquirySuccessIcon}><CheckCircle2 size={28} aria-hidden="true" /></span>
      <span className={styles.inquirySuccessEyebrow}>Request received</span>
      <h3>Thank you for reaching out.</h3>
      <p>Our team will review your organization and priorities, then follow up using the work email you provided.</p>
      <PublicButton variant="secondary" type="button" onClick={() => setState("idle")}>Send another request</PublicButton>
    </section>;
  }

  return <form className={styles.inquiryForm} onSubmit={submit}>
    <div className={styles.formIntro}>
      <span>START THE CONVERSATION</span>
      <strong>Tell us what you’re looking to achieve.</strong>
      <p>Share a few details about your priority and we’ll start the conversation with the right context. Fields marked <b aria-hidden="true">*</b> are required.</p>
    </div>
    <div className={styles.formGrid}>
      <label><span className={styles.fieldLabel}>Full name <b aria-hidden="true">*</b></span><input name="name" autoComplete="name" minLength={2} maxLength={160} placeholder="e.g. Alex Morgan" required /></label>
      <label><span className={styles.fieldLabel}>Work email <b aria-hidden="true">*</b></span><input name="work_email" type="email" autoComplete="email" maxLength={320} placeholder="you@company.com" required aria-invalid={Boolean(emailError)} aria-describedby={emailError ? "landing-email-error" : undefined} onChange={() => { if (emailError) { setEmailError(""); setError(""); setState("idle"); } }} />{emailError && <small className={styles.fieldError} id="landing-email-error">{emailError}</small>}</label>
      <label><span className={styles.fieldLabel}>Organization <b aria-hidden="true">*</b></span><input name="organization" autoComplete="organization" minLength={2} maxLength={200} placeholder="Company or group name" required /></label>
      <label htmlFor="landing-country-input"><span className={styles.fieldLabel}>Country <b aria-hidden="true">*</b></span>
        <Select<CountryOption, false>
          inputId="landing-country-input"
          className={styles.landingCountry}
          classNamePrefix="landing-country"
          instanceId="landing-country"
          options={countryOptions}
          value={country}
          onChange={(option: SingleValue<CountryOption>) => { setCountry(option); if (option) { setCountryError(""); if (countryError) { setError(""); setState("idle"); } } }}
          placeholder="Search country or code"
          isSearchable
          aria-required={true}
          aria-invalid={Boolean(countryError)}
          aria-describedby={countryError ? "landing-country-error" : undefined}
          formatOptionLabel={option => <span className={styles.countryOption}><span className={styles.countryFlag} aria-hidden="true" style={{ backgroundImage: `url("/flags/4x3/${option.value.toLowerCase()}.svg")` }} /><span className={styles.countryName}>{option.label}</span><span className={styles.countryDial}>{option.dialCode}</span></span>}
        />
        {countryError && <small className={styles.fieldError} id="landing-country-error">{countryError}</small>}
      </label>
      <label><span className={styles.fieldLabel}>Business phone <small>Optional</small></span><div className={styles.landingIntlPhone}><InternationalPhoneInput country={country?.value || null} value={phoneNumber} onChange={handlePhoneChange} id="landing-business-phone" invalid={Boolean(phoneError)} errorId={phoneError ? "landing-phone-error" : undefined} /></div>{phoneError && <small className={styles.fieldError} id="landing-phone-error">{phoneError}</small>}</label>
      <label><span className={styles.fieldLabel}>Primary objective <b aria-hidden="true">*</b></span><select name="objective" defaultValue="" required><option value="" disabled>Select priority</option>{OBJECTIVES.map(item => <option key={item} value={item}>{item}</option>)}</select></label>
    </div>
    <label><span className={styles.fieldLabel}>What should our team understand? <small>Optional</small></span><textarea name="message" rows={4} maxLength={700} placeholder="Share your goals, current environment, priority workflows or evaluation context." /></label>
    <div className={styles.inquiryTrustRow}>
      <span><MailCheck size={15}/><b>Built for enterprise</b><small>Designed for organizational conversations</small></span>
      <span><Globe2 size={15}/><b>International-ready</b><small>Country and dialing support</small></span>
      <span><LockKeyhole size={15}/><b>Handled securely</b><small>Used to respond to your request</small></span>
    </div>
    <div className={styles.honeypot} aria-hidden="true"><label>Website <input name="website" tabIndex={-1} autoComplete="off" /></label></div>
    <div className={styles.sensitiveDataNote} role="note">
      <LockKeyhole size={14} aria-hidden="true"/>
      <span><strong>Information handling</strong><small>Please do not include sensitive personal, health, financial, or confidential employee information. Share only the business context needed for our team to respond.</small></span>
    </div>
    <label className={styles.consent}><input name="consent" type="checkbox" required />
      <span>I agree that Kalam may use these details to respond to my request and manage the related business conversation.</span>
    </label>
    <PublicButton className={styles.primaryButton} disabled={state === "sending"} type="submit">
      {state === "sending" ? "Sending request…" : <>Start the conversation <ArrowRight size={16}/></>}
    </PublicButton>
    <p className={styles.formStatus} role="status" aria-live="polite">
      {error}
    </p>
  </form>;
}
