import type { Metadata } from "next";
import { Building2, Quote } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { PublicButton } from "@/components/public-button";
import { getPublicCommercialCatalog } from "@/lib/public-commercial";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "Customer Stories | Kalam",
  description: "Approved Kalam customer references and capability stories.",
  robots: { index: false, follow: true },
};

export default async function ClientsPage() {
  const { clients } = await getPublicCommercialCatalog();

  return <CommercialShell>
    <section className={styles.hero}><div className={styles.container}><div className={styles.heroGrid}>
      <div><span className={styles.kicker}><Building2 size={14}/> CUSTOMER STORIES</span><h1>Capability becomes clearer <span className={styles.heroAccent}>when the context is real.</span></h1><p>Explore approved customer references and use cases as they become available, with each story grounded in the workforce challenge and business context.</p><div className={styles.heroActions}><PublicButton href="/contact-sales">Discuss your use case</PublicButton><PublicButton href="/pricing" variant="secondary">View pricing</PublicButton></div></div>
      <div className={styles.heroPanel}><span>REFERENCE PRINCIPLE</span><h2>Real customers. Approved context.</h2><p>Published references are shown only with approved attribution and supporting context.</p></div>
    </div></div></section>

    <section className={styles.section}><div className={styles.container}><div className={styles.sectionHead}><div><span className={styles.kicker}>CUSTOMER REFERENCES</span><h2>Approved stories and organizations.</h2></div><p>References are added as customer approvals are completed.</p></div>
      {clients.length ? <div className={styles.grid3}>{clients.map(client => <article className={`${styles.card} ${styles.clientCard}`} key={client.id}><div className={styles.clientLogo}>{client.name.slice(0,2).toUpperCase()}</div><h3>{client.name}</h3><p>{[client.industry,client.country].filter(Boolean).join(" · ") || "Approved customer reference"}</p>{client.testimonial && <blockquote><Quote size={14}/> {client.testimonial}</blockquote>}</article>)}</div> : <div className={styles.empty}><strong>Customer stories are being prepared.</strong><p>Talk with our team about the capability challenge, operating scenario and outcome most relevant to your organization.</p><div className={`${styles.heroActions} ${styles.centeredActions}`}><PublicButton href="/contact-sales">Talk to Sales</PublicButton></div></div>}
    </div></section>
  </CommercialShell>;
}
