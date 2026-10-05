import type { Metadata } from "next";
import { ArrowRight, BookOpen, Compass, FileText, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { CommercialShell } from "@/components/commercial-shell";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "Resources | Kalam",
  description: "Kalam resources on capability, workforce development, assessment, performance and enterprise adoption.",
  alternates: { canonical: "/resources" },
};

const resources = [
  ["Capability", "Build a clearer organizational capability model.", "#"],
  ["Workforce", "Understand readiness, gaps and workforce capability.", "#"],
  ["Development", "Connect development activity to capability need.", "#"],
  ["Enterprise", "Explore implementation, integration and trust.", "/trust"],
] as const;

export default function ResourcesPage() {
  return <CommercialShell>
    <section className={styles.hero}><div className={styles.container}><div className={styles.heroGrid}>
      <div><span className={styles.kicker}><BookOpen size={14}/> KALAM RESOURCES</span><h1>Ideas for building <span className={styles.heroAccent}>better organizations.</span></h1><p>Practical perspectives on capability, workforce development, assessment, performance and enterprise adoption.</p></div>
      <div className={styles.heroPanel}><span>START HERE</span><h2>Learn the language of capability.</h2><p>Understand the business problem before choosing the technology.</p></div>
    </div></div></section>

    <section className={styles.section}><div className={styles.container}>
      <div className={styles.sectionHead}><div><span className={styles.kicker}>EXPLORE</span><h2>Start with the question<br/><em>you need to answer.</em></h2></div><p>Resources are organized around the decisions that leaders and practitioners make about capability.</p></div>
      <div className={styles.grid4}>{resources.map(([title,copy,href],index) => <article className={styles.card} key={title}><span className={styles.planBadge}>0{index+1}</span><FileText size={22}/><h3>{title}</h3><p>{copy}</p>{href === "#" ? <span className={styles.verificationLink}>Coming soon</span> : <Link className={styles.verificationLink} href={href}>Explore <ArrowRight size={14}/></Link>}</article>)}</div>
    </div></section>

    <section className={styles.sectionAlt}><div className={styles.container}>
      <div className={styles.grid3}>
        <article className={styles.card}><Compass size={22}/><h3>Guided evaluation</h3><p>Evaluate Kalam against a representative workforce scenario.</p><Link className={styles.verificationLink} href="/guided-evaluation">Evaluate Kalam <ArrowRight size={14}/></Link></article>
        <article className={styles.card}><ShieldCheck size={22}/><h3>Security &amp; trust</h3><p>Review the enterprise foundations that matter before adoption.</p><Link className={styles.verificationLink} href="/trust">Review trust <ArrowRight size={14}/></Link></article>
        <article className={styles.card}><BookOpen size={22}/><h3>Customer stories</h3><p>See approved references and stories as they become available.</p><Link className={styles.verificationLink} href="/clients">View stories <ArrowRight size={14}/></Link></article>
      </div>
    </div></section>
  </CommercialShell>;
}
