import type { Metadata } from "next";
import { ArrowRight, BarChart3, BookOpenCheck, BriefcaseBusiness, UsersRound } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { PublicButton } from "@/components/public-button";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "Solutions | Kalam",
  description: "Kalam solutions for executives, HR and people leaders, L&D leaders and managers.",
  alternates: { canonical: "/solutions" },
};

const audiences = [
  [BriefcaseBusiness, "Executive Leadership", "Make capability visible.", "See whether the organization has the capabilities required to execute strategy."],
  [UsersRound, "CHRO & People", "Understand workforce readiness.", "Connect people, roles, capability and development in one operating picture."],
  [BookOpenCheck, "L&D Leadership", "Develop what matters.", "Align development investment with the capabilities the business actually needs."],
  [BarChart3, "Managers", "Act on team capability.", "See gaps, evidence and next actions without losing the business context."],
] as const;

export default function SolutionsPage() {
  return <CommercialShell>
    <section className={styles.hero}><div className={styles.container}><div className={styles.heroGrid}>
      <div><span className={styles.kicker}>KALAM SOLUTIONS</span><h1>Capability insight for <span className={styles.heroAccent}>every decision-maker.</span></h1><p>One connected capability picture, with the right insight for the people responsible for strategy, workforce and development.</p><div className={styles.heroActions}><PublicButton href="/guided-evaluation">Get started <ArrowRight size={15}/></PublicButton><PublicButton href="/contact-sales" variant="secondary">Talk to Sales</PublicButton></div></div>
      <div className={styles.heroPanel}><span>ONE SYSTEM</span><h2>Different questions. One capability picture.</h2><p>Executives need visibility. HR needs workforce intelligence. L&D needs development focus. Managers need action.</p></div>
    </div></div></section>

    <section className={styles.section}><div className={styles.container}>
      <div className={styles.sectionHead}><div><span className={styles.kicker}>FOR LEADERS</span><h2>Built around the decisions<br/><em>your role has to make.</em></h2></div><p>Kalam does not create another isolated data layer. It connects capability insight to the people accountable for using it.</p></div>
      <div className={styles.grid4}>{audiences.map(([Icon,title,headline,copy]) => <article className={styles.card} key={title}><Icon size={22}/><span className={styles.planBadge}>{title}</span><h3>{headline}</h3><p>{copy}</p></article>)}</div>
    </div></section>

    <section className={styles.sectionAlt}><div className={styles.container}>
      <div className={styles.sectionHead}><div><span className={styles.kicker}>BUSINESS USE CASES</span><h2>Start with the outcome.</h2></div><p>Use Kalam to make capability decisions clearer across workforce planning, development, readiness and performance.</p></div>
      <div className={styles.grid3}>
        <article className={styles.card}><h3>Workforce readiness</h3><p>Understand whether people and roles have the capability required for the work ahead.</p></article>
        <article className={styles.card}><h3>Capability risk</h3><p>See where capability gaps may affect execution and where leadership attention matters.</p></article>
        <article className={styles.card}><h3>Development effectiveness</h3><p>Connect development investment to capability improvement and reassessment.</p></article>
      </div>
    </div></section>

    <section className={styles.section}><div className={styles.container}><div className={styles.heroPanel}>
      <span className={styles.kicker}>NEXT STEP</span><h2>Bring a real capability challenge.</h2><p>We will use your operating context to show where Kalam fits and what the right next step looks like.</p><div className={styles.heroActions}><PublicButton href="/guided-evaluation">Evaluate Kalam</PublicButton><PublicButton href="/contact-sales" variant="secondary">Talk to Sales</PublicButton></div>
    </div></div></section>
  </CommercialShell>;
}
