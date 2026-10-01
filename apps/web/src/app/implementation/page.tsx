import type { Metadata } from "next";
import { ArrowRight, CheckCircle2, Database, Flag, Settings2, ShieldCheck, UsersRound } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { PublicButton } from "@/components/public-button";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "Implementation",
  description: "Review the Kalam enterprise implementation approach from discovery and design through validation, rollout and adoption.",
  alternates: { canonical: "/implementation" },
};

const phases = [
  ["01", "Discover", "Clarify business outcomes, stakeholder groups, governance, evidence requirements and the workflows that matter most."],
  ["02", "Design", "Confirm organization structure, roles, permissions, data flows, migration scope and implementation ownership."],
  ["03", "Configure", "Set up the agreed capability, learning, assessment and compliance workflows in a controlled environment."],
  ["04", "Integrate", "Connect the approved identity, people-data, reporting and external-service flows required for the deployment."],
  ["05", "Validate", "Test representative scenarios with the administrators, managers and business owners who will use and govern them."],
  ["06", "Roll out", "Sequence launch, adoption, support and operational ownership around the agreed business scope."],
] as const;

export default function ImplementationPage() {
  return <CommercialShell>
    <section className={styles.hero}><div className={styles.container}><div className={styles.heroGrid}>
      <div><span className={styles.kicker}><Flag size={14}/> Enterprise implementation</span><h1>Go from capability strategy to <span className={styles.heroAccent}>a governed rollout.</span></h1><p>Kalam implementation starts with the business outcome, operating model and people who will own the change—then turns that foundation into a controlled path to adoption.</p><div className={styles.heroActions}><PublicButton href="/contact-sales">Contact sales <ArrowRight size={15}/></PublicButton><PublicButton href="/guided-evaluation" variant="secondary">Run a guided evaluation</PublicButton></div></div>
      <div className={styles.heroPanel}><span>IMPLEMENTATION PRINCIPLE</span><h2>Start with representative business scenarios.</h2><p>Use a defined workforce problem, the people who own it and the evidence required to validate that Kalam fits the operating model you intend to deploy.</p><div className={styles.signalRow}><div><strong>Business</strong><span>Outcomes & owners</span></div><div><strong>Technology</strong><span>Data & identity</span></div><div><strong>Adoption</strong><span>Launch & governance</span></div></div></div>
    </div></div></section>

    <section className={styles.section}><div className={styles.container}>
      <div className={styles.sectionHead}><div><span className={styles.kicker}>IMPLEMENTATION JOURNEY</span><h2>From operating reality to governed rollout.</h2></div><p>The exact sequence and responsibilities are confirmed for each deployment. The framework below shows the implementation areas that should be addressed before production launch.</p></div>
      <div className={styles.grid3}>{phases.map(([number,title,description]) => <article className={styles.card} key={number}><span className={styles.planBadge}>{number}</span><h3>{title}</h3><p>{description}</p></article>)}</div>
    </div></section>

    <section className={styles.sectionAlt}><div className={styles.container}>
      <div className={styles.sectionHead}><div><span className={styles.kicker}>READINESS CHECK</span><h2>What enterprise teams should align early.</h2></div><p>Clear ownership reduces rework and helps technical, HR, learning and compliance teams evaluate the same deployment assumptions.</p></div>
      <div className={styles.grid4}>
        <article className={styles.card}><UsersRound size={22}/><h3>Stakeholders & ownership</h3><p>Executive sponsor, business owners, administrators, technical owners and the teams responsible for adoption.</p></article>
        <article className={styles.card}><Database size={22}/><h3>Data & migration</h3><p>People data, organizational structure, learning history, capability records and the quality rules applied to migration.</p></article>
        <article className={styles.card}><Settings2 size={22}/><h3>Configuration</h3><p>Roles, permissions, workflows, notifications, reporting and the governance boundaries required for the operating model.</p></article>
        <article className={styles.card}><ShieldCheck size={22}/><h3>Security & launch</h3><p>Identity, access, data flows, validation evidence, launch criteria, support ownership and post-launch monitoring.</p></article>
      </div>
      <div className={`${styles.notice} ${styles.noticeSpacing}`}><CheckCircle2 size={18}/><span><strong>Deployment is scoped to the operating model.</strong> Timelines, migration responsibilities, integration scope and service commitments are confirmed in the agreed implementation plan for each customer.</span></div>
    </div></section>
  </CommercialShell>;
}
