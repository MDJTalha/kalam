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
          <p>Develop capability. Drive performance.</p>
        </div>
        <nav className={styles.footerGroup} aria-label="Platform"><strong>Platform</strong><a href={link("#platform")}>Platform</a><a href={link("#how-it-works")}>How it works</a><Link href="/guided-evaluation">Get started</Link></nav>
        <nav className={styles.footerGroup} aria-label="Solutions"><strong>Solutions</strong><a href={link("#roles")}>Executives &amp; HR</a><a href={link("#roles")}>L&amp;D &amp; Managers</a><Link href="/pricing">Pricing</Link></nav>
        <nav className={styles.footerGroup} aria-label="Enterprise"><strong>Enterprise</strong><Link href="/trust">Security &amp; trust</Link><Link href="/integrations">Integrations</Link><Link href="/implementation">Implementation</Link></nav>
        <nav className={styles.footerGroup} aria-label="Company"><strong>Company</strong><Link href="/contact-sales">Talk to Sales</Link><Link href="/login">Sign in</Link><Link href="/clients">Customer stories</Link></nav>
      </div>
      <div className={styles.footerBottom}><span>© {new Date().getFullYear()} Kalam</span></div>
    </div>
  </footer>;
}
