import type { Metadata } from "next";
import { ArrowRight } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { PublicButton } from "@/components/public-button";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "FAQ | Kalam",
  description: "Frequently asked questions about the Kalam corporate capability development platform.",
  alternates: { canonical: "/faq" },
};

const faqs = [
  ["What is Kalam?", "Kalam is a Corporate Capability Development Platform that connects business strategy, workforce capability, assessment, evidence and development."],
  ["Who is Kalam for?", "Kalam is designed for organizations that want a clearer, more measurable way to understand and improve capability."],
  ["Is Kalam an LMS?", "Kalam can support learning and development, but its purpose extends beyond learning administration to connect development with organizational capability."],
  ["What makes Kalam different?", "Kalam connects what the business needs with what people can demonstrate and what they need to develop."],
  ["Can Kalam support enterprise organizations?", "Yes. Kalam is designed for complex organizational structures, governed access and enterprise capability workflows."],
  ["Can Kalam identify capability gaps?", "Yes. Kalam connects required capability with demonstrated capability to surface gaps and prioritize action."],
  ["Does Kalam use AI?", "Kalam includes a governed AI foundation designed to support capability intelligence while keeping organizational control at the center."],
  ["How do I evaluate Kalam?", "Use a representative workforce scenario through the guided evaluation path, or speak with the Kalam team about your requirements."],
] as const;

export default function FAQPage() {
  return <CommercialShell>
    <section className={styles.hero}><div className={styles.container}><div className={styles.heroGrid}>
      <div><span className={styles.kicker}>FREQUENTLY ASKED QUESTIONS</span><h1>Clear answers. <span className={styles.heroAccent}>Confident decisions.</span></h1><p>The essential questions about Kalam, its purpose and how organizations can evaluate it.</p></div>
      <div className={styles.heroPanel}><span>THE CORE IDEA</span><h2>Connect business need with demonstrated capability.</h2><p>Then focus development where it matters.</p></div>
    </div></div></section>

    <section className={styles.section}><div className={styles.container}>
      <div className={styles.grid3}>{faqs.map(([question,answer],index) => <details className={styles.card} key={question} open={index===0}><summary><strong>{question}</strong><span>0{index+1}</span></summary><p>{answer}</p></details>)}</div>
    </div></section>

    <section className={styles.sectionAlt}><div className={styles.container}><div className={styles.heroPanel}>
      <span className={styles.kicker}>READY?</span><h2>See Kalam in context.</h2><p>Bring a real capability challenge and evaluate the platform against it.</p><div className={styles.heroActions}><PublicButton href="/guided-evaluation">Evaluate Kalam <ArrowRight size={15}/></PublicButton><PublicButton href="/contact-sales" variant="secondary">Talk to Sales</PublicButton></div>
    </div></div></section>
  </CommercialShell>;
}
