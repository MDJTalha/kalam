import type { Metadata } from "next";
import { ArrowRight, BarChart3, CheckCircle2, ClipboardCheck, FlaskConical, Gauge, Layers3, LockKeyhole, ShieldCheck, Target, Workflow } from "lucide-react";
import { CommercialShell } from "@/components/commercial-shell";
import { PublicButton } from "@/components/public-button";
import { CommercialInquiryForm } from "@/components/commercial-inquiry-form";
import styles from "@/app/commercial.module.css";

export const metadata: Metadata = {
  title: "Enterprise Evaluation",
  description: "Evaluate Kalam against your organization's roles, workflows, skills, learning and workforce readiness requirements through a structured enterprise evaluation.",
  alternates: { canonical: "/guided-evaluation" },
};

type EvaluationArea = { icon: typeof Layers3; title: string; copy: string };
type EvaluationStep = [number, string, string];
type EvaluationOutcome = [string, string];

const evaluationAreas: EvaluationArea[] = [
  { icon: Layers3, title: "Capability architecture", copy: "Test how roles, capabilities, skills and readiness expectations can be represented in Kalam." },
  { icon: Target, title: "Skills & role readiness", copy: "Validate how teams can see capability requirements, gaps and readiness by role." },
  { icon: Workflow, title: "Operational workflows", copy: "Run representative learning, assessment, compliance and workforce workflows in context." },
  { icon: ClipboardCheck, title: "Assessment & evidence", copy: "See how assessment outcomes and supporting evidence contribute to a clearer capability picture." },
  { icon: ShieldCheck, title: "Compliance & control", copy: "Review permissions, accountability, auditability and the controls relevant to adoption." },
  { icon: BarChart3, title: "Workforce visibility", copy: "Evaluate management and leadership views needed to turn capability data into action." },
  { icon: Gauge, title: "Integrations & data", copy: "Explore how Kalam fits with systems and data flows already present in your environment." },
  { icon: LockKeyhole, title: "Security & governance", copy: "Give IT and governance stakeholders a structured basis for technical and control review." },
];

const evaluationSteps: EvaluationStep[] = [
  [1, "Define", "Agree the business question, users, scope and success criteria."],
  [2, "Configure", "Shape the evaluation around a representative workforce scenario."],
  [3, "Validate", "Run the workflows and capabilities that matter to your team."],
  [4, "Review", "Bring business, technology and governance stakeholders together around the findings."],
  [5, "Decide", "Leave with a clearer basis for the appropriate next step."],
];

const outcomes: EvaluationOutcome[] = [
  ["Fit clarity", "Understand where Kalam fits your workforce capability priorities—and where further validation is needed."],
  ["Workflow validation", "See the platform against real roles, processes and operating scenarios rather than a generic walkthrough."],
  ["Stakeholder confidence", "Create a shared evaluation basis for business, IT, security and governance stakeholders."],
  ["A clear next step", "Move from evaluation findings to a practical commercial or implementation decision."],
];

const evaluationCriteria: EvaluationOutcome[] = [
  ["Your workforce", "Use representative roles, teams and responsibilities rather than an abstract demo audience."],
  ["Your workflows", "Test the processes that connect learning, skills, assessment, evidence and readiness."],
  ["Your capability model", "Validate the way your organization defines capability, proficiency and role readiness."],
  ["Your enterprise environment", "Give business, IT, security and governance stakeholders the context they need to evaluate fit."],
];

export default function GuidedEvaluationPage() {
  return (
    <CommercialShell>
      <section className={styles.evaluationHero}>
        <div className={styles.container}>
          <div className={styles.evaluationGrid}>
            <div className={styles.evaluationIntro}>
              <span className={styles.kicker}><FlaskConical size={14}/> Guided enterprise evaluation</span>
              <h1>Prove fit before you commit.</h1>
              <p className={styles.evaluationLead}>Evaluate Kalam against the roles, workflows and capability outcomes that matter to your organization—before making a broader deployment decision.</p>
              <div className={styles.evaluationBenefits}>
                <span><CheckCircle2 size={16}/> Built around your workforce and operating reality</span>
                <span><CheckCircle2 size={16}/> Success criteria agreed before evaluation begins</span>
                <span><CheckCircle2 size={16}/> A shared basis for business, IT and governance stakeholders</span>
              </div>
              <div className={styles.evaluationSteps} aria-label="Evaluation journey">
                <div className={styles.activeStep}><b>01</b><span><strong>Define</strong><small>Set the question</small></span></div>
                <div><b>02</b><span><strong>Validate</strong><small>Run the scenario</small></span></div>
                <div><b>03</b><span><strong>Decide</strong><small>Review the fit</small></span></div>
              </div>
              <div className={styles.evaluationAssurance}><ShieldCheck size={18}/><div><strong>Designed for a meaningful evaluation</strong><span>Scope, participants, access and decision criteria are aligned before activation so your team can evaluate Kalam in the right context.</span></div></div>
            </div>
            <div className={styles.evaluationFormStack} id="evaluation-request">
              <div className={styles.evaluationContextBar}><span><b>PLAN YOUR EVALUATION</b><strong>Let’s define what you need to prove.</strong></span><small>Your context shapes the evaluation scope before access is provisioned.</small></div>
              <CommercialInquiryForm mode="trial" />
            </div>
          </div>
        </div>
      </section>

      <section className={styles.evaluationFramework}>
        <div className={styles.container}>
          <div className={styles.evaluationSectionHead}>
            <div><span className={styles.kicker}>WHY EVALUATE KALAM</span><h2>Don’t evaluate software.<br/><em>Evaluate the fit.</em></h2></div>
            <p>A meaningful enterprise evaluation starts with your operating reality. Kalam is assessed against the workforce, workflows, capability model and environment that will determine whether it creates value.</p>
          </div>
          <div className={styles.evaluationAreaGrid}>
            {evaluationCriteria.map(([title, copy], index) => <article key={title}><span><Target size={18}/></span><h3>{title}</h3><p>{copy}</p><b>0{index + 1}</b></article>)}
          </div>
        </div>
      </section>

      <section className={styles.evaluationPlans}>
        <div className={styles.container}>
          <div className={styles.evaluationSectionHead}>
            <div><span className={styles.kicker}>WHAT YOU CAN EVALUATE</span><h2>Evaluate Kalam where it matters.</h2></div>
            <p>Choose the areas that matter to your business case. The evaluation can combine multiple workflows into one representative scenario.</p>
          </div>
          <div className={styles.evaluationAreaGrid}>
            {evaluationAreas.map(({ icon: Icon, title, copy }) => <article key={title}><span><Icon size={18}/></span><h3>{title}</h3><p>{copy}</p></article>)}
          </div>
        </div>
      </section>

      <section className={styles.evaluationFramework}>
        <div className={styles.container}>
          <div className={styles.evaluationSectionHead}>
            <div><span className={styles.kicker}>HOW THE EVALUATION WORKS</span><h2>From business question to decision evidence.</h2></div>
            <p>The evaluation is structured so every stage has a purpose, a stakeholder outcome and a clear transition to the next step.</p>
          </div>
          <div className={styles.evaluationStepGrid}>
            {evaluationSteps.map(([number, title, copy]) => <article key={number}><span><span className={styles.stepNumber}>{String(number).padStart(2, "0")}</span></span><h3>{title}</h3><p>{copy}</p></article>)}
          </div>
        </div>
      </section>

      <section className={styles.evaluationPlans}>
        <div className={styles.container}>
          <div className={styles.evaluationSectionHead}>
            <div><span className={styles.kicker}>WHAT YOU LEAVE WITH</span><h2>A clearer basis for the decision.</h2></div>
            <p>The goal is not simply to give your team access. It is to create relevant validation for stakeholders to understand fit and agree on the right next move.</p>
          </div>
          <div className={styles.evaluationAreaGrid}>
            {outcomes.map(([title, copy]) => <article key={title}><span><CheckCircle2 size={18}/></span><h3>{title}</h3><p>{copy}</p></article>)}
          </div>
          <div className={styles.evaluationFooterNote}><LockKeyhole size={17}/><span><strong>Enterprise evaluation, not self-service production access.</strong> Scope, participants, access and governance expectations are confirmed before evaluation access is provisioned.</span></div>
        </div>
      </section>

      <section className={styles.evaluationFramework}>
        <div className={styles.container}>
          <div className={styles.heroPanel}>
            <span className={styles.kicker}>READY WHEN YOU ARE</span>
            <h2>Have a real workforce scenario in mind?</h2>
            <p>Bring the roles, workflows or capability challenge you want to validate. We’ll use that context to shape an evaluation relevant to your organization.</p>
            <div className={styles.heroActions}>
              <PublicButton href="#evaluation-request">Plan my evaluation <ArrowRight size={16}/></PublicButton>
              <PublicButton href="/contact-sales" variant="secondary">Talk to Sales</PublicButton>
            </div>
          </div>
        </div>
      </section>
    </CommercialShell>
  );
}
