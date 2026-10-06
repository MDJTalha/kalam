import type { Metadata } from "next";
import { FileCheck2, KeyRound, LockKeyhole, ShieldCheck, Waypoints } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { getPublicCommercialCatalog } from "@/lib/public-commercial";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "Security & Trust | Kalam",
  description: "Review Kalam's enterprise security, access governance, evidence and verified certification information.",
  alternates: { canonical: "/trust" },
};

export default async function TrustPage() {
  const { certifications } = await getPublicCommercialCatalog();

  return <CommercialShell>
    <section className={styles.hero}><div className={styles.container}><div className={styles.heroGrid}>
      <div><span className={styles.kicker}><ShieldCheck size={14}/> SECURITY &amp; TRUST</span><h1>Enterprise trust requires <span className={styles.heroAccent}>verifiable foundations.</span></h1><p>Review the controls and evidence that matter when evaluating Kalam for enterprise use.</p></div>
      <div className={styles.heroPanel}><span>TRUST PRINCIPLE</span><h2>Make claims you can verify.</h2><p>Product principles, contractual commitments and formal certifications are kept distinct so buyers can evaluate each on its own evidence.</p></div>
    </div></div></section>

    <section className={styles.section}><div className={styles.container}>
      <div className={styles.sectionHead}><div><span className={styles.kicker}>ENTERPRISE REVIEW</span><h2>Four areas to validate.</h2></div><p>Focus technical and procurement review on the controls that matter to your deployment.</p></div>
      <div className={styles.grid4}>
        <article className={styles.card}><LockKeyhole size={22}/><h3>Access governance</h3><p>Tenant boundaries, roles, privileged access and administrator responsibilities.</p></article>
        <article className={styles.card}><KeyRound size={22}/><h3>Identity</h3><p>Authentication, SSO and identity-integration options for the deployment.</p></article>
        <article className={styles.card}><FileCheck2 size={22}/><h3>Traceable evidence</h3><p>Learning, assessment, credential and capability records linked to authorized activity.</p></article>
        <article className={styles.card}><Waypoints size={22}/><h3>Integration controls</h3><p>Data flows, external services and ownership boundaries reviewed during solution design.</p></article>
      </div>
    </div></section>

    <section className={styles.sectionAlt}><div className={styles.container}>
      <div className={styles.sectionHead}><div><span className={styles.kicker}>VERIFIED EVIDENCE</span><h2>Current certification information.</h2></div><p>Formal certifications are listed only when current evidence is available for verification.</p></div>
      {certifications.length ? <div className={styles.grid3}>{certifications.map(cert => <article className={styles.card} key={cert.id}><span className={styles.planBadge}>Verified record</span><h3>{cert.title}</h3><p>{cert.issuer}</p><small>{cert.registration_number ? `Registration: ${cert.registration_number}` : "Registration number not published"}{cert.expires_at ? ` · Expires ${new Date(cert.expires_at).toLocaleDateString("en-US",{year:"numeric",month:"short",day:"numeric"})}` : ""}</small>{cert.verification_url && <a className={styles.verificationLink} href={cert.verification_url} target="_blank" rel="noreferrer">Verification source</a>}</article>)}</div> : <div className={styles.empty}><strong>No formal certifications are currently listed.</strong><p>Kalam publishes certification claims only when current evidence is available for independent verification.</p></div>}
    </div></section>
  </CommercialShell>;
}
