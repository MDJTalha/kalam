import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Check, ClipboardList, Layers3, ShieldCheck } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { CommercialInquiryForm } from "@/components/commercial-inquiry-form";
import { PublicButton } from "@/components/public-button";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "Contact Sales",
  description: "Talk with Kalam about enterprise learning, workforce capability, compliance, implementation and commercial fit.",
  alternates: { canonical: "/contact-sales" },
};

const conversation = [
  { number: "01", title: "Your priorities", detail: "Workforce scale, goals, regions and the decisions you need to make." },
  { number: "02", title: "Platform fit", detail: "Relevant learning, capability and readiness workflows, including integration needs." },
  { number: "03", title: "A practical path", detail: "Evaluation scope, implementation considerations and commercial options." },
];

export default function ContactSalesPage() {
  return <CommercialShell>
    <section className={styles.salesHero} aria-labelledby="sales-title">
      <div className={styles.container}>
        <div className={styles.salesLayout}>
          <div className={styles.salesIntro}>
            <span className={styles.salesEyebrow}><span className={styles.salesEyebrowDot}/> Let&apos;s talk</span>
            <h1 id="sales-title">Start with the <span>outcome you need.</span></h1>
            <p className={styles.salesLead}>Tell us where your organization needs stronger capability, learning, compliance or workforce readiness. We&apos;ll use that context to shape the right conversation from the outset.</p>
            <div className={styles.salesValueRow} aria-label="What happens after you submit">
              <div><strong>01</strong><span>Share priorities</span></div>
              <div><strong>02</strong><span>Align the conversation</span></div>
              <div><strong>03</strong><span>Define next steps</span></div>
            </div>
            <PublicButton className={styles.salesJump} href="#sales-inquiry" variant="primary">Tell us what you need <ArrowRight size={16} aria-hidden="true"/></PublicButton>
            <div className={styles.salesConversation}>
              <div className={styles.salesConversationHead}><ClipboardList size={19} aria-hidden="true"/><h2>Bring the context that matters</h2></div>
              <ol>{conversation.map(item => <li key={item.number}><span className={styles.salesNumber}>{item.number}</span><div><strong>{item.title}</strong><p>{item.detail}</p></div></li>)}</ol>
            </div>
            <div className={styles.salesExplore}>
              <span>Exploring first?</span>
              <Link href="/trust">Security &amp; trust <ArrowRight size={14} aria-hidden="true"/></Link>
              <Link href="/pricing">Pricing approach <ArrowRight size={14} aria-hidden="true"/></Link>
            </div>
          </div>
          <div id="sales-inquiry" className={styles.salesForm}><CommercialInquiryForm mode="sales"/></div>
        </div>
      </div>
    </section>
    <section className={styles.salesAssurance} aria-label="Enterprise evaluation topics">
      <div className={styles.container}>
        <div className={styles.salesAssuranceGrid}>
          <div><Layers3 size={20} aria-hidden="true"/><span><strong>Fit to your workflows</strong><small>Learning, skills, capability and readiness</small></span></div>
          <div><ShieldCheck size={20} aria-hidden="true"/><span><strong>Governance in scope</strong><small>Access, security and data requirements</small></span></div>
          <div><Check size={20} aria-hidden="true"/><span><strong>A considered next step</strong><small>Evaluation and rollout aligned to your needs</small></span></div>
        </div>
      </div>
    </section>
  </CommercialShell>;
}
