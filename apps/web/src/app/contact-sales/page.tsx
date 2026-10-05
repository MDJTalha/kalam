import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Check, ClipboardList, Layers3, ShieldCheck } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { CommercialInquiryForm } from "@/components/commercial-inquiry-form";
import { PublicButton } from "@/components/public-button";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "Talk to Sales | Kalam",
  description: "Talk with Kalam about your organization's capability priorities, enterprise fit and path to adoption.",
  alternates: { canonical: "/contact-sales" },
};

const conversation = [
  { number: "01", title: "Your priority", detail: "The capability or business outcome you want to improve." },
  { number: "02", title: "Your context", detail: "Workforce scale, operating model and technology environment." },
  { number: "03", title: "Your next step", detail: "Evaluation, implementation and commercial fit." },
];

export default function ContactSalesPage() {
  return <CommercialShell>
    <section className={styles.salesHero} aria-labelledby="sales-title">
      <div className={styles.container}>
        <div className={styles.salesLayout}>
          <div className={styles.salesIntro}>
            <span className={styles.salesEyebrow}><span className={styles.salesEyebrowDot}/> TALK TO KALAM</span>
            <h1 id="sales-title">Start with the <span>outcome that matters.</span></h1>
            <p className={styles.salesLead}>Tell us what your organization needs to build, measure or improve. We'll shape the conversation around your operating reality.</p>
            <div className={styles.salesValueRow} aria-label="What happens after you submit">
              <div><strong>01</strong><span>Share the priority</span></div>
              <div><strong>02</strong><span>Align the context</span></div>
              <div><strong>03</strong><span>Define the next step</span></div>
            </div>
            <PublicButton className={styles.salesJump} href="#sales-inquiry" variant="inverse">Start the conversation <ArrowRight size={16} aria-hidden="true"/></PublicButton>
            <div className={styles.salesConversation}>
              <div className={styles.salesConversationHead}><ClipboardList size={19} aria-hidden="true"/><h2>Bring what matters</h2></div>
              <ol>{conversation.map(item => <li key={item.number}><span className={styles.salesNumber}>{item.number}</span><div><strong>{item.title}</strong><p>{item.detail}</p></div></li>)}</ol>
            </div>
            <div className={styles.salesExplore}>
              <span>Explore first?</span>
              <Link href="/trust">Security &amp; trust <ArrowRight size={14} aria-hidden="true"/></Link>
              <Link href="/pricing">Pricing <ArrowRight size={14} aria-hidden="true"/></Link>
            </div>
          </div>
          <div id="sales-inquiry" className={styles.salesForm}><CommercialInquiryForm mode="sales"/></div>
        </div>
      </div>
    </section>

    <section className={styles.salesAssurance} aria-label="Enterprise evaluation topics">
      <div className={styles.container}>
        <div className={styles.salesAssuranceGrid}>
          <div><Layers3 size={20} aria-hidden="true"/><span><strong>Business fit</strong><small>Capability, development and performance priorities</small></span></div>
          <div><ShieldCheck size={20} aria-hidden="true"/><span><strong>Enterprise fit</strong><small>Governance, access and data requirements</small></span></div>
          <div><Check size={20} aria-hidden="true"/><span><strong>Practical next step</strong><small>Evaluation or rollout aligned to your needs</small></span></div>
        </div>
      </div>
    </section>
  </CommercialShell>;
}
