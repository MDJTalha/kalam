import type { Metadata } from "next";
import { ArrowRight, BarChart3, CheckCircle2, ClipboardCheck, FlaskConical, LockKeyhole, ShieldCheck, Target } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { PublicButton } from "@/components/public-button";
import { CommercialInquiryForm } from "@/components/commercial-inquiry-form";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "Evaluate Kalam | Enterprise Capability Platform",
  description: "Evaluate Kalam against a representative workforce scenario before broader enterprise adoption.",
  alternates: { canonical: "/guided-evaluation" },
};

const criteria = [
  ["Your workforce", "Use representative roles, teams and responsibilities."],
  ["Your workflows", "Test how learning, assessment, evidence and development connect."],
  ["Your capability model", "Validate capability, proficiency and role expectations."],
  ["Your enterprise environment", "Review business, technology, security and governance fit."],
] as const;

const areas = [
  { icon: Target, title: "Capability", copy: "Roles, capabilities, competencies and readiness expectations." },
  { icon: ClipboardCheck, title: "Assessment", copy: "Assessment outcomes and evidence in context." },
  { icon: BarChart3, title: "Workforce insight", copy: "Management and leadership views for action." },
  { icon: ShieldCheck, title: "Governance", copy: "Permissions, accountability and enterprise controls." },
] as const;

const steps = [
  ["01", "Define", "Agree the business question and success criteria."],
  ["02", "Validate", "Run a representative workforce scenario."],
  ["03", "Decide", "Review findings and choose the appropriate next step."],
] as const;

export default function GuidedEvaluationPage() {
  return <CommercialShell>
    <section className={styles.evaluationHero}>
      <div className={styles.container}>
        <div className={styles.evaluationGrid}>
          <div className={styles.evaluationIntro}>
            <span className={styles.kicker}><FlaskConical size={14}/> GUIDED ENTERPRISE EVALUATION</span>
            <h1>Prove fit before you commit.</h1>
            <p className={styles.evaluationLead}>Evaluate Kalam against the roles, workflows and capability outcomes that matter to your organization.</p>
            <div className={styles.evaluationBenefits}>
              <span><CheckCircle2 size={16}/> Built around your operating reality</span>
              <span><CheckCircle2 size={16}/> Success criteria agreed up front</span>
              <span><CheckCircle2 size={16}/> One basis for business and technical review</span>
            </div>
            <div className={styles.evaluationSteps} aria-label="Evaluation journey">
              <div className={styles.activeStep}><b>01</b><span><strong>Define</strong><small>Set the question</small></span></div>
              <div><b>02</b><span><strong>Validate</strong><small>Run the scenario</small></span></div>
              <div><b>03</b><span><strong>Decide</strong><small>Review the fit</small></span></div>
            </div>
            <div className={styles.evaluationAssurance}><ShieldCheck size={18}/><div><strong>Enterprise evaluation, not generic access.</strong><span>Scope, participants, access and decision criteria are aligned before evaluation access is provisioned.</span></div></div>
          </div>
          <div className={styles.evaluationFormStack} id="evaluation-request">
            <div className={styles.evaluationContextBar}><span><b>PLAN YOUR EVALUATION</b><strong>Define what you need to prove.</strong></span><small>Your context shapes the evaluation scope.</small></div>
            <CommercialInquiryForm mode="trial" />
          </div>
        </div>
      </div>
    </section>

    <section className={styles.evaluationFramework}>
      <div className={styles.container}>
        <div className={styles.evaluationSectionHead}>
          <div><span className={styles.kicker}>WHY EVALUATE KALAM</span><h2>Evaluate the fit.<br/><em>Not just the software.</em></h2></div>
          <p>A meaningful evaluation uses your workforce, workflows, capability model and enterprise environment.</p>
        </div>
        <div className={styles.evaluationAreaGrid}>
          {criteria.map(([title, copy], index) => <article key={title}><span><Target size={18}/></span><h3>{title}</h3><p>{copy}</p><b>0{index + 1}</b></article>)}
        </div>
      </div>
    </section>

    <section className={styles.evaluationPlans}>
      <div className={styles.container}>
        <div className={styles.evaluationSectionHead}>
          <div><span className={styles.kicker}>WHAT TO VALIDATE</span><h2>Focus on what matters.</h2></div>
          <p>Combine the areas relevant to your business case into one representative evaluation.</p>
        </div>
        <div className={styles.evaluationAreaGrid}>
          {areas.map(({ icon: Icon, title, copy }) => <article key={title}><span><Icon size={18}/></span><h3>{title}</h3><p>{copy}</p></article>)}
        </div>
      </div>
    </section>

    <section className={styles.evaluationFramework}>
      <div className={styles.container}>
        <div className={styles.evaluationSectionHead}>
          <div><span className={styles.kicker}>THE EVALUATION</span><h2>From question to decision evidence.</h2></div>
          <p>Every stage has a defined purpose and a clear transition to the next decision.</p>
        </div>
        <div className={styles.evaluationStepGrid}>
          {steps.map(([number, title, copy]) => <article key={number}><span><span className={styles.stepNumber}>{number}</span></span><h3>{title}</h3><p>{copy}</p></article>)}
        </div>
      </div>
    </section>

    <section className={styles.evaluationPlans}>
      <div className={styles.container}>
        <div className={styles.evaluationSectionHead}>
          <div><span className={styles.kicker}>THE OUTCOME</span><h2>A clearer basis for the decision.</h2></div>
          <p>Leave with relevant validation for the people who need to understand fit and agree on the next move.</p>
        </div>
        <div className={styles.evaluationAreaGrid}>
          <article><span><CheckCircle2 size={18}/></span><h3>Fit clarity</h3><p>Understand where Kalam fits and where further validation is needed.</p></article>
          <article><span><CheckCircle2 size={18}/></span><h3>Workflow evidence</h3><p>See the platform against real roles and operating scenarios.</p></article>
          <article><span><CheckCircle2 size={18}/></span><h3>Stakeholder confidence</h3><p>Create a shared basis for business, IT and governance review.</p></article>
        </div>
        <div className={styles.evaluationFooterNote}><LockKeyhole size={17}/><span><strong>Controlled evaluation.</strong> Scope, participants and governance expectations are confirmed before access is provisioned.</span></div>
      </div>
    </section>

    <section className={styles.evaluationFramework}>
      <div className={styles.container}><div className={styles.heroPanel}>
        <span className={styles.kicker}>READY TO EVALUATE KALAM?</span>
        <h2>Bring a real capability challenge.</h2>
        <p>We'll use that context to shape an evaluation relevant to your organization.</p>
        <div className={styles.heroActions}><PublicButton href="#evaluation-request">Plan my evaluation <ArrowRight size={16}/></PublicButton><PublicButton href="/contact-sales" variant="secondary">Talk to Sales</PublicButton></div>
      </div></div>
    </section>
  </CommercialShell>;
}
