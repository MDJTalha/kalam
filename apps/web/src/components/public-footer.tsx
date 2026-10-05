import Link from "next/link";
import { KalamBrand } from "./kalam-brand";
import styles from "./public-chrome.module.css";

export function PublicFooter() {
  return <footer className={styles.footer}>
    <div className={styles.container}>
      <div className={styles.footerGrid}>
        <div className={styles.footerBrand}>
          <KalamBrand dark compact/>
          <p>Develop capability. Drive performance.</p>
        </div>
        <nav className={styles.footerGroup} aria-label="Platform"><strong>Platform</strong><Link href="/platform">Platform</Link><Link href="/#how-it-works">How it works</Link><Link href="/get-started">Get started</Link></nav>
        <nav className={styles.footerGroup} aria-label="Solutions"><strong>Solutions</strong><Link href="/solutions">Solutions</Link><Link href="/pricing">Pricing</Link></nav>
        <nav className={styles.footerGroup} aria-label="Resources"><strong>Resources</strong><Link href="/resources">Resources</Link><Link href="/trust">Security &amp; trust</Link><Link href="/faq">FAQ</Link><Link href="/clients">Customer stories</Link></nav>
        <nav className={styles.footerGroup} aria-label="Company"><strong>Company</strong><Link href="/about">About Kalam</Link><Link href="/contact-sales">Talk to Sales</Link><Link href="/implementation">Implementation</Link><Link href="/login">Sign in</Link></nav>
      </div>
      <div className={styles.footerBottom}><span>© {new Date().getFullYear()} Kalam</span></div>
    </div>
  </footer>;
}
