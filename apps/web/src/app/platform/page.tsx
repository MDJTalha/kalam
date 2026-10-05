import type { Metadata } from "next";
import { ArrowRight, BarChart3, BookOpenCheck, ShieldCheck, Target } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { PublicButton } from "@/components/public-button";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "Platform | Kalam",
  description: "Explore Kalam's connected corporate capability development platform.",
  alternates: { canonical: "/platform" },
};

const pillars = [
  ["01", Target, "Understand", "Connect strategy, capabilities, competencies, roles and workforce requirements."],
  ["02", ShieldCheck, "Assess", "Measure demonstrated capability through structured assessment and evidence."],
  ["03", BookOpenCheck, "Develop", "Turn capability gaps into focused development action and experiences."],
  ["04", BarChart3, "Improve", "Reassess capability and connect progress to performance insight."],
] as const;

export default function PlatformPage() {
  return <CommercialShell>
    <section className={styles.hero}><div className={styles.container}><div className={styles.heroGrid}>
      <div><span className={styles.kicker}>KALAM PLATFORM</span><h1>One connected <span className={styles.heroAccent}>capability system.</span></h1><p>Kalam connects strategy, people, capability, assessment, evidence and development in one enterprise platform.</p><div className={styles.heroActions}><PublicButton href="/guided-evaluation">Evaluate Kalam <ArrowRight size={15}/></PublicButton><PublicButton href="/contact-sales" variant="secondary">Talk to Sales</PublicButton></div></div>
      <div className={styles.heroPanel}><span>THE KALAM LIFECYCLE</span><h2>From business need to demonstrated capability.</h2><p>Strategy → Capability → People → Assess → Develop → Reassess → Performance.</p></div>
    </div></div></section>

    <section className={styles.section}><div className={styles.container}>
      <div className={styles.sectionHead}><div><span className={styles.kicker}>THE PLATFORM</span><h2>Four capabilities.<br/><em>One connected lifecycle.</em></h2></div><p>Kalam keeps the capability story connected from the business requirement through evidence, development and improvement.</p></div>
      <div className={styles.grid4}>{pillars.map(([number,Icon,title,copy]) => <article className={styles.card} key={title}><span className={styles.planBadge}>{number}</span><Icon size={22}/><h3>{title}</h3><p>{copy}</p></article>)}</div>
    </div></section>

    <section className={styles.sectionAlt}><div className={styles.container}>
      <div className={styles.sectionHead}><div><span className={styles.kicker}>WHY IT MATTERS</span><h2>Move beyond activity.<br/><em>See capability.</em></h2></div><p>Learning completion is useful. Demonstrated capability is more meaningful. Kalam connects the two in the context of business need.</p></div>
      <div className={styles.grid3}>
        <article className={styles.card}><h3>Required capability</h3><p>Define what the business needs by capability, competency and role.</p></article>
        <article className={styles.card}><h3>Demonstrated capability</h3><p>Use assessments and evidence to establish what people can demonstrate.</p></article>
        <article className={styles.card}><h3>Capability improvement</h3><p>Direct development, reassess progress and understand what changed.</p></article>
      </div>
    </div></section>

    <section className={styles.section}><div className={styles.container}><div className={styles.heroPanel}>
      <span className={styles.kicker}>THE DIFFERENCE</span><h2>Connect what the business needs with what people can demonstrate.</h2><p>Kalam adds the capability layer between strategy, workforce data and development.</p>
      <div className={styles.heroActions}><PublicButton href="/solutions">Explore solutions <ArrowRight size={15}/></PublicButton><PublicButton href="/pricing" variant="secondary">View pricing</PublicButton></div>
    </div></div></section>
  </CommercialShell>;
}
