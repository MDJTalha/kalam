import type { Metadata } from "next";
import { ArrowRight, Braces, Database, FileInput, KeyRound, Network, Webhook } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { PublicButton } from "@/components/public-button";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "Integrations | Kalam",
  description: "Review the enterprise integration areas considered during Kalam solution design.",
  alternates: { canonical: "/integrations" },
};

export default function IntegrationsPage() {
  return <CommercialShell>
    <section className={styles.hero}><div className={styles.container}><div className={styles.heroGrid}>
      <div><span className={styles.kicker}><Network size={14}/> INTEGRATIONS</span><h1>Connect Kalam to <span className={styles.heroAccent}>your enterprise environment.</span></h1><p>Scope identity, people data, learning, reporting and APIs around your architecture, ownership and security requirements.</p><div className={styles.heroActions}><PublicButton href="/contact-sales">Review your scope <ArrowRight size={15}/></PublicButton><PublicButton href="/implementation" variant="secondary">Implementation</PublicButton></div></div>
      <div className={styles.heroPanel}><span>INTEGRATION PRINCIPLE</span><h2>Scope first. Validate with evidence.</h2><p>Each connector and service dependency is confirmed against the current product and deployment requirements before it is represented as supported.</p></div>
    </div></div></section>

    <section className={styles.section}><div className={styles.container}>
      <div className={styles.sectionHead}><div><span className={styles.kicker}>INTEGRATION AREAS</span><h2>Connect the systems that matter.</h2></div><p>These categories describe the integration work that can be evaluated and scoped with your technical team.</p></div>
      <div className={styles.grid3}>
        <article className={styles.card}><KeyRound size={22}/><h3>Identity & access</h3><p>Authentication and organization access aligned to the approved identity model.</p></article>
        <article className={styles.card}><Database size={22}/><h3>People & organization</h3><p>Employee, role, manager, business-unit and location data from authoritative sources.</p></article>
        <article className={styles.card}><FileInput size={22}/><h3>Learning data</h3><p>Content, assignments, learning history and evidence flows required by the operating model.</p></article>
        <article className={styles.card}><Braces size={22}/><h3>APIs & data exchange</h3><p>Defined interfaces aligned to authorization, data ownership and solution architecture.</p></article>
        <article className={styles.card}><Webhook size={22}/><h3>Events & webhooks</h3><p>Workflow events validated for the specific destinations and controls involved.</p></article>
        <article className={styles.card}><Network size={22}/><h3>Reporting</h3><p>Exports and downstream consumption for analytics, audit and operational teams.</p></article>
      </div>
    </div></section>

    <section className={styles.sectionAlt}><div className={styles.container}>
      <div className={styles.notice}><Network size={18}/><span><strong>No blanket integration claims.</strong> Your evaluation confirms the connector, protocol, data scope, ownership boundary and support commitment relevant to the deployment.</span></div>
    </div></section>
  </CommercialShell>;
}
