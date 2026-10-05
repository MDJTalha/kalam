import type { Metadata } from "next";
import { ArrowRight, CheckCircle2, Database, Flag, Settings2, ShieldCheck, UsersRound } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { PublicButton } from "@/components/public-button";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "Implementation | Kalam",
  description: "See how Kalam moves from capability priorities to a governed enterprise rollout.",
  alternates: { canonical: "/implementation" },
};

const phases = [
  ["01", "Discover", "Clarify outcomes, owners and the workflows that matter."],
  ["02", "Design", "Confirm organization, roles, permissions, data and ownership."],
  ["03", "Configure", "Set up the agreed capability and development workflows."],
  ["04", "Integrate", "Connect approved identity, people-data and reporting flows."],
  ["05", "Validate", "Test representative scenarios with accountable stakeholders."],
  ["06", "Roll out", "Sequence launch, adoption, support and operational ownership."],
] as const;

export default function ImplementationPage() {
  return <CommercialShell>
    <section className={styles.hero}><div className={styles.container}><div className={styles.heroGrid}>
      <div><span className={styles.kicker}><Flag size={14}/> IMPLEMENTATION</span><h1>From capability priority to <span className={styles.heroAccent}>governed adoption.</span></h1><p>Start with the business outcome, design around the operating model, validate the workflows and move to rollout with clear ownership.</p><div className={styles.heroActions}><PublicButton href="/contact-sales">Talk to Sales <ArrowRight size={15}/></PublicButton><PublicButton href="/guided-evaluation" variant="secondary">Evaluate Kalam</PublicButton></div></div>
      <div className={styles.heroPanel}><span>IMPLEMENTATION PRINCIPLE</span><h2>Use real business scenarios.</h2><p>Define the workforce problem, the people who own it and the evidence needed to validate the deployment.</p><div className={styles.signalRow}><div><strong>Business</strong><span>Outcome & owners</span></div><div><strong>Technology</strong><span>Data & identity</span></div><div><strong>Adoption</strong><span>Launch & governance</span></div></div></div>
    </div></div></section>

    <section className={styles.section}><div className={styles.container}>
      <div className={styles.sectionHead}><div><span className={styles.kicker}>IMPLEMENTATION JOURNEY</span><h2>A controlled path to rollout.</h2></div><p>The exact scope is agreed for each customer. The framework stays focused on the decisions that must be clear before launch.</p></div>
      <div className={styles.grid3}>{phases.map(([number,title,description]) => <article className={styles.card} key={number}><span className={styles.planBadge}>{number}</span><h3>{title}</h3><p>{description}</p></article>)}</div>
    </div></section>

    <section className={styles.sectionAlt}><div className={styles.container}>
      <div className={styles.sectionHead}><div><span className={styles.kicker}>READYING THE ORGANIZATION</span><h2>Align the essentials early.</h2></div><p>Clear ownership reduces rework and keeps business, technology and governance decisions connected.</p></div>
      <div className={styles.grid4}>
        <article className={styles.card}><UsersRound size={22}/><h3>Owners</h3><p>Executive sponsor, business owners, administrators and technical owners.</p></article>
        <article className={styles.card}><Database size={22}/><h3>Data</h3><p>People, organization, learning history and capability records.</p></article>
        <article className={styles.card}><Settings2 size={22}/><h3>Configuration</h3><p>Roles, permissions, workflows, notifications and reporting.</p></article>
        <article className={styles.card}><ShieldCheck size={22}/><h3>Launch</h3><p>Identity, validation, launch criteria, support and monitoring.</p></article>
      </div>
      <div className={`${styles.notice} ${styles.noticeSpacing}`}><CheckCircle2 size={18}/><span><strong>Scope is customer-specific.</strong> Migration, integrations, timelines and service commitments are confirmed in the agreed implementation plan.</span></div>
    </div></section>
  </CommercialShell>;
}
