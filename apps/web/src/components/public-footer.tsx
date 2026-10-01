import Link from "next/link";
import { KalamBrand } from "./kalam-brand";
import styles from "./public-chrome.module.css";

export function PublicFooter({ landing = false }: { landing?: boolean }) {
  const link = (anchor: string) => landing ? anchor : "/" + anchor;
  return <footer className={styles.footer}>
    <div className={styles.container}>
      <div className={styles.footerGrid}>
        <div className={styles.footerBrand}>
          <KalamBrand dark compact/>
          <p>Built for better workforce decisions.</p>
        </div>
        <nav className={styles.footerGroup} aria-label="Platform"><strong>Platform</strong><a href={link("#platform")}>Capabilities</a><a href={link("#how-it-works")}>How it works</a><Link href="/integrations">Integrations</Link><Link href="/implementation">Implementation</Link></nav>
        <nav className={styles.footerGroup} aria-label="Evaluate"><strong>Evaluate</strong><Link href="/pricing">Pricing</Link><Link href="/guided-evaluation">Guided evaluation</Link><Link href="/contact-sales">Contact sales</Link><Link href="/clients">Customer stories</Link></nav>
        <nav className={styles.footerGroup} aria-label="Trust and access"><strong>Trust &amp; access</strong><Link href="/trust">Security &amp; trust</Link><a href={link("#enterprise-readiness")}>Enterprise readiness</a><Link href="/login">Sign in</Link></nav>
      </div>
      <div className={styles.footerBottom}><span>© {new Date().getFullYear()} Kalam</span></div>
    </div>
  </footer>;
}
