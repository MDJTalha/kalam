import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Award, BarChart3, BookOpenCheck, ChevronRight, ClipboardCheck, FileCheck2, Globe2, LockKeyhole, ShieldCheck, Target, UsersRound } from "lucide-react";
import styles from "./landing.module.css";
import { DemoInquiryForm } from "./demo-inquiry-form";
import { CapabilityCommandCenter } from "@/components/capability-command-center";
import { PublicHeader } from "@/components/public-header";
import { PublicFooter } from "@/components/public-footer";
import { PublicButton } from "@/components/public-button";

export const metadata: Metadata = {
  title: "Kalam | Enterprise Workforce Capability Platform",
  description: "Kalam turns workforce capability into business readiness by connecting roles, skills, learning, assessment, evidence, compliance and action.",
  alternates: { canonical: "/" },
};

const capabilities = [
  { icon: BookOpenCheck, title: "Learning operations", description: "Create, assign and manage structured development with delivery work visible.", details: ["Courses, learning paths and programs", "Assignments, progress and delivery"] },
  { icon: Target, title: "Skills & capability", description: "Connect role expectations to capability gaps and development priorities.", details: ["Role and skill mappings", "Gaps, plans and development actions"] },
  { icon: ShieldCheck, title: "Compliance readiness", description: "Connect requirements, due dates, exceptions and supporting evidence.", details: ["Requirements and due dates", "Evidence and exception context"] },
  { icon: ClipboardCheck, title: "Assessments", description: "Check understanding and keep results connected to the learning journey.", details: ["Question banks and attempts", "Pass rules and recorded results"] },
  { icon: Award, title: "Credentials", description: "Keep issued credentials connected to learning history and expiry status.", details: ["Certificates and expiry", "Verification and revocation"] },
  { icon: BarChart3, title: "Workforce intelligence", description: "Turn learning and capability signals into clearer management attention.", details: ["Manager and executive views", "Reports, filters and action queues"] },
] as const;

const journey = [
  ["01","Role expectation","Define what the role needs to know, demonstrate or maintain."],
  ["02","Capability gap","Compare expectations with current learning, skills and evidence."],
  ["03","Development action","Connect gaps to learning, practice and development plans."],
  ["04","Assessment & evidence","Record results, credentials and compliance evidence in context."],
  ["05","Readiness signal","Surface what is complete, at risk or waiting for review."],
  ["06","Manager action","Give accountable people the context to decide what happens next."],
] as const;

const outcomes = [
  ["Reduce fragmentation","Bring learning, skills, assessments, credentials and compliance context into a more connected operating picture."],
  ["Focus development investment","Direct attention toward role-relevant gaps instead of treating all learning demand the same."],
  ["Improve evidence visibility","Give managers, L&D and compliance teams a clearer path from requirements to supporting records."],
  ["Move from reporting to action","Turn workforce signals into accountable follow-through on people, roles and capability priorities."],
] as const;

const audiences = [
  ["EXECUTIVE LEADERS","Know if the workforce is ready.","See the capability picture behind strategic priorities and identify where leadership attention is required."],
  ["CHRO / HR","Turn workforce data into capability decisions.","Connect roles, skills, development and readiness so workforce planning has a clearer capability foundation."],
  ["COO / OPERATIONS","Know who is ready for the work.","See role requirements, capability gaps and readiness signals across teams, sites and operating units."],
  ["L&D TEAMS","Make learning close capability gaps.","Connect programs, learning activity and development plans to the skills and role requirements that matter."],
  ["MANAGERS","Know who needs support.","See team needs, evidence and development activity, then move the right actions forward."],
  ["COMPLIANCE TEAMS","Keep requirements and evidence visible.","Track requirements, status, credentials and exceptions with a clearer route to accountable action."],
] as const;

const enterprisePaths = [
  { icon: ShieldCheck, title: "Security & Trust", description: "Review governance, access, evidence principles and verified trust information.", href: "/trust", action: "Review trust posture" },
  { icon: Globe2, title: "Integrations", description: "Scope identity, people data, APIs, webhooks and reporting around real enterprise data flows.", href: "/integrations", action: "Review integration approach" },
  { icon: LockKeyhole, title: "Implementation", description: "Plan discovery, configuration, validation, rollout and operational ownership as part of the product decision.", href: "/implementation", action: "Review implementation" },
] as const;

const questions = [
  ["How should we evaluate Kalam?","Use a representative workforce scenario and follow it from role expectations through learning, assessment, evidence, and management action. Review security, integration, governance, and deployment scope alongside the workflow."],
  ["How should we interpret readiness signals?","Use readiness signals to identify records, capability areas, and workforce conditions that require human review. Kalam provides evidence to support accountable decisions—it does not independently certify competence or regulatory compliance."],
  ["Can Kalam fit our existing enterprise systems?","Integration is scoped around your identity, people-data, reporting, and service architecture. During technical review, we confirm supported connectors, integration requirements, deployment approach, and applicable implementation commitments."],
] as const;

export default function Home() {
  const inquiriesEnabled = process.env.MARKETING_INBOX_ENABLED === "true" && !!process.env.MARKETING_REVIEW_TENANT_SLUG;
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
  const structuredData = {
    "@context":"https://schema.org",
    "@graph":[
      {"@type":"Organization","@id":siteUrl+"/#organization",name:"Kalam",url:siteUrl,logo:siteUrl+"/kalam-logo.svg",description:"Enterprise Workforce Capability Platform connecting workforce expectations, development, evidence and action."},
      {"@type":"SoftwareApplication","@id":siteUrl+"/#software",name:"Kalam",applicationCategory:"BusinessApplication",operatingSystem:"Web",url:siteUrl,description:"Enterprise Workforce Capability Platform for learning, skills, compliance, development, evidence and workforce readiness.",publisher:{"@id":siteUrl+"/#organization"}},
    ],
  };

  return <div className={styles.page}>
    <script type="application/ld+json" dangerouslySetInnerHTML={{__html:JSON.stringify(structuredData)}}/>
    <a className={styles.skip} href="#main">Skip to content</a>
    <PublicHeader landing/>

    <main id="main">
      <section className={styles.hero} aria-labelledby="hero-title">
        <div className={styles.container}>
          <div className={styles.heroGrid}>
            <div className={styles.heroCopy}>
              <div className={styles.eyebrow}><span/> ENTERPRISE WORKFORCE CAPABILITY PLATFORM</div>
              <h1 id="hero-title"><span>Build Capability.</span><em>Prove Readiness.</em></h1>
              <p>Kalam connects roles, skills, learning, assessment, evidence and workforce readiness in one enterprise capability platform—so organizations can see capability gaps, strengthen readiness and turn workforce capability into business action.</p>
              <div className={styles.heroActions}>
                <PublicButton href="#how-it-works">See how Kalam works <ArrowRight size={17}/></PublicButton>
                <PublicButton href="/guided-evaluation" variant="secondary">Run a guided evaluation <ChevronRight size={16}/></PublicButton>
              </div>
              <div className={styles.heroNote}><ShieldCheck size={18}/> More than an LMS: connect learning to capability, evidence and workforce readiness.</div>
            </div>
            <CapabilityCommandCenter/>
          </div>
          <div className={styles.heroRail} aria-label="Kalam capability model"><strong>THE KALAM CAPABILITY MODEL</strong><span>Expectation <ChevronRight size={14}/> Capability <ChevronRight size={14}/> Evidence <ChevronRight size={14}/> Action <ChevronRight size={14}/> Readiness</span></div>
        </div>
      </section>

      <section className={styles.signalBand} aria-label="The workforce capability problem">
        <div className={styles.container}><div className={styles.problemIntro}><span>THE WORKFORCE CAPABILITY PROBLEM</span><h2>Your workforce data is everywhere. Your capability decisions shouldn’t be.</h2><p>Your LMS tracks learning. Your HR system holds people data. Spreadsheets track skills. Compliance records sit elsewhere. Kalam connects the capability picture between them.</p></div></div>
        <div className={styles.container}><div className={styles.signalGrid}>
          <article><ShieldCheck size={20}/><span><strong>One connected capability picture</strong><small>Bring roles, skills, learning, assessment, evidence and readiness into context.</small></span></article>
          <article><UsersRound size={20}/><span><strong>Beyond learning completion</strong><small>Connect development activity to capability gaps and role requirements.</small></span></article>
          <article><Globe2 size={20}/><span><strong>Built for enterprise decisions</strong><small>Give leaders and managers clearer signals about gaps, readiness and action.</small></span></article>
          <article><FileCheck2 size={20}/><span><strong>Actionable by design</strong><small>Move from fragmented reporting to accountable workforce action.</small></span></article>
        </div></div>
      </section>

      <section id="platform" className={styles.section} aria-labelledby="platform-title">
        <div className={styles.container}>
          <div className={styles.sectionHead}><div><span>THE PLATFORM</span><h2 id="platform-title">More than an LMS.<br/><em>Built for workforce capability.</em></h2></div><p>Connect role requirements, skills, learning, assessment, evidence, compliance and readiness in one operating picture—so capability becomes visible and actionable.</p></div>
          <div className={styles.capabilityGrid}>{capabilities.map(({icon:Icon,title,description,details},index)=><details className={styles.capabilityCard} key={title}><summary><span className={styles.cardTop}><span className={styles.cardIcon}><Icon size={21}/></span><span className={styles.cardNumber}>0{index+1}</span></span><strong>{title}</strong><p>{description}</p><span className={styles.cardAction}>Explore capability <ChevronRight size={15}/></span></summary><div className={styles.cardDetail}><b>In the workspace</b><ul>{details.map(item=><li key={item}>{item}</li>)}</ul></div></details>)}</div>
        </div>
      </section>

      <section id="difference" className={`${styles.section} ${styles.differenceSection}`} aria-labelledby="difference-title">
        <div className={styles.container}>
          <div className={styles.sectionHead}><div><span>WHY KALAM</span><h2 id="difference-title">Training completion is not<br/><em>workforce capability.</em></h2></div><p>Most organizations already have systems for learning and people data. Kalam connects the capability layer between them, so development can be understood in the context of roles, skills, evidence and readiness.</p></div>
          <div className={styles.differenceGrid}>
            <article><span>TRADITIONAL LMS</span><h3>What people completed</h3><p>Courses, assignments, attendance and completion remain the center of the record.</p></article>
            <article><span>KALAM</span><h3>What the workforce can demonstrate</h3><p>Connect role expectations, skills, learning, assessment and evidence to a clearer readiness picture.</p></article>
            <article><span>HR SYSTEM</span><h3>Who the people are</h3><p>Workforce identity and organizational context stay connected without turning Kalam into an HRIS.</p></article>
          </div>
        </div>
      </section>

      <section id="how-it-works" className={`${styles.section} ${styles.sectionTint}`} aria-labelledby="journey-title">
        <div className={styles.container}>
          <div className={styles.sectionHead}><div><span>HOW KALAM WORKS</span><h2 id="journey-title">A connected path from<br/><em>expectation to action.</em></h2></div><p>Capability becomes manageable when role expectations, development, evidence and management action remain part of one traceable journey.</p></div>
          <div className={styles.journeyGrid}>{journey.map(([number,title,description])=><article key={number}><span>{number}</span><h3>{title}</h3><p>{description}</p></article>)}</div>
        </div>
      </section>

      <section id="outcomes" className={`${styles.section} ${styles.outcomesSection}`} aria-labelledby="outcomes-title">
        <div className={styles.container}>
          <div className={styles.sectionHead}><div><span>BUSINESS OUTCOMES</span><h2 id="outcomes-title">Designed for workforce outcomes.<br/><em>Built to turn evidence into action.</em></h2></div><p>Start with the operating outcome your organization needs, then connect the learning, capability and evidence workflow behind it.</p></div>
          <div className={styles.outcomeGrid}>{outcomes.map(([title,description],index)=><article key={title}><span>0{index+1}</span><h3>{title}</h3><p>{description}</p></article>)}</div>
        </div>
      </section>

      <section id="roles" className={`${styles.section} ${styles.rolesSection}`} aria-labelledby="roles-title">
        <div className={styles.container}>
          <div className={styles.sectionHead}><div><span>ONE SYSTEM, MANY DECISIONS</span><h2 id="roles-title">One shared view of capability.<br/><em>Clear actions for every team.</em></h2></div><p>The same workforce record should answer different questions for the people responsible for development, readiness and risk.</p></div>
          <div className={styles.roleGrid}>{audiences.map(([label,title,description])=><article key={label}><span>{label}</span><h3>{title}</h3><p>{description}</p></article>)}</div>
        </div>
      </section>

      <section id="enterprise-readiness" className={`${styles.section} ${styles.enterpriseSection}`} aria-labelledby="enterprise-title">
        <div className={styles.container}>
          <div className={styles.sectionHead}><div><span>ENTERPRISE READINESS</span><h2 id="enterprise-title">Evaluate the product,<br/><em>the controls and the rollout.</em></h2></div><p>Enterprise adoption depends on more than feature fit. Review how Kalam aligns with your security, integration and implementation requirements before deployment.</p></div>
          <div className={styles.enterpriseGrid}>{enterprisePaths.map(({icon:Icon,title,description,href,action})=><article key={title}><Icon size={23}/><h3>{title}</h3><p>{description}</p><Link href={href}>{action} <ArrowRight size={15}/></Link></article>)}</div>
        </div>
      </section>

      <section id="questions" className={styles.section} aria-labelledby="questions-title">
        <div className={styles.container}><div className={styles.questionLayout}>
          <div className={styles.questionIntro}><span className={styles.kicker}>ENTERPRISE QUESTIONS, ANSWERED</span><h2 id="questions-title">Clear answers.<br/><em>Confident decisions.</em></h2><p>Before you evaluate Kalam, understand how it fits your operating model, technology environment, governance requirements, and path to enterprise adoption.</p><div className={styles.questionMeta}><span><strong>01</strong><small>Business fit</small></span><span><strong>02</strong><small>Technology fit</small></span><span><strong>03</strong><small>Adoption path</small></span></div></div>
          <div className={styles.questionList}>
            {questions.map(([question,answer],index)=><details key={question} open={index===0}>
              <summary><span className={styles.questionSummary}><b>0{index+1}</b><span>{question}</span></span><ChevronRight size={18}/></summary>
              <div className={styles.questionAnswer}><span className={styles.answerMark}><ShieldCheck size={16}/></span><p>{answer}</p></div>
            </details>)}
            <Link className={styles.questionCta} href="/guided-evaluation"><span><b>Ready to evaluate Kalam?</b><small>Use a representative workforce scenario and see the platform in context.</small></span><ArrowRight size={18}/></Link>
          </div>
        </div></div>
      </section>

      {inquiriesEnabled && <section id="demo" className={`${styles.section} ${styles.demoSection}`} aria-labelledby="demo-title"><div className={styles.container}><div className={styles.demoGrid}><div className={styles.demoIntro}><div className={styles.demoIntroTop}><span className={styles.kicker}>LET&apos;S TALK</span><span className={styles.demoBadge}>01 / CONVERSATION</span></div><h2 id="demo-title">Start with your<br/><em>operating reality.</em></h2><p>Tell us what your organization is trying to improve across capability, learning, compliance, or workforce readiness. We&apos;ll start with the context that matters to your team.</p><div className={styles.demoSignals}><div><span><Target size={16}/></span><section><b>Start with the priority</b><small>Tell us the outcome or capability challenge behind the conversation.</small></section></div><div><span><UsersRound size={16}/></span><section><b>Bring the right context</b><small>We&apos;ll use your information to prepare a more relevant discussion.</small></section></div><div><span><ArrowRight size={16}/></span><section><b>Move toward action</b><small>Explore the right next step for your organization—not a generic demo.</small></section></div></div><div className={styles.demoLoop}><span>YOUR PRIORITY</span><i></i><span>RIGHT CONTEXT</span><i></i><span>NEXT ACTION</span></div></div><DemoInquiryForm/></div></div></section>}

      {!inquiriesEnabled && <section className={styles.closing} aria-labelledby="closing-title"><div className={styles.container}><div className={styles.closingInner}><div><span>THE NEXT STEP</span><h2 id="closing-title">Turn capability priorities<br/>into business action.</h2><p>See how Kalam connects the workforce picture, then explore the path that fits your organization.</p></div><div><PublicButton href="/contact-sales" variant="secondary">Contact sales <ArrowRight size={17}/></PublicButton><Link href="/login">Already have access? Sign in <ChevronRight size={15}/></Link></div></div></div></section>}
    </main>

    <PublicFooter landing/>
  </div>;
}


