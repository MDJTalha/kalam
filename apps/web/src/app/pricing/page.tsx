import type { Metadata } from "next";
import { ArrowRight, Check, CircleDollarSign, ShieldCheck, UsersRound, Zap } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { PublicButton } from "@/components/public-button";
import { KalamBrand } from "@/components/kalam-brand";
import { formatCommercialPrice, getPublicCommercialCatalog, type PublicPlan } from "@/lib/public-commercial";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "Kalam Pricing | Enterprise Workforce Capability Platform",
  description: "Explore Kalam pricing for enterprise learning, skills management, compliance and workforce readiness. Compare active plans and deployment options.",
  keywords: ["Kalam pricing", "workforce capability platform", "enterprise learning platform", "skills management software", "workforce readiness", "compliance management software"],
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
            <h1><span className={styles.heroLead}>Build workforce capability.</span><span className={styles.heroAccent}>Scale business performance.</span></h1>
            <p>One connected platform for learning, skills, compliance and workforce readiness—built to scale with your organization.</p>
            <div className={styles.heroActions}>
              <PublicButton href="#plans">Explore plans</PublicButton>
              <PublicButton href="/contact-sales" variant="secondary">Contact sales</PublicButton>
            </div>
            <div className={styles.pricingTrust}>
              <span><ShieldCheck size={15}/> Transparent USD pricing</span>
              <span><Zap size={15}/> Built to scale</span>
            </div>
          </div>
          <aside className={styles.pricingPromise}>
            <div className={styles.promiseBrand}><span>WHAT&apos;S INCLUDED</span><KalamBrand dark compact className={styles.promiseLogo}/></div>
            <div className={styles.promiseIntro}><strong>One platform to turn capability investment into workforce readiness.</strong><span>Choose the level of scale and support your organization needs.</span></div>
            <div className={styles.promiseList}>
              <div><span className={styles.promiseIndex}>01</span><div><b>Learning</b><small>Courses, programs and workforce development</small></div></div>
              <div><span className={styles.promiseIndex}>02</span><div><b>Skills &amp; readiness</b><small>Skills visibility, capability and role readiness</small></div></div>
              <div><span className={styles.promiseIndex}>03</span><div><b>Compliance</b><small>Governance, evidence and operational assurance</small></div></div>
            </div>
            <div className={styles.promiseFoot}><span>ONE PLATFORM</span><span>USD PRICING</span><span>ENTERPRISE READY</span></div>
          </aside>
        </div>
      </div>
    </section>

    <section id="plans" className={styles.pricingSection}>
      <div className={styles.container}>
        <div className={styles.sectionHead}>
          <div><span className={styles.kicker}>PLANS</span><h2>Choose the right scale for your workforce.</h2></div>
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
            <div className={styles.planTopline}>
              <span className={styles.planBadge}>{plan.billing_model.replaceAll("_", " ")}</span>
            </div>
            <div className={styles.planName}>{plan.name}</div>
            <div className={styles.planTag}>{plan.tagline || plan.description || "Kalam commercial plan"}</div>
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
        })}</div> : <div className={styles.empty}><strong>Commercial plans are being prepared.</strong><p>The pricing page publishes only active USD plans approved in CRM. Contact sales for a scoped proposal in the meantime.</p><div className={`${styles.heroActions} ${styles.centeredActions}`}><PublicButton href="/contact-sales">Request pricing</PublicButton></div></div>}
      </div>
    </section>

    <section className={styles.pricingClose}>
      <div className={styles.container}>
        <div className={styles.pricingCloseInner}>
          <div><span className={styles.kicker}>ENTERPRISE</span><h2>Need a tailored deployment?</h2><p>Talk to our team about workforce scale, integrations and implementation.</p></div>
          <PublicButton href="/contact-sales">Contact sales <ArrowRight size={15}/></PublicButton>
        </div>
        <div className={styles.notice}><ShieldCheck size={18}/><span>Final commercial terms are confirmed in your customer agreement.</span></div>
      </div>
    </section>
  </CommercialShell>;
}
