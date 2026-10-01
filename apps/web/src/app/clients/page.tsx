import type { Metadata } from "next";
import { Building2, Quote } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { PublicButton } from "@/components/public-button";
import { getPublicCommercialCatalog } from "@/lib/public-commercial";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "Customer Stories",
  description: "Approved Kalam customer references and customer stories.",
  robots: { index: false, follow: true },
};

export default async function ClientsPage() {
  const { clients } = await getPublicCommercialCatalog();
  return <CommercialShell>
    <section className={styles.hero}><div className={styles.container}><div className={styles.heroGrid}>
      <div><span className={styles.kicker}><Building2 size={14}/> Customer stories</span><h1>See how organizations use Kalam to build <span className={styles.heroAccent}>workforce capability.</span></h1><p>Explore approved customer references and use cases as they become available. Each story focuses on the workforce challenge, Kalam workflow and business context behind the deployment.</p><div className={styles.heroActions}><PublicButton href="/contact-sales">Discuss your use case</PublicButton><PublicButton href="/pricing" variant="secondary">Explore pricing</PublicButton></div></div>
      <div className={styles.heroPanel}><span>REFERENCE PRINCIPLE</span><h2>Real customers. Approved stories. Verifiable context.</h2><p>Customer references are presented with approved attribution and context so evaluation teams can distinguish published evidence from marketing language.</p></div>
    </div></div></section>
    <section className={styles.section}><div className={styles.container}><div className={styles.sectionHead}><div><span className={styles.kicker}>CUSTOMER REFERENCES</span><h2>Approved organizations and stories.</h2></div><p>References are added as customer approvals are completed.</p></div>
      {clients.length ? <div className={styles.grid3}>{clients.map(client => <article className={`${styles.card} ${styles.clientCard}`} key={client.id}><div className={styles.clientLogo}>{client.name.slice(0,2).toUpperCase()}</div><h3>{client.name}</h3><p>{[client.industry,client.country].filter(Boolean).join(" · ") || "Approved customer reference"}</p>{client.testimonial && <blockquote><Quote size={14}/> {client.testimonial}</blockquote>}</article>)}</div> : <div className={styles.empty}><strong>Customer stories are being prepared for publication.</strong><p>In the meantime, talk with our team about the operating scenarios, deployment requirements and outcomes most relevant to your organization.</p><div className={`${styles.heroActions} ${styles.centeredActions}`}><PublicButton href="/contact-sales">Contact sales</PublicButton></div></div>}
    </div></section>
  </CommercialShell>;
}
