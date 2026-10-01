import type { Metadata } from "next";
import { ArrowRight, Braces, Database, FileInput, KeyRound, Network, Webhook } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { PublicButton } from "@/components/public-button";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "Integrations",
  description: "Review the integration areas Kalam considers during enterprise solution design, including identity, people data, reporting, APIs and webhooks.",
  alternates: { canonical: "/integrations" },
};

export default function IntegrationsPage() {
  return <CommercialShell>
    <section className={styles.hero}><div className={styles.container}><div className={styles.heroGrid}>
      <div><span className={styles.kicker}><Network size={14}/> Enterprise integrations</span><h1>Connect Kalam to <span className={styles.heroAccent}>your enterprise ecosystem.</span></h1><p>Kalam is designed to fit alongside the systems that already run your organization. We scope identity, people data, learning, reporting and APIs around your architecture, data ownership and security requirements.</p><div className={styles.heroActions}><PublicButton href="/contact-sales">Review your integration scope <ArrowRight size={15}/></PublicButton><PublicButton href="/implementation" variant="secondary">Implementation approach</PublicButton></div></div>
      <div className={styles.heroPanel}><span>INTEGRATION PRINCIPLE</span><h2>Scope first. Validate second. Commit after evidence.</h2><p>Each connector, data flow and service dependency should be confirmed against the current product, technical architecture and deployment requirements before it is represented as supported.</p></div>
    </div></div></section>

    <section className={styles.section}><div className={styles.container}>
      <div className={styles.sectionHead}><div><span className={styles.kicker}>INTEGRATION AREAS</span><h2>Connect the systems that support capability work.</h2></div><p>Availability varies by deployment. These categories describe the integration work that can be evaluated and scoped with your technical team.</p></div>
      <div className={styles.grid3}>
        <article className={styles.card}><KeyRound size={22}/><h3>Identity & access</h3><p>Authentication, organization access and identity flows should align with the access model approved for your deployment.</p></article>
        <article className={styles.card}><Database size={22}/><h3>People & organization data</h3><p>Employee, role, manager, business-unit and location data can be scoped around the systems that remain authoritative.</p></article>
        <article className={styles.card}><FileInput size={22}/><h3>Content & learning data</h3><p>Review the content, assignment, history and evidence flows required to support the learning operating model.</p></article>
        <article className={styles.card}><Braces size={22}/><h3>APIs & data exchange</h3><p>Use defined interfaces where they fit the approved solution architecture, authorization boundaries and data ownership model.</p></article>
        <article className={styles.card}><Webhook size={22}/><h3>Events & webhooks</h3><p>Event-driven integrations should be validated for the specific workflows, security controls and destinations involved.</p></article>
        <article className={styles.card}><Network size={22}/><h3>Reporting & downstream systems</h3><p>Confirm the reporting, export and downstream consumption patterns needed by analytics, audit and operational teams.</p></article>
      </div>
    </div></section>

    <section className={styles.sectionAlt}><div className={styles.container}>
      <div className={styles.notice}><Network size={18}/><span><strong>Integration names and logos are intentionally not presented as blanket claims.</strong> Your evaluation should confirm each required connector, protocol, data field, ownership boundary and support commitment before deployment.</span></div>
    </div></section>
  </CommercialShell>;
}
