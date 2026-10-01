"use client";

import { useCallback, useMemo, useState, type FormEvent } from "react";
import { ArrowRight, CheckCircle2, Globe2, LockKeyhole, MailCheck } from "lucide-react";
import Link from "next/link";
import Select, { type SingleValue } from "react-select";
import { getCountries, getCountryCallingCode, type CountryCode } from "libphonenumber-js";
import { InternationalPhoneInput } from "@/components/international-phone-input";
import { PublicButton } from "@/components/public-button";
import styles from "@/app/commercial.module.css";

type CountryOption = { value: CountryCode; label: string; dialCode: string };

const PERSONAL_EMAIL_DOMAINS = new Set([
  "gmail.com","googlemail.com","yahoo.com","yahoo.co.uk","hotmail.com","outlook.com","live.com","msn.com",
  "icloud.com","me.com","aol.com","proton.me","protonmail.com","gmx.com","mail.com","yandex.com","zoho.com"
]);

const ORG_SIZES = ["1–249 employees","250–999 employees","1,000–4,999 employees","5,000–19,999 employees","20,000+ employees"];
const SALES_OBJECTIVES = ["Enterprise learning platform","Skills & capability management","Compliance & readiness","Leadership & development","Workforce intelligence & analytics","Platform consolidation / LMS replacement","Global rollout / multi-region deployment","Other"];
const TRIAL_OBJECTIVES = ["Validate learner experience","Evaluate administration & governance","Test skills / capability workflows","Evaluate compliance workflows","Assess integrations & data flows","Technical / security evaluation","Other"];
const TIMELINES = ["Immediately / active project","Within 1–3 months","Within 3–6 months","Within 6–12 months","12+ months / early research"];

function isOfficialWorkEmail(email: string) {
  const domain = email.trim().toLowerCase().split("@")[1] || "";
  return Boolean(domain && !PERSONAL_EMAIL_DOMAINS.has(domain));
}

export function CommercialInquiryForm({ mode, planCode }: { mode: "sales" | "trial"; planCode?: string }) {
  const [state, setState] = useState<"idle"|"sending"|"sent"|"error">("idle");
  const [message, setMessage] = useState("");
  const [detailCount, setDetailCount] = useState(0);
  const [country, setCountry] = useState<CountryOption | null>(null);
  const [phoneNumber, setPhoneNumber] = useState("");
  const [emailError, setEmailError] = useState("");
  const [countryError, setCountryError] = useState("");
  const objectives = mode === "trial" ? TRIAL_OBJECTIVES : SALES_OBJECTIVES;

  const countryOptions = useMemo<CountryOption[]>(() => {
    const displayNames = new Intl.DisplayNames(["en"], { type: "region" });
    return getCountries()
      .map(code => ({
        value: code,
        label: displayNames.of(code) || code,
        dialCode: "+" + getCountryCallingCode(code),
      }))
      .sort((a, b) => a.label.localeCompare(b.label));
  }, []);

  function selectCountry(option: SingleValue<CountryOption>) {
    setCountry(option);
    if (option) setCountryError("");
  }

  const handlePhoneChange = useCallback((value: string) => {
    setPhoneNumber(value);
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (state === "sending") return;
    const form = event.currentTarget;
    const data = new FormData(form);
    const workEmail = String(data.get("work_email") || "").trim().toLowerCase();

    if (!isOfficialWorkEmail(workEmail)) {
      setState("error");
      setEmailError("Use your official organization email address.");
      setMessage("Please review the highlighted field.");
      return;
    }
    setEmailError("");
    if (!country) {
      setState("error");
      setCountryError("Select your country so we can route the inquiry correctly.");
      setMessage("Please review the highlighted field.");
      return;
    }
    setCountryError("");

    setState("sending");
    setMessage("");
    const detail = String(data.get("message") || "").trim();
    const fullPhone = phoneNumber.trim();
    const attribution = new URLSearchParams(window.location.search);

    try {
      const response = await fetch("/api/marketing/inquiries", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          name: data.get("name"),
          work_email: workEmail,
          organization: data.get("organization"),
          job_title: data.get("job_title"),
          message: detail.slice(0, 1200) || null,
          request_type: mode,
          plan_code: planCode || null,
          source: mode === "trial" ? "guided-evaluation-page" : "contact-sales-page",
          country_code: country.value,
          country_name: country.label,
          organization_size: data.get("organization_size"),
          business_phone: fullPhone || null,
          primary_objective: data.get("objective"),
          evaluation_timeline: data.get("timeline"),
          utm_source: attribution.get("utm_source"),
          utm_medium: attribution.get("utm_medium"),
          utm_campaign: attribution.get("utm_campaign"),
          landing_path: window.location.pathname,
          consent: data.get("consent") === "on",
          website: data.get("website"),
        }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(response.status === 503 ? "Requests are temporarily unavailable. Please contact the Kalam team through your approved sales channel." : typeof body.detail === "string" ? body.detail : "We could not send your request.");
      }
      form.reset();
      setCountry(null);
      setPhoneNumber("");
      setDetailCount(0);
      setState("sent");
    } catch (error) {
      setState("error");
      setMessage(error instanceof Error ? error.message : "We could not send your request.");
    }
  }

  if (state === "sent") {
    return <section className={styles.formSuccess} aria-live="polite">
      <span className={styles.successIcon}><CheckCircle2 size={24} /></span>
      <span className={styles.formEyebrow}>Request received</span>
      <h2>Thank you. Your enterprise inquiry is now with Kalam.</h2>
      <p>Our team will review your organization, objectives and evaluation timeline before responding.</p>
      <div className={styles.responsePromise}><MailCheck size={18} /><span><strong>What happens next</strong><small>A Kalam representative will follow up using the official work email you provided.</small></span></div>
      <div className={styles.successActions}>
        <PublicButton href="/trust" variant="secondary">Review Security & Trust</PublicButton>
        <PublicButton href="/implementation" variant="secondary">Implementation approach</PublicButton>
        <PublicButton variant="text" type="button" onClick={() => setState("idle")}>Submit another request</PublicButton>
      </div>
    </section>;
  }

  return <form className={styles.enterpriseForm} onSubmit={submit}>
    <div className={styles.formHeader}>
      <span className={styles.formEyebrow}>{mode === "trial" ? "Guided enterprise evaluation" : "Enterprise conversation"}</span>
      <h2>{mode === "trial" ? "Tell us what must be proven." : "Let’s discuss your business priorities."}</h2>
      <p>{mode === "trial" ? <>Share enough context for us to shape a meaningful evaluation. Fields marked <b aria-hidden="true">*</b> are required.</> : <>A few details will help us prepare the right conversation. Fields marked <b aria-hidden="true">*</b> are required.</>}</p>
    </div>

    <fieldset className={styles.formSection} aria-labelledby="sales-details-title">
      <div className={styles.salesSectionTitle} id="sales-details-title">Your details</div>
      <div className={styles.formGrid}>
        <label><span>Full name <b aria-hidden="true">*</b></span><input name="name" autoComplete="name" minLength={2} maxLength={160} placeholder="e.g. Alex Morgan" required /></label>
        <label><span>Official work email <b aria-hidden="true">*</b></span><input name="work_email" type="email" inputMode="email" autoComplete="email" maxLength={320} placeholder="alex@company.com" required aria-invalid={Boolean(emailError)} aria-describedby={emailError ? "enterprise-email-error" : undefined} onChange={() => emailError && setEmailError("")} />{emailError && <small className={styles.fieldError} id="enterprise-email-error">{emailError}</small>}</label>
        <label><span>Organization <b aria-hidden="true">*</b></span><input name="organization" autoComplete="organization" minLength={2} maxLength={200} placeholder="Company or group name" required /></label>
        <label><span>Job title</span><input name="job_title" autoComplete="organization-title" maxLength={160} placeholder="e.g. VP Learning & Development" /></label>

        <label><span>Organization size <b aria-hidden="true">*</b></span><select name="organization_size" defaultValue="" required><option value="" disabled>Select employee range</option>{ORG_SIZES.map(size => <option key={size} value={size}>{size}</option>)}</select></label>

        <label htmlFor="enterprise-country-input">
          <span>Country <b aria-hidden="true">*</b></span>
          <Select<CountryOption, false>
            inputId="enterprise-country-input"
            instanceId="enterprise-country"
            className={styles.countrySelect}
            classNamePrefix="k-country"
            options={countryOptions}
            value={country}
            onChange={selectCountry}
            isSearchable
            placeholder="Search country"
            noOptionsMessage={() => "No country found"}
            aria-invalid={Boolean(countryError)}
            aria-describedby={countryError ? "enterprise-country-error" : undefined}
            formatOptionLabel={option => <span className={styles.countryOption}><span className={styles.countryFlag} aria-hidden="true" style={{ backgroundImage: `url("/flags/4x3/${option.value.toLowerCase()}.svg")` }} /><span className={styles.countryName}>{option.label}</span><span className={styles.countryDial}>{option.dialCode}</span></span>}
          />
          <input type="hidden" name="country" value={country?.value || ""} />
          {countryError && <small className={styles.fieldError} id="enterprise-country-error">{countryError}</small>}
        </label>

        <label className={styles.phoneField}>
          <span>Business phone <em>Optional</em></span>
          <div className={styles.intlPhone}>
            <InternationalPhoneInput
              country={country?.value || null}
              value={phoneNumber}
              onChange={handlePhoneChange}
            />
          </div>
        </label>
      </div>
    </fieldset>

    <fieldset className={styles.formSection} aria-labelledby="sales-priorities-title">
      <div className={styles.salesSectionTitle} id="sales-priorities-title">Your priorities</div>
      <div className={styles.formGrid}>
        <label><span>Primary objective <b aria-hidden="true">*</b></span><select name="objective" defaultValue="" required><option value="" disabled>Select priority</option>{objectives.map(item => <option key={item} value={item}>{item}</option>)}</select></label>
        <label><span>Evaluation timeline <b aria-hidden="true">*</b></span><select name="timeline" defaultValue="" required><option value="" disabled>Select timeline</option>{TIMELINES.map(item => <option key={item} value={item}>{item}</option>)}</select></label>
      </div>

      <label className={styles.detailsField}>
        <span>{mode === "trial" ? "What do you want to validate?" : "What should our team understand?"}</span>
        <textarea name="message" maxLength={700} rows={5} onChange={event => setDetailCount(event.target.value.length)} placeholder={mode === "trial" ? "Share the teams involved, intended trial users, integrations, security requirements and the outcomes you want to validate." : "Share your business goals, current platform or learning environment, regions, integration needs, governance requirements and any decision criteria."} />
        <small><span>Do not include sensitive personal, health or confidential employee data.</span><span>{detailCount}/700</span></small>
      </label>
    </fieldset>

    <div className={styles.formTrustBar}>
      <div><Globe2 size={17}/><span><strong>International-ready</strong><small>Country-aware routing and international dialing support.</small></span></div>
      <div><LockKeyhole size={17}/><span><strong>Handled securely</strong><small>Your details are used to prepare the conversation.</small></span></div>
    </div>

    <div style={{position:"absolute",left:"-9999px"}} aria-hidden="true"><label>Website<input name="website" tabIndex={-1} autoComplete="off"/></label></div>

    <label className={styles.enterpriseConsent}>
      <input name="consent" type="checkbox" required/>
      <span>I agree that Kalam may use these details to respond to this request and manage the related commercial conversation. See our <Link href="/trust">Trust & security information</Link>.</span>
    </label>

    <div className={styles.formActions}>
      <PublicButton className={styles.enterpriseSubmit} type="submit" disabled={state === "sending"}><span>{state === "sending" ? "Sending request…" : mode === "trial" ? "Request guided evaluation" : "Start the conversation"}</span><ArrowRight size={17} aria-hidden="true"/></PublicButton>
      <span className={styles.formResponseNote}>{mode === "trial" ? "We’ll use your context to shape the evaluation before access is provisioned." : "We’ll use your context to prepare the right commercial conversation."}</span>
    </div>

    <p className={styles.status} role="status" aria-live="polite">{message}</p>
  </form>;
}

