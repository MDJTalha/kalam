"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowDown, ArrowRight, LogIn, Menu, X } from "lucide-react";
import { useState } from "react";
import { KalamBrand } from "./kalam-brand";
import { PublicButton } from "./public-button";
import styles from "./public-chrome.module.css";

const publicLinks = [
  {
    label: "Platform",
    anchor: "#platform",
    items: [
      ["Understand", "Strategy, capabilities and roles"],
      ["Assess", "Assessment and evidence"],
      ["Develop", "Focused development action"],
      ["Improve", "Reassessment and performance"],
    ],
  },
  {
    label: "Solutions",
    anchor: "#roles",
    items: [
      ["Executives", "Organizational capability visibility"],
      ["HR & People", "Workforce capability and readiness"],
      ["L&D", "Development aligned to business need"],
      ["Managers", "Team capability and next action"],
    ],
  },
  {
    label: "Enterprise",
    anchor: "#enterprise-readiness",
    items: [
      ["Security & Trust", "Governance and enterprise controls"],
      ["Integrations", "Identity, data and reporting"],
      ["Implementation", "A controlled path to adoption"],
    ],
  },
] as const;

export function PublicHeader({ landing = false }: { landing?: boolean }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const link = (anchor: string) => landing ? anchor : "/" + anchor;
  const routeActive = (route: string) => pathname === route;

  return <header className={styles.header}>
    <div className={styles.container}>
      <nav className={styles.nav} aria-label="Main navigation">
        <KalamBrand compact className={styles.brand}/>
        <div className={styles.links}>
          {publicLinks.map(item => <div key={item.label} className={styles.navGroup} onMouseEnter={() => setActiveMenu(item.label)} onMouseLeave={() => setActiveMenu(null)}>
            <a className={styles.navTrigger} href={link(item.anchor)} aria-haspopup="true" aria-expanded={activeMenu === item.label}>{item.label}<ArrowDown size={12} aria-hidden="true"/></a>
            {activeMenu === item.label && <div className={styles.megaMenu}>
              <div className={styles.megaIntro}>
                <span>EXPLORE KALAM</span>
                <strong>{item.label}</strong>
                <p>{item.label === "Platform" ? "One connected capability system." : item.label === "Solutions" ? "Clear capability insight for every decision-maker." : "The foundations behind enterprise adoption."}</p>
                <a href={link(item.anchor)} className={styles.megaView}>Explore {item.label} <ArrowRight size={14} aria-hidden="true"/></a>
              </div>
              <div className={styles.megaItems}>
                {item.items.map(([title, description]) => <a key={title} href={title === "Security & Trust" ? "/trust" : title === "Integrations" ? "/integrations" : title === "Implementation" ? "/implementation" : link(item.anchor)} onClick={() => setActiveMenu(null)}>
                  <span><strong>{title}</strong><small>{description}</small></span><ArrowRight size={14} aria-hidden="true"/>
                </a>)}
              </div>
            </div>}
          </div>)}
          <Link href="/pricing" aria-current={routeActive("/pricing") ? "page" : undefined}>Pricing</Link>
        </div>
        <div className={styles.actions}>
          <Link className={styles.signin} href="/login"><LogIn size={14} strokeWidth={2.2} aria-hidden="true"/><span>Sign in</span></Link>
          <PublicButton href="/guided-evaluation"><span className={styles.salesLabel}>Get started</span><ArrowRight size={15} aria-hidden="true"/></PublicButton>
        </div>
        <button className={styles.menuButton} type="button" aria-label={open ? "Close navigation menu" : "Open navigation menu"} aria-expanded={open} aria-controls="public-mobile-menu" onClick={() => setOpen(value => !value)}>
          {open ? <X size={19} aria-hidden="true"/> : <Menu size={19} aria-hidden="true"/>}
        </button>
      </nav>
      {open && <div id="public-mobile-menu" className={`${styles.mobileMenu} ${styles.mobileMenuOpen}`}>
        <nav className={styles.mobileMenuNav} aria-label="Explore Kalam">
          <span className={styles.mobileMenuLabel}>Explore Kalam</span>
          {publicLinks.map(item => <a key={item.label} href={link(item.anchor)} onClick={() => setOpen(false)}>{item.label}<ArrowRight size={14} aria-hidden="true"/></a>)}
          <Link href="/pricing" onClick={() => setOpen(false)} aria-current={routeActive("/pricing") ? "page" : undefined}>Pricing <ArrowRight size={14} aria-hidden="true"/></Link>
        </nav>
        <div className={styles.mobileMenuActions}>
          <Link href="/login" onClick={() => setOpen(false)}>Sign in</Link>
          <PublicButton href="/guided-evaluation" onClick={() => setOpen(false)}>Get started <ArrowRight size={15} /></PublicButton>
          <Link href="/contact-sales" onClick={() => setOpen(false)}>Talk to Sales <ArrowRight size={15} /></Link>
        </div>
      </div>}
    </div>
  </header>;
}
