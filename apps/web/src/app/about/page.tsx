import type { Metadata } from "next";
import { ArrowRight, Compass, Eye, Target } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { PublicButton } from "@/components/public-button";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "About Kalam",
  description: "Learn what Kalam believes about organizational capability and the technology it is building.",
  alternates: { canonical: "/about" },
};

export default function AboutPage() {
  return <CommercialShell>
    <section className={styles.hero}><div className={styles.container}><div className={styles.heroGrid}>
      <div><span className={styles.kicker}>ABOUT KALAM</span><h1>Technology for the <span className={styles.heroAccent}>capability economy.</span></h1><p>Kalam exists to help organizations understand, develop and improve the capabilities that drive performance.</p><div className={styles.heroActions}><PublicButton href="/platform">Explore the platform <ArrowRight size={15}/></PublicButton><PublicButton href="/contact-sales" variant="secondary">Talk to Sales</PublicButton></div></div>
      <div className={styles.heroPanel}><span>OUR BELIEF</span><h2>Organizations perform when people can turn strategy into action.</h2><p>Kalam connects those two realities through capability technology.</p></div>
    </div></div></section>

    <section className={styles.section}><div className={styles.container}>
      <div className={styles.sectionHead}><div><span className={styles.kicker}>OUR MISSION</span><h2>Make organizational capability <em>visible, actionable and measurable.</em></h2></div><p>Give organizations a clearer way to understand what they need, what they have, what is missing and what to do next.</p></div>
      <div className={styles.grid3}>
        <article className={styles.card}><Target size={22}/><h3>Visible</h3><p>Make capability requirements, evidence and gaps easier to see.</p></article>
        <article className={styles.card}><Compass size={22}/><h3>Actionable</h3><p>Turn capability insight into focused development decisions.</p></article>
        <article className={styles.card}><Eye size={22}/><h3>Measurable</h3><p>Reassess progress and understand whether capability improved.</p></article>
      </div>
    </div></section>

    <section className={styles.sectionAlt}><div className={styles.container}><div className={styles.heroPanel}>
      <span className={styles.kicker}>OUR VISION</span><h2>A world where every organization can understand and build the capabilities it needs to perform.</h2><p>Simple for people. Powerful for organizations.</p>
    </div></div></section>
  </CommercialShell>;
}
