import type { Metadata } from "next";
import Link from "next/link";
import { ArrowDownRight, ArrowRight, Award, BarChart3, BookOpenCheck, CheckCircle2, ChevronRight, ClipboardCheck, FileCheck2, Globe2, Layers3, LockKeyhole, ShieldCheck, Sparkles, Target, UsersRound } from "lucide-react";
import styles from "./landing.module.css";
import { DemoInquiryForm } from "./demo-inquiry-form";

export const metadata: Metadata = {
  title: "Kognivon | Enterprise Workforce Capability Platform",
  description: "Kognivon is an Enterprise Workforce Capability Platform connecting learning, skills, compliance, development and workforce readiness in one role-aware SaaS workspace.",
};

const capabilities = [
  { icon: BookOpenCheck, title: "Learning operations", description: "Create, assign and manage learning with the delivery work visible.", details: ["Courses, learning paths and programs", "Assignments, progress and session delivery"] },
  { icon: Layers3, title: "Skills and capability", description: "Connect role expectations to development priorities.", details: ["Skill and role mappings", "Gaps, plans and development actions"] },
  { icon: ShieldCheck, title: "Compliance readiness", description: "See requirements and the records behind their status.", details: ["Assignments, due dates and exceptions", "Evidence and escalation context"] },
  { icon: ClipboardCheck, title: "Assessments", description: "Check understanding as part of the learning journey.", details: ["Question banks and attempts", "Pass rules and recorded results"] },
  { icon: Award, title: "Credentials", description: "Keep issued credentials connected to learning history.", details: ["Certificates and expiry tracking", "Verification and revocation records"] },
  { icon: BarChart3, title: "Decision support", description: "Turn participation and capability signals into next actions.", details: ["Manager and executive views", "Reports, filters and export workflows"] },
] as const;

const audiences = [
  { label: "PEOPLE LEADERS", title: "Understand the capability picture.", description: "Bring development, skills and compliance signals into leadership decisions without losing the underlying context." },
  { label: "L&D TEAMS", title: "Keep delivery moving.", description: "Work across authoring, assignments, programs and operational queues from the same platform." },
  { label: "MANAGERS", title: "Know who needs support.", description: "See team learning and skill needs, then connect people to relevant development actions." },
  { label: "COMPLIANCE TEAMS", title: "Follow the evidence.", description: "Review requirements, status and exceptions with a clearer path back to recorded activity." },
] as const;

const steps = [
  { number: "01", title: "Define the expectation", description: "Bring roles, skills and learning requirements into a shared operating picture." },
  { number: "02", title: "Move learning forward", description: "Assign the right experience and keep learners, managers and L&D aligned." },
  { number: "03", title: "Check and record", description: "Connect assessments, credentials and compliance records to the activity." },
  { number: "04", title: "Act on the evidence", description: "See what is complete, what needs attention and where to develop next." },
] as const;

export default function Home() {
  const inquiriesEnabled = process.env.MARKETING_INBOX_ENABLED === "true" && !!process.env.MARKETING_REVIEW_TENANT_SLUG;
  return (
    <div className={styles.page}>
      <a className={styles.skip} href="#main">Skip to content</a>
      <header className={styles.header}>
        <div className={styles.container}>
          <nav className={styles.nav} aria-label="Main navigation">
            <Link className={styles.brand} href="/" aria-label="Kognivon home">
              <span className={styles.brandMark} aria-hidden="true"><span>K</span></span>
              <span>Kognivon<span className={styles.brandPeriod}>.</span></span>
            </Link>
            <div className={styles.navLinks}>
              <a href="#platform">Platform</a><a href="#workflow">How it works</a><a href="#roles">For teams</a><a href="#enterprise">Enterprise</a>
            </div>
            <div className={styles.navActions}>
              <Link className={styles.signin} href="/login">Sign in</Link>
              <a className={styles.navCta} href={inquiriesEnabled ? "#demo" : "#workflow"}>{inquiriesEnabled ? "Request a demo" : "See the workflow"} <ArrowRight size={16} aria-hidden="true" /></a>
            </div>
          </nav>
          <nav className={styles.mobileNav} aria-label="Explore the landing page"><a href="#platform">Platform</a>{inquiriesEnabled && <a href="#demo">Request a demo</a>}<a href="#workflow">Workflow</a><a href="#roles">For teams</a><a href="#enterprise">Enterprise</a><a href="#questions">Questions</a></nav>
        </div>
      </header>

      <main id="main">
        <section className={styles.hero} aria-labelledby="hero-title">
          <div className={styles.container}>
            <div className={styles.heroGrid}>
              <div className={styles.heroCopy}>
                <div className={styles.eyebrow}><span className={styles.eyebrowLine} /> ENTERPRISE WORKFORCE CAPABILITY PLATFORM</div>
                <h1 id="hero-title">Build workforce capability. <span>Prove readiness. Move the enterprise forward.</span></h1>
                <p className={styles.heroLead}>Kognivon is an Enterprise Workforce Capability Platform that connects learning, skills, compliance, assessments and development in one role-aware SaaS workspace. Give every stakeholder a clear line of sight from role expectations to evidence and the next decision.</p>
                <div className={styles.heroActions}>
                  <a className={styles.primaryButton} href={inquiriesEnabled ? "#demo" : "#platform"}>{inquiriesEnabled ? "Request a demo" : "Explore the platform"} <ArrowRight size={18} aria-hidden="true" /></a>
                  <a className={styles.secondaryButton} href="#workflow">See how it works <ArrowDownRight size={17} aria-hidden="true" /></a>
                </div>
                <div className={styles.heroFootnote}><ShieldCheck size={18} aria-hidden="true" /> Role-aware workspaces. Governed workflows. Connected evidence.</div>
              </div>
              <div className={styles.heroVisual} aria-label="Illustrative Kognivon workspace preview">
                <div className={styles.previewTop}><div className={styles.previewIdentity}><span className={styles.previewLogo}>K</span><span>Kognivon <small>WORKSPACE PREVIEW</small></span></div><span className={styles.previewSample}>ILLUSTRATIVE VIEW</span></div>
                <div className={styles.previewBody}>
                  <div className={styles.previewHeading}><div><span className={styles.previewOverline}>WORKFORCE INTELLIGENCE</span><strong>Capability overview</strong><span>A connected view of learning and readiness</span></div><span className={styles.previewAvatar} aria-hidden="true">KT</span></div>
                  <div className={styles.previewMetrics}>
                    <div><span><UsersRound size={15} aria-hidden="true" /> People</span><strong>Role context</strong><small>Understand who needs what</small></div>
                    <div><span><Target size={15} aria-hidden="true" /> Skills</span><strong>Capability gaps</strong><small>Prioritize development</small></div>
                    <div><span><ShieldCheck size={15} aria-hidden="true" /> Compliance</span><strong>Evidence status</strong><small>See what requires action</small></div>
                  </div>
                  <div className={styles.previewLower}>
                    <div className={styles.previewPanel}><div className={styles.previewPanelHead}><strong>From requirement to readiness</strong><span>CONNECTED WORKFLOW</span></div><div className={styles.previewTrack}><span><CheckCircle2 size={15} /> Define</span><i /><span><BookOpenCheck size={15} /> Learn</span><i /><span><ClipboardCheck size={15} /> Assess</span><i /><span><FileCheck2 size={15} /> Evidence</span></div><div className={styles.previewBars}><span style={{ width: "86%" }} /><span style={{ width: "66%" }} /><span style={{ width: "76%" }} /></div></div>
                    <div className={styles.previewAside}><span className={styles.previewAsideIcon}><Sparkles size={20} /></span><strong>Clearer next actions</strong><small>Bring signals and work into the same view.</small></div>
                  </div>
                </div>
                <div className={styles.previewGlow} aria-hidden="true" />
              </div>
            </div>
            <div className={styles.heroBottom}><span>ONE CONNECTED SYSTEM</span><span>Learning <ChevronRight size={15} /> Skills <ChevronRight size={15} /> Compliance <ChevronRight size={15} /> Evidence</span></div>
          </div>
        </section>

        <section className={styles.introBand} aria-label="Product proposition"><div className={styles.container}><span>THE CATEGORY</span><p>Kognivon goes beyond a stand-alone LMS. It brings learning delivery, capability planning, assessments and compliance evidence into one enterprise operating picture of <strong>what your workforce needs</strong>, <strong>how readiness is changing</strong> and <strong>what comes next.</strong></p></div></section>

        <section className={styles.enterpriseSignals} aria-label="Enterprise SaaS principles"><div className={styles.container}><div className={styles.signalGrid}>
          <div><ShieldCheck size={21} aria-hidden="true" /><span><strong>Governed by design</strong><small>Permissions, evidence and accountability stay close to the work.</small></span></div>
          <div><UsersRound size={21} aria-hidden="true" /><span><strong>Built around roles</strong><small>Learners, managers, L&D and compliance teams see what matters to them.</small></span></div>
          <div><Globe2 size={21} aria-hidden="true" /><span><strong>Ready for distributed organizations</strong><small>Organize capability work across teams, business units and locations.</small></span></div>
          <div><FileCheck2 size={21} aria-hidden="true" /><span><strong>Evidence connected</strong><small>Keep learning, assessment, credentials and readiness context together.</small></span></div>
        </div></div></section>

        <section id="platform" className={styles.section} aria-labelledby="platform-title">
          <div className={styles.container}>
            <div className={styles.sectionHead}><div><span className={styles.kicker}>THE PLATFORM</span><h2 id="platform-title">One platform for capability,<br /><em>from plan to proof.</em></h2></div><p>Connect the tools and records behind development, verification and action. Each team gets a relevant view of the same capability journey.</p></div>
            <div className={styles.capabilityGrid}>{capabilities.map(({ icon: Icon, title, description, details }, index) => <details className={styles.capabilityCard} key={title}><summary><span className={styles.cardTop}><span className={styles.cardIcon}><Icon size={22} strokeWidth={1.8} aria-hidden="true" /></span><span className={styles.cardNumber}>0{index + 1}</span></span><span className={styles.cardTitle}>{title}</span><span className={styles.cardDescription}>{description}</span><span className={styles.cardAction}>Explore capability <ChevronRight size={16} aria-hidden="true" /></span></summary><div className={styles.cardDetail}><strong>In the workspace</strong><ul>{details.map(detail => <li key={detail}>{detail}</li>)}</ul></div></details>)}</div>
          </div>
        </section>

        <section id="workflow" className={styles.workflow} aria-labelledby="workflow-title"><div className={styles.container}>
          <div className={styles.sectionHead}><div><span className={styles.kicker}>HOW IT WORKS</span><h2 id="workflow-title">A line of sight from<br /><em>expectation to evidence.</em></h2></div><p>Capability is easier to manage when the steps between a requirement and its proof are visible.</p></div>
          <div className={styles.steps}>{steps.map(step => <div className={styles.step} key={step.number}><span>{step.number}</span><div><h3>{step.title}</h3><p>{step.description}</p></div></div>)}</div>
        </div></section>

        <section id="roles" className={styles.roles} aria-labelledby="roles-title"><div className={styles.container}>
          <div className={styles.sectionHead}><div><span className={styles.kicker}>ONE SYSTEM, MANY DECISIONS</span><h2 id="roles-title">Clarity for every team<br /><em>moving people forward.</em></h2></div><p>The same learning record should answer different questions for the people responsible for workforce capability.</p></div>
          <div className={styles.rolesGrid}>{audiences.map(audience => <article className={styles.roleCard} key={audience.label}><span>{audience.label}</span><h3>{audience.title}</h3><p>{audience.description}</p></article>)}</div>
        </div></section>

        <section id="enterprise" className={styles.enterprise} aria-labelledby="enterprise-title"><div className={styles.container}><div className={styles.enterpriseGrid}>
          <div><span className={styles.kicker}>ENTERPRISE CONTROL WITHOUT ENTERPRISE FRICTION</span><h2 id="enterprise-title">Make capability visible, governable and easier to move forward.</h2><p>Give learning teams, managers, compliance owners and leaders relevant views of the same work. Kognivon connects requirements, delivery and evidence so decisions can be traced back to the underlying records without forcing every team into the same workflow.</p><a href="#platform" className={styles.textLink}>Explore the capability system <ArrowRight size={17} aria-hidden="true" /></a></div>
          <div className={styles.enterpriseList}>
            <div><LockKeyhole size={23} aria-hidden="true" /><span><strong>Role-aware workspaces</strong><small>Keep actions and information relevant to the person using them.</small></span></div>
            <div><FileCheck2 size={23} aria-hidden="true" /><span><strong>Evidence in context</strong><small>Connect learning activity to assessments, credentials and compliance records.</small></span></div>
            <div><Globe2 size={23} aria-hidden="true" /><span><strong>Organizational context across teams</strong><small>Organize people, roles and learning work across business units and locations.</small></span></div>
          </div>
        </div></div></section>

        <section id="questions" className={styles.questions} aria-labelledby="questions-title"><div className={styles.container}><div className={styles.questionsGrid}>
          <div><span className={styles.kicker}>EVALUATING KOGNIVON</span><h2 id="questions-title">The right questions<br />deserve clear answers.</h2><p>Use these questions to examine the product against your workflows. Security, integration and deployment requirements should be scoped with your team before a rollout is agreed.</p></div>
          <div className={styles.questionList}>
            <details><summary>What can we review in a walkthrough?<ChevronRight size={19} aria-hidden="true" /></summary><p>Follow a real workflow from role and learning requirements through assignments, assessments, credentials, compliance records and reporting. The preview above is illustrative; a walkthrough should use the current product.</p></details>
            <details><summary>How should we interpret a readiness signal?<ChevronRight size={19} aria-hidden="true" /></summary><p>Use it to find records that need review. A signal is context for a human decision, not an independent certification of competence or regulatory compliance.</p></details>
            <details><summary>Can different teams work from relevant views?<ChevronRight size={19} aria-hidden="true" /></summary><p>Kognivon includes role-aware learner, manager and administrative workspaces. Specific permissions and organizational scope should be verified as part of an enterprise evaluation.</p></details>
            <details><summary>How would Kognivon fit our existing systems?<ChevronRight size={19} aria-hidden="true" /></summary><p>Review required identity, HR, content and reporting data flows with your team. The platform has integration and reporting workspaces; each connector and service commitment needs a scoped technical review.</p></details>
            <details><summary>What would an enterprise rollout involve?<ChevronRight size={19} aria-hidden="true" /></summary><p>Start with your organizational structure, user roles, learning records, required integrations and security review. The configuration, migration and service scope should be confirmed together before a deployment commitment.</p></details>
          </div>
        </div></div></section>

        {inquiriesEnabled && <section id="demo" className={styles.demoSection} aria-labelledby="demo-title"><div className={styles.container}><div className={styles.demoGrid}><div><span className={styles.kicker}>LET&apos;S TALK</span><h2 id="demo-title">Explore Kognivon with your team.</h2><p>Tell us what your organization needs to understand about learning, skills and readiness. We&apos;ll use your details to respond to your request.</p></div><DemoInquiryForm /></div></div></section>}

        <section className={styles.closing} aria-labelledby="closing-title"><div className={styles.container}><div className={styles.closingInner}><div><span className={styles.kicker}>THE NEXT STEP</span><h2 id="closing-title">See the whole picture.<br />Move people forward.</h2><p>{inquiriesEnabled ? "Request a conversation about your needs, or enter your workspace when you have access." : "Review the connected workflow, then enter your workspace when you have access."}</p></div><div className={styles.closingActions}><a className={styles.lightButton} href={inquiriesEnabled ? "#demo" : "#questions"}>{inquiriesEnabled ? "Request a conversation" : "Review evaluation questions"} <ArrowRight size={18} aria-hidden="true" /></a><Link href="/login">Already have access? Sign in <ChevronRight size={16} aria-hidden="true" /></Link></div></div></div></section>
      </main>
      <footer className={styles.footer}><div className={styles.container}><div className={styles.footerTop}><Link className={styles.brand} href="/" aria-label="Kognivon home"><span className={styles.brandMark} aria-hidden="true"><span>K</span></span><span>Kognivon<span className={styles.brandPeriod}>.</span></span></Link><p>Enterprise workforce capability, delivered through one connected SaaS workspace.</p><div><a href="#platform">Platform</a><a href="#workflow">Workflow</a><a href="#roles">For teams</a><a href="#questions">Questions</a>{inquiriesEnabled && <a href="#demo">Request a demo</a>}<Link href="/login">Sign in</Link></div></div><div className={styles.footerBottom}><span>© {new Date().getFullYear()} Kognivon</span><span>Workforce capability, with clarity.</span></div></div></footer>
    </div>
  );
}
