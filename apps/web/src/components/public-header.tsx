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
    href: "/platform",
    items: [
      ["Understand", "Strategy, capabilities and roles"],
      ["Assess", "Assessment and evidence"],
      ["Develop", "Focused development action"],
      ["Improve", "Reassessment and performance"],
    ],
  },
  {
    label: "Solutions",
    href: "/solutions",
    items: [
      ["Executives", "Organizational capability visibility"],
      ["HR & People", "Workforce capability and readiness"],
      ["L&D", "Development aligned to business need"],
      ["Managers", "Team capability and next action"],
    ],
  },
  {
    label: "Resources",
    href: "/resources",
    items: [
      ["Security & Trust", "Governance and enterprise controls"],
      ["Customer Stories", "Approved references and use cases"],
      ["FAQ", "Clear answers for evaluation"],
      ["Implementation", "A controlled path to adoption"],
    ],
  },
] as const;

const resourceLinks: Record<string, string> = {
  "Security & Trust": "/trust",
  "Customer Stories": "/clients",
  "FAQ": "/faq",
  "Implementation": "/implementation",
};

export function PublicHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const routeActive = (route: string) => pathname === route;

  return <header className={styles.header}>
    <div className={styles.container}>
      <nav className={styles.nav} aria-label="Main navigation">
        <KalamBrand compact className={styles.brand}/>
        <div className={styles.links}>
          {publicLinks.map(item => <div key={item.label} className={styles.navGroup} onMouseEnter={() => setActiveMenu(item.label)} onMouseLeave={() => setActiveMenu(null)}>
            <Link className={styles.navTrigger} href={item.href} aria-haspopup="true" aria-expanded={activeMenu === item.label}>{item.label}<ArrowDown size={12} aria-hidden="true"/></Link>
            {activeMenu === item.label && <div className={styles.megaMenu}>
              <div className={styles.megaIntro}>
                <span>EXPLORE KALAM</span>
                <strong>{item.label}</strong>
                <p>{item.label === "Platform" ? "One connected capability system." : item.label === "Solutions" ? "Clear capability insight for every decision-maker." : "Ideas, evidence and enterprise guidance."}</p>
                <Link href={item.href} className={styles.megaView} onClick={() => setActiveMenu(null)}>Explore {item.label} <ArrowRight size={14} aria-hidden="true"/></Link>
              </div>
              <div className={styles.megaItems}>
                {item.items.map(([title, description]) => {
                  const href = resourceLinks[title] || item.href;
                  return <Link key={title} href={href} onClick={() => setActiveMenu(null)}>
                    <span><strong>{title}</strong><small>{description}</small></span><ArrowRight size={14} aria-hidden="true"/>
                  </Link>;
                })}
              </div>
            </div>}
          </div>)}
          <Link href="/pricing" aria-current={routeActive("/pricing") ? "page" : undefined}>Pricing</Link>
        </div>
        <div className={styles.actions}>
          <Link className={styles.signin} href="/login"><LogIn size={14} strokeWidth={2.2} aria-hidden="true"/><span>Sign in</span></Link>
          <PublicButton href="/get-started"><span className={styles.salesLabel}>Get started</span><ArrowRight size={15} aria-hidden="true"/></PublicButton>
        </div>
        <button className={styles.menuButton} type="button" aria-label={open ? "Close navigation menu" : "Open navigation menu"} aria-expanded={open} aria-controls="public-mobile-menu" onClick={() => setOpen(value => !value)}>
          {open ? <X size={19} aria-hidden="true"/> : <Menu size={19} aria-hidden="true"/>}
        </button>
      </nav>
      {open && <div id="public-mobile-menu" className={`${styles.mobileMenu} ${styles.mobileMenuOpen}`}>
        <nav className={styles.mobileMenuNav} aria-label="Explore Kalam">
          <span className={styles.mobileMenuLabel}>Explore Kalam</span>
          {publicLinks.map(item => <Link key={item.label} href={item.href} onClick={() => setOpen(false)}>{item.label}<ArrowRight size={14} aria-hidden="true"/></Link>)}
          <Link href="/pricing" onClick={() => setOpen(false)} aria-current={routeActive("/pricing") ? "page" : undefined}>Pricing <ArrowRight size={14} aria-hidden="true"/></Link>
        </nav>
        <div className={styles.mobileMenuActions}>
          <Link href="/login" onClick={() => setOpen(false)}>Sign in</Link>
          <PublicButton href="/get-started" onClick={() => setOpen(false)}>Get started <ArrowRight size={15} /></PublicButton>
          <Link href="/contact-sales" onClick={() => setOpen(false)}>Talk to Sales <ArrowRight size={15} /></Link>
        </div>
      </div>}
    </div>
  </header>;
}
