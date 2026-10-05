import type { Metadata } from "next";
import { ArrowRight, Check, CircleDollarSign, ShieldCheck, UsersRound } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { PublicButton } from "@/components/public-button";
import { KalamBrand } from "@/components/kalam-brand";
import { formatCommercialPrice, getPublicCommercialCatalog, type PublicPlan } from "@/lib/public-commercial";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "Kalam Pricing | Corporate Capability Development Platform",
  description: "Explore Kalam pricing and choose the scale of capability development, assessment and workforce intelligence that fits your organization.",
  keywords: ["Kalam pricing", "corporate capability development", "workforce capability platform", "capability assessment", "enterprise development"],
  alternates: { canonical: "/pricing" },
};

function minimumCommitment(plan: PublicPlan) {
  if (plan.billing_model !== "per_user" || plan.monthly_price_minor == null) return null;
  return formatCommercialPrice(plan.monthly_price_minor * plan.minimum_seats, plan.currency);
}

function seatLabel(plan: PublicPlan) {
  if (plan.maximum_seats) return `${plan.minimum_seats.toLocaleString()}–${plan.maximum_seats.toLocaleString()} users`;
  if (plan.minimum_seats > 1) return `From ${plan.minimum_seats.toLocaleString()} users`;
  return "Flexible user scale";
}

function merchandisingFor(plan: PublicPlan) {
  const raw = plan.limits?.public_merchandising;
  const merchandising = raw && typeof raw === "object" ? raw as Record<string, unknown> : {};
  return {
    featured: merchandising.featured === true,
    ctaType: typeof merchandising.cta_type === "string" ? merchandising.cta_type : "auto",
    ctaLabel: typeof merchandising.cta_label === "string" ? merchandising.cta_label : "",
    comparisonLabel: typeof merchandising.comparison_label === "string" ? merchandising.comparison_label : "",
  };
}

export default async function PricingPage() {
  const catalog = await getPublicCommercialCatalog();
  const plans = catalog.plans.filter((plan) => plan.currency === "USD");

  return <CommercialShell>
    <section className={styles.pricingHero}>
      <div className={styles.container}>
        <div className={styles.pricingHeroGrid}>
          <div>
            <span className={styles.kicker}><CircleDollarSign size={14}/> KALAM PRICING</span>
            <h1><span className={styles.heroLead}>Build capability.</span><span className={styles.heroAccent}>Scale with confidence.</span></h1>
            <p>Choose the Kalam scale that fits your organization, from focused capability development to enterprise deployment.</p>
            <div className={styles.heroActions}>
              <PublicButton href="#plans">View plans</PublicButton>
              <PublicButton href="/contact-sales" variant="secondary">Talk to Sales</PublicButton>
            </div>
            <div className={styles.pricingTrust}>
              <span><ShieldCheck size={15}/> Active USD pricing</span>
              <span><UsersRound size={15}/> Built for organizational scale</span>
            </div>
          </div>
          <aside className={styles.pricingPromise}>
            <div className={styles.promiseBrand}><span>THE KALAM APPROACH</span><KalamBrand dark compact className={styles.promiseLogo}/></div>
            <div className={styles.promiseIntro}><strong>One platform for the capability lifecycle.</strong><span>Choose the plan that matches your scope and operating model.</span></div>
            <div className={styles.promiseList}>
              <div><span className={styles.promiseIndex}>01</span><div><b>Understand</b><small>Strategy, capabilities, competencies and roles</small></div></div>
              <div><span className={styles.promiseIndex}>02</span><div><b>Assess</b><small>Assessment, evidence and demonstrated capability</small></div></div>
              <div><span className={styles.promiseIndex}>03</span><div><b>Develop</b><small>Development action, progress and reassessment</small></div></div>
            </div>
            <div className={styles.promiseFoot}><span>CAPABILITY</span><span>ASSESSMENT</span><span>DEVELOPMENT</span></div>
          </aside>
        </div>
      </div>
    </section>

    <section id="plans" className={styles.pricingSection}>
      <div className={styles.container}>
        <div className={styles.sectionHead}>
          <div><span className={styles.kicker}>PLANS</span><h2>Choose the right scale.</h2></div>
          <p>Clear pricing for the scope your organization needs. Active commercial plans are published directly from Kalam's approved pricing catalogue.</p>
        </div>

        {plans.length ? <div className={styles.pricingGrid}>{plans.map((plan) => {
          const monthly = formatCommercialPrice(plan.monthly_price_minor, plan.currency);
          const annual = formatCommercialPrice(plan.annual_price_minor, plan.currency);
          const minimum = minimumCommitment(plan);
          const features = Array.isArray(plan.features) ? plan.features.filter((item): item is string => typeof item === "string") : [];
          const merch = merchandisingFor(plan);
          const recommended = merch.featured;
          const perUser = plan.billing_model === "per_user";
          const useEvaluation = merch.ctaType === "evaluation" || (merch.ctaType === "auto" && plan.trial_days > 0);
          const ctaLabel = merch.ctaLabel || (useEvaluation ? `Evaluate ${plan.name}` : "Contact sales");

          return <article className={`${styles.pricingCard} ${recommended ? styles.pricingCardFeatured : ""}`} key={plan.id}>
            <div className={styles.planTopline}><span className={styles.planBadge}>{plan.billing_model.replaceAll("_", " ")}</span></div>
            <div className={styles.planName}>{plan.name}</div>
            <div className={styles.planTag}>{plan.tagline || plan.description || "Kalam capability platform plan"}</div>
            {merch.comparisonLabel && <div className={styles.comparisonLabel}>{merch.comparisonLabel}</div>}
            <div className={styles.priceBlock}>
              <div className={styles.price}>{monthly || annual || "Custom"}</div>
              {monthly && <span>{perUser ? "per user / month" : "per month"}</span>}
              {annual && <div className={styles.annualPrice}><strong>{annual}</strong><span>billed annually{perUser ? " per user" : ""}</span></div>}
            </div>
            <div className={styles.commercialMeta}>
              <span><UsersRound size={14}/>{seatLabel(plan)}</span>
              {minimum && <span>Minimum: {minimum} / month</span>}
            </div>
            <ul className={styles.pricingFeatures}>
              {features.slice(0, 5).map((item) => <li key={item}><Check size={15} aria-hidden="true"/>{item}</li>)}
            </ul>
            {useEvaluation
              ? <PublicButton className={styles.planAction} href={`/guided-evaluation?plan=${encodeURIComponent(plan.code)}`}>{ctaLabel}</PublicButton>
              : <PublicButton className={styles.planAction} href={`/contact-sales?plan=${encodeURIComponent(plan.code)}`} variant={recommended ? "primary" : "secondary"}>{ctaLabel}</PublicButton>}
          </article>;
        })}</div> : <div className={styles.empty}><strong>Commercial plans are being prepared.</strong><p>The pricing page publishes only active USD plans approved in CRM. Contact Sales for a scoped proposal.</p><div className={`${styles.heroActions} ${styles.centeredActions}`}><PublicButton href="/contact-sales">Contact Sales</PublicButton></div></div>}
      </div>
    </section>

    <section className={styles.pricingClose}>
      <div className={styles.container}>
        <div className={styles.pricingCloseInner}>
          <div><span className={styles.kicker}>ENTERPRISE</span><h2>Need a tailored deployment?</h2><p>Discuss workforce scale, integrations and implementation with the Kalam team.</p></div>
          <PublicButton href="/contact-sales">Talk to Sales <ArrowRight size={15}/></PublicButton>
        </div>
        <div className={styles.notice}><ShieldCheck size={18}/><span>Final commercial terms are confirmed in your customer agreement.</span></div>
      </div>
    </section>
  </CommercialShell>;
}
