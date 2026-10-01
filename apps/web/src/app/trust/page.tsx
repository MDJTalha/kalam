import type { Metadata } from "next";
import { FileCheck2, KeyRound, LockKeyhole, ShieldCheck, Waypoints } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { getPublicCommercialCatalog } from "@/lib/public-commercial";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "Security & Trust",
  description: "Review Kalam security, access governance, evidence principles and verified certification information for enterprise evaluation.",
  alternates: { canonical: "/trust" },
};

export default async function TrustPage() {
  const { certifications } = await getPublicCommercialCatalog();
  return <CommercialShell>
    <section className={styles.hero}><div className={styles.container}><div className={styles.heroGrid}>
      <div><span className={styles.kicker}><ShieldCheck size={14}/> Security & trust</span><h1>Enterprise trust starts with <span className={styles.heroAccent}>verifiable controls.</span></h1><p>Review the controls, access model, data handling and service commitments that matter to enterprise adoption—with clear separation between product principles, contractual commitments and verified certifications.</p></div>
      <div className={styles.heroPanel}><span>TRUST PRINCIPLE</span><h2>Claim only what can be demonstrated.</h2><p>Kalam separates product principles from formal certification claims so enterprise buyers can distinguish implemented controls, contractual commitments and independently verified evidence.</p></div>
    </div></div></section>

    <section className={styles.section}><div className={styles.container}>
      <div className={styles.sectionHead}><div><span className={styles.kicker}>ENTERPRISE REVIEW</span><h2>Areas your technical and procurement teams should validate.</h2></div><p>We encourage structured due diligence across identity, permissions, data flows, auditability, integrations and deployment requirements.</p></div>
      <div className={styles.grid4}>
        <article className={styles.card}><LockKeyhole size={22}/><h3>Access governance</h3><p>Review tenant boundaries, role-aware permissions, privileged access and administrator responsibilities for your deployment.</p></article>
        <article className={styles.card}><KeyRound size={22}/><h3>Identity & authentication</h3><p>Confirm the authentication, SSO and identity-integration options available for your implementation before rollout.</p></article>
        <article className={styles.card}><FileCheck2 size={22}/><h3>Traceable evidence</h3><p>Learning, assessment, credential and readiness records should remain attributable to their source activity and authorized users.</p></article>
        <article className={styles.card}><Waypoints size={22}/><h3>Integration review</h3><p>Identity, people data, reporting and external-service flows are reviewed as part of deployment and security design.</p></article>
      </div>
    </div></section>

    <section className={styles.sectionAlt}><div className={styles.container}>
      <div className={styles.sectionHead}><div><span className={styles.kicker}>VERIFIED EVIDENCE</span><h2>Certification information.</h2></div><p>Formal certifications are listed here only when Kalam can provide current, verifiable evidence.</p></div>
      {certifications.length ? <div className={styles.grid3}>{certifications.map(cert => <article className={styles.card} key={cert.id}><span className={styles.planBadge}>Verified record</span><h3>{cert.title}</h3><p>{cert.issuer}</p><small>{cert.registration_number ? `Registration: ${cert.registration_number}` : "Registration number not published"}{cert.expires_at ? ` · Expires ${new Date(cert.expires_at).toLocaleDateString("en-US",{year:"numeric",month:"short",day:"numeric"})}` : ""}</small>{cert.verification_url && <a className={styles.verificationLink} href={cert.verification_url} target="_blank" rel="noreferrer">Verification source</a>}</article>)}</div> : <div className={styles.empty}><strong>No formal certifications are currently listed.</strong><p>Kalam will publish certification claims here only when current evidence is available for independent verification.</p></div>}
    </div></section>
  </CommercialShell>;
}
