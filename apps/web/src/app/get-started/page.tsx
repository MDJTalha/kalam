import type { Metadata } from "next";
import { ArrowRight, CheckCircle2, MessageSquareText } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { PublicButton } from "@/components/public-button";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "Get Started | Kalam",
  description: "Start your Kalam evaluation and define the right path for your organization.",
  alternates: { canonical: "/get-started" },
};

const steps = [
  ["01", "Choose the path", "Evaluate Kalam or start an enterprise conversation."],
  ["02", "Bring your context", "Use the capability challenge, workforce scenario or business outcome that matters."],
  ["03", "Define the next move", "Leave with a clearer evaluation, implementation or commercial path."],
] as const;

export default function GetStartedPage() {
  return <CommercialShell>
    <section className={styles.hero}><div className={styles.container}><div className={styles.heroGrid}>
      <div><span className={styles.kicker}>GET STARTED WITH KALAM</span><h1>Build the capabilities <span className={styles.heroAccent}>your business needs.</span></h1><p>Start with a real capability priority. Kalam will help you evaluate the platform in the context of your organization.</p><div className={styles.heroActions}><PublicButton href="/guided-evaluation">Start an evaluation <ArrowRight size={15}/></PublicButton><PublicButton href="/contact-sales" variant="secondary">Talk to Sales</PublicButton></div></div>
      <div className={styles.heroPanel}><span>THE NEXT STEP</span><h2>Useful context beats a generic demo.</h2><p>Bring the role, capability, workforce or development challenge you want to improve.</p></div>
    </div></div></section>

    <section className={styles.section}><div className={styles.container}>
      <div className={styles.sectionHead}><div><span className={styles.kicker}>HOW TO START</span><h2>Three simple steps.</h2></div><p>Keep the first conversation focused, practical and relevant to your organization.</p></div>
      <div className={styles.grid3}>{steps.map(([number,title,copy]) => <article className={styles.card} key={number}><span className={styles.planBadge}>{number}</span><CheckCircle2 size={22}/><h3>{title}</h3><p>{copy}</p></article>)}</div>
    </div></section>

    <section className={styles.sectionAlt}><div className={styles.container}><div className={styles.heroPanel}>
      <span className={styles.kicker}><MessageSquareText size={14}/> NEED A CONVERSATION?</span><h2>Talk to Kalam.</h2><p>We&apos;ll shape the next step around your capability priority, operating model and enterprise requirements.</p><div className={styles.heroActions}><PublicButton href="/contact-sales">Talk to Sales <ArrowRight size={15}/></PublicButton><PublicButton href="/pricing" variant="secondary">View pricing</PublicButton></div>
    </div></div></section>
  </CommercialShell>;
}
