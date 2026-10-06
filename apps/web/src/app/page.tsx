import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, BarChart3, BookOpenCheck, ChevronRight, Globe2, LockKeyhole, ShieldCheck, Target, UsersRound } from "lucide-react";
import styles from "./landing.module.css";
import { DemoInquiryForm } from "./demo-inquiry-form";
import { CapabilityCommandCenter } from "@/components/capability-command-center";
import { PublicHeader } from "@/components/public-header";
import { PublicFooter } from "@/components/public-footer";
import { PublicButton } from "@/components/public-button";

export const metadata: Metadata = {
  title: "Kalam | Corporate Capability Development Platform",
  description: "Kalam connects business strategy, workforce capability, assessment and development in one enterprise platform.",
  alternates: { canonical: "/" },
};

const capabilities = [
  { icon: Target, title: "Understand", description: "Connect strategy, capabilities, competencies and roles.", details: ["Business priorities and capability requirements", "Roles, competencies and workforce context"] },
  { icon: ShieldCheck, title: "Assess", description: "Measure demonstrated capability through assessment and evidence.", details: ["Structured assessments and outcomes", "Evidence linked to demonstrated capability"] },
  { icon: BookOpenCheck, title: "Develop", description: "Turn capability gaps into focused development action.", details: ["Learning, interventions and development plans", "Progress, execution and supporting evidence"] },
  { icon: BarChart3, title: "Improve", description: "Reassess capability and connect progress to performance.", details: ["Capability improvement and gap recalculation", "Executive insight and business impact"] },
] as const;

const journey = [
  ["01", "Strategy", "Define the capabilities the business needs."],
  ["02", "People", "Connect capability requirements to roles and workforce."],
  ["03", "Evidence", "Assess, develop and verify demonstrated capability."],
  ["04", "Performance", "Reassess progress and understand business impact."],
] as const;

const outcomes = [
  ["See capability clearly", "Build a shared view of capability requirements, evidence, gaps and progress."],
  ["Target development", "Focus development where capability gaps matter most."],
  ["Measure improvement", "Reassess capability instead of relying on activity or completion alone."],
  ["Support better decisions", "Give leaders the evidence they need to act with confidence."],
] as const;

const audiences = [
  ["EXECUTIVE LEADERS", "Make capability visible.", "See whether the organization has the capabilities required to execute strategy."],
  ["CHRO & PEOPLE", "Understand workforce readiness.", "Connect people, roles, capability and development in one operating picture."],
  ["L&D LEADERS", "Develop what matters.", "Align development investment with real organizational capability needs."],
  ["MANAGERS", "Act on team capability.", "See where people need support and what action should happen next."],
] as const;

const enterprisePaths = [
  { icon: ShieldCheck, title: "Security & Trust", description: "Review governance, access, auditability and enterprise control principles.", href: "/trust", action: "Review trust" },
  { icon: Globe2, title: "Integrations", description: "Understand how identity, people data, APIs and reporting fit your environment.", href: "/integrations", action: "Review integrations" },
  { icon: LockKeyhole, title: "Implementation", description: "See the path from business context to controlled rollout and adoption.", href: "/implementation", action: "Review implementation" },
] as const;

const questions = [
  ["What makes Kalam different?", "Kalam connects what the business needs with what people can demonstrate and what they need to develop."],
  ["Can Kalam scale with our organization?", "Kalam is designed for complex organizations, multiple structures, governed access and enterprise capability workflows."],
] as const;

export default function Home() {
  const inquiriesEnabled = process.env.MARKETING_INBOX_ENABLED === "true" && !!process.env.MARKETING_REVIEW_TENANT_SLUG;
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
  const structuredData = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Organization",
        "@id": siteUrl + "/#organization",
        name: "Kalam",
        url: siteUrl,
        logo: siteUrl + "/kalam-logo.svg",
        description: "Corporate Capability Development Platform connecting strategy, workforce capability, assessment and development.",
      },
      {
        "@type": "SoftwareApplication",
        "@id": siteUrl + "/#software",
        name: "Kalam",
        applicationCategory: "BusinessApplication",
        operatingSystem: "Web",
        url: siteUrl,
        description: "Enterprise platform for corporate capability development, assessment, evidence and workforce performance.",
        publisher: { "@id": siteUrl + "/#organization" },
      },
    ],
  };

  return <div className={styles.page}>
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }} />
    <a className={styles.skip} href="#main">Skip to content</a>
    <PublicHeader />

    <main id="main">
      <section className={styles.hero} aria-labelledby="hero-title">
        <div className={styles.container}>
          <div className={styles.heroGrid}>
            <div className={styles.heroCopy}>
              <div className={styles.eyebrow}><span /> CORPORATE CAPABILITY DEVELOPMENT PLATFORM</div>
              <h1 id="hero-title"><span>Develop Capability.</span><em>Drive Performance.</em></h1>
              <p>Kalam connects business strategy, workforce capability, assessment and development in one intelligent enterprise platform.</p>
              <div className={styles.heroActions}>
                <PublicButton href="/get-started">Get started <ArrowRight size={17} /></PublicButton>
                <PublicButton href="/contact-sales" variant="secondary">Talk to Sales <ChevronRight size={16} /></PublicButton>
              </div>
              <div className={styles.heroNote}><ShieldCheck size={18} /> Built for organizations that want capability, development and performance connected.</div>
            </div>
            <CapabilityCommandCenter />
          </div>
          <div className={styles.heroRail}>
            <strong>THE KALAM CAPABILITY LIFECYCLE</strong>
            <span>Strategy <ChevronRight size={14} /> Capability <ChevronRight size={14} /> Assess <ChevronRight size={14} /> Develop <ChevronRight size={14} /> Reassess <ChevronRight size={14} /> Perform</span>
          </div>
        </div>
      </section>

      <section className={styles.signalBand} aria-label="The capability challenge">
        <div className={styles.container}>
          <div className={styles.problemIntro}>
            <span>THE BUSINESS CHALLENGE</span>
            <h2>Capability gaps become business gaps.</h2>
            <p>Organizations need to know what capabilities matter, where gaps exist, what to develop and whether development is making a difference.</p>
          </div>
        </div>
        <div className={styles.container}>
          <div className={styles.signalGrid}>
            <article><Target size={20} /><span><strong>Know what matters</strong><small>Connect strategy to capability requirements.</small></span></article>
            <article><UsersRound size={20} /><span><strong>Know where you stand</strong><small>See workforce capability and demonstrated evidence.</small></span></article>
            <article><ShieldCheck size={20} /><span><strong>Know what to develop</strong><small>Turn capability gaps into focused action.</small></span></article>
            <article><BarChart3 size={20} /><span><strong>Know whether it worked</strong><small>Reassess progress and understand impact.</small></span></article>
          </div>
        </div>
      </section>

      <section id="platform" className={styles.section} aria-labelledby="platform-title">
        <div className={styles.container}>
          <div className={styles.sectionHead}>
            <div><span>THE PLATFORM</span><h2 id="platform-title">One connected<br /><em>capability system.</em></h2></div>
            <p>Understand the business need, assess demonstrated capability, develop targeted action and measure improvement.</p>
          </div>
          <div className={styles.capabilityGrid}>
            {capabilities.map(({ icon: Icon, title, description, details }, index) => <details className={styles.capabilityCard} key={title}>
              <summary>
                <span className={styles.cardTop}><span className={styles.cardIcon}><Icon size={21} /></span><span className={styles.cardNumber}>0{index + 1}</span></span>
                <strong>{title}</strong><p>{description}</p><span className={styles.cardAction}>Explore capability <ChevronRight size={15} /></span>
              </summary>
              <div className={styles.cardDetail}><b>In the workspace</b><ul>{details.map(item => <li key={item}>{item}</li>)}</ul></div>
            </details>)}
          </div>
        </div>
      </section>

      <section id="difference" className={`${styles.section} ${styles.differenceSection}`} aria-labelledby="difference-title">
        <div className={styles.container}>
          <div className={styles.sectionHead}>
            <div><span>WHY KALAM</span><h2 id="difference-title">Connect what the business needs<br /><em>with what people can demonstrate.</em></h2></div>
            <p>Kalam adds the capability layer between business priorities, people data and development—so organizations can make better decisions about readiness and growth.</p>
          </div>
          <div className={styles.differenceGrid}>
            <article><span>BUSINESS</span><h3>What capability is required?</h3><p>Translate strategic priorities into capabilities, competencies and role expectations.</p></article>
            <article><span>KALAM</span><h3>What can people demonstrate?</h3><p>Connect assessment and evidence to a clearer picture of demonstrated capability.</p></article>
            <article><span>DEVELOPMENT</span><h3>What should happen next?</h3><p>Focus development on real gaps and reassess progress over time.</p></article>
          </div>
        </div>
      </section>

      <section id="how-it-works" className={`${styles.section} ${styles.sectionTint}`} aria-labelledby="journey-title">
        <div className={styles.container}>
          <div className={styles.sectionHead}>
            <div><span>HOW KALAM WORKS</span><h2 id="journey-title">From business need<br /><em>to performance.</em></h2></div>
            <p>A simple capability lifecycle connects strategy, people, evidence, development and improvement.</p>
          </div>
          <div className={styles.journeyGrid}>{journey.map(([number, title, description]) => <article key={number}><span>{number}</span><h3>{title}</h3><p>{description}</p></article>)}</div>
        </div>
      </section>

      <section id="outcomes" className={`${styles.section} ${styles.outcomesSection}`} aria-labelledby="outcomes-title">
        <div className={styles.container}>
          <div className={styles.sectionHead}>
            <div><span>BUSINESS OUTCOMES</span><h2 id="outcomes-title">Capability that leads<br /><em>to better decisions.</em></h2></div>
            <p>Kalam is designed to make capability visible, actionable and measurable.</p>
          </div>
          <div className={styles.outcomeGrid}>{outcomes.map(([title, description], index) => <article key={title}><span>0{index + 1}</span><h3>{title}</h3><p>{description}</p></article>)}</div>
        </div>
      </section>

      <section id="roles" className={`${styles.section} ${styles.rolesSection}`} aria-labelledby="roles-title">
        <div className={styles.container}>
          <div className={styles.sectionHead}>
            <div><span>FOR LEADERS</span><h2 id="roles-title">One view of capability.<br /><em>Different decisions for every role.</em></h2></div>
            <p>Give each stakeholder the insight they need without creating another disconnected system.</p>
          </div>
          <div className={styles.roleGrid}>{audiences.map(([label, title, description]) => <article key={label}><span>{label}</span><h3>{title}</h3><p>{description}</p></article>)}</div>
        </div>
      </section>

      <section id="enterprise-readiness" className={`${styles.section} ${styles.enterpriseSection}`} aria-labelledby="enterprise-title">
        <div className={styles.container}>
          <div className={styles.sectionHead}>
            <div><span>ENTERPRISE READY</span><h2 id="enterprise-title">Built for organizations<br /><em>that take capability seriously.</em></h2></div>
            <p>Review the foundations that matter before enterprise adoption: trust, integration and implementation.</p>
          </div>
          <div className={styles.enterpriseGrid}>{enterprisePaths.map(({ icon: Icon, title, description, href, action }) => <article key={title}><Icon size={23} /><h3>{title}</h3><p>{description}</p><Link href={href}>{action} <ArrowRight size={15} /></Link></article>)}</div>
        </div>
      </section>

      <section id="questions" className={styles.section} aria-labelledby="questions-title">
        <div className={styles.container}><div className={styles.questionLayout}>
          <div className={styles.questionIntro}><span className={styles.kicker}>FREQUENT QUESTIONS</span><h2 id="questions-title">Clear answers.<br /><em>Confident decisions.</em></h2><p>Start with the questions that matter before you evaluate Kalam.</p></div>
          <div className={styles.questionList}>
            {questions.map(([question, answer], index) => <details key={question} open={index === 0}>
              <summary><span className={styles.questionSummary}><b>0{index + 1}</b><span>{question}</span></span><ChevronRight size={18} /></summary>
              <div className={styles.questionAnswer}><span className={styles.answerMark}><ShieldCheck size={16} /></span><p>{answer}</p></div>
            </details>)}
            <Link className={styles.questionCta} href="/guided-evaluation"><span><b>Ready to evaluate Kalam?</b><small>Bring a representative workforce scenario.</small></span><ArrowRight size={18} /></Link>
          </div>
        </div></div>
      </section>

      {inquiriesEnabled && <section id="demo" className={`${styles.section} ${styles.demoSection}`} aria-labelledby="demo-title">
        <div className={styles.container}><div className={styles.demoGrid}><div className={styles.demoIntro}>
          <div className={styles.demoIntroTop}><span className={styles.kicker}>LET&apos;S TALK</span><span className={styles.demoBadge}>01 / CONVERSATION</span></div>
          <h2 id="demo-title">Start with your<br /><em>business priority.</em></h2>
          <p>Tell us what capability challenge your organization is trying to solve and we&apos;ll start with the context that matters.</p>
          <div className={styles.demoSignals}><div><span><Target size={16} /></span><section><b>Define the priority</b><small>Start with the outcome that matters.</small></section></div><div><span><UsersRound size={16} /></span><section><b>Bring the context</b><small>We&apos;ll prepare around your organization.</small></section></div><div><span><ArrowRight size={16} /></span><section><b>Choose the next step</b><small>Move from discussion to action.</small></section></div></div>
        </div><DemoInquiryForm /></div></div>
      </section>}

      {!inquiriesEnabled && <section className={styles.closing} aria-labelledby="closing-title">
        <div className={styles.container}><div className={styles.closingInner}>
          <div><span>THE NEXT STEP</span><h2 id="closing-title">Build the capabilities<br />your business needs.</h2><p>See how Kalam connects strategy, people, capability and development.</p></div>
          <div><PublicButton href="/get-started">Get started <ArrowRight size={17} /></PublicButton><Link href="/contact-sales">Talk to Sales <ChevronRight size={15} /></Link></div>
        </div></div>
      </section>}
    </main>

    <PublicFooter />
  </div>;
}
