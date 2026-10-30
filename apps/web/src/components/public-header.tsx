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
      ["Learning operations", "Courses, paths, programs and delivery"],
      ["Skills & capability", "Role expectations, gaps and development"],
      ["Assessments & credentials", "Verification, results and certificates"],
      ["Compliance readiness", "Requirements, evidence and exceptions"],
      ["Workforce intelligence", "Signals, reports and management action"],
    ],
  },
  {
    label: "Solutions",
    anchor: "#roles",
    items: [
      ["People leaders", "A clearer workforce capability picture"],
      ["L&D teams", "Connected learning and development operations"],
      ["Managers", "Team needs, evidence and next actions"],
      ["Compliance teams", "Requirements, status and supporting evidence"],
    ],
  },
  {
    label: "Enterprise",
    anchor: "#enterprise-readiness",
    items: [
      ["Security & Trust", "Governance, access and evidence principles"],
      ["Integrations", "Identity, people data, APIs and reporting"],
      ["Implementation", "Discovery, validation, rollout and ownership"],
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
          {publicLinks.map(item => <div
            key={item.label}
            className={styles.navGroup}
            onMouseEnter={() => setActiveMenu(item.label)}
            onMouseLeave={() => setActiveMenu(null)}
            onFocus={() => setActiveMenu(item.label)}
            onBlur={event => {
              if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setActiveMenu(null);
            }}
            onKeyDown={event => {
              if (event.key === "Escape") {
                setActiveMenu(null);
                event.currentTarget.querySelector<HTMLButtonElement>(".public-nav-trigger")?.focus();
              }
            }}
          >
            <button
              className={`${styles.navTrigger} public-nav-trigger`}
              type="button"
              aria-expanded={activeMenu === item.label}
              aria-controls={`public-menu-${item.label.toLowerCase()}`}
              onClick={() => setActiveMenu(activeMenu === item.label ? null : item.label)}
            >
              {item.label}<ArrowDown size={12} aria-hidden="true"/>
            </button>
            <div
              id={`public-menu-${item.label.toLowerCase()}`}
              className={styles.megaMenu}
              hidden={activeMenu !== item.label}
            >
              <div className={styles.megaIntro}>
                <span>EXPLORE KALAM</span>
                <strong>{item.label}</strong>
                <p>{item.label === "Platform" ? "The connected operating layer for learning, skills, evidence and workforce readiness." : item.label === "Solutions" ? "Role-relevant views that turn capability signals into accountable action." : "The controls, integrations and rollout foundations behind enterprise adoption."}</p>
                <a href={link(item.anchor)} className={styles.megaView} onClick={() => setActiveMenu(null)}>Explore {item.label} <ArrowRight size={14} aria-hidden="true"/></a>
              </div>
              <div className={styles.megaItems}>
                {item.items.map(([title, description]) => <a key={title} href={title === "Security & Trust" ? "/trust" : title === "Integrations" ? "/integrations" : title === "Implementation" ? "/implementation" : link(item.anchor)} onClick={() => setActiveMenu(null)}>
                  <span><strong>{title}</strong><small>{description}</small></span><ArrowRight size={14} aria-hidden="true"/>
                </a>)}
              </div>
            </div>
          </div>)}
          <Link href="/pricing" aria-current={routeActive("/pricing") ? "page" : undefined}>Pricing</Link>
        </div>
        <div className={styles.actions}>
          <PublicButton className={styles.guided} href="/guided-evaluation" variant="secondary">Guided evaluation</PublicButton>
          <Link className={styles.signin} href="/login"><LogIn size={14} strokeWidth={2.2} aria-hidden="true"/><span>Sign in</span></Link>
          <PublicButton href="/contact-sales"><span className={styles.salesLabel}>Contact sales</span><ArrowRight size={15} aria-hidden="true"/></PublicButton>
          <button
            className={styles.menuButton}
            type="button"
            aria-label={open ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={open}
            onClick={() => setOpen(value => !value)}
          >
            {open ? <X size={19} aria-hidden="true"/> : <Menu size={19} aria-hidden="true"/>}
          </button>
        </div>
      </nav>
      {open && <div id="public-mobile-menu" className={`${styles.mobileMenu} ${styles.mobileMenuOpen}`}>
        <nav className={styles.mobileMenuNav} aria-label="Explore Kalam">
          <span className={styles.mobileMenuLabel}>Explore Kalam</span>
          {publicLinks.map(item => <a key={item.label} href={link(item.anchor)} onClick={() => setOpen(false)}>{item.label}<ArrowRight size={14} aria-hidden="true"/></a>)}
          <Link href="/trust" onClick={() => setOpen(false)} aria-current={routeActive("/trust") ? "page" : undefined}>Security &amp; Trust <ArrowRight size={14} aria-hidden="true"/></Link>
          <Link href="/pricing" onClick={() => setOpen(false)} aria-current={routeActive("/pricing") ? "page" : undefined}>Pricing <ArrowRight size={14} aria-hidden="true"/></Link>
        </nav>
        <div className={styles.mobileMenuActions}>
          <Link href="/login" onClick={() => setOpen(false)}>Sign in</Link>
          <PublicButton href="/guided-evaluation" variant="secondary" onClick={() => setOpen(false)}>Guided evaluation</PublicButton>
          <PublicButton href="/contact-sales" onClick={() => setOpen(false)}>Contact sales <ArrowRight size={15} aria-hidden="true"/></PublicButton>
        </div>
      </div>}
    </div>
  </header>;
}
