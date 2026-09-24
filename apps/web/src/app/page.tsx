import Link from "next/link";
import { ArrowRight, Award, BarChart3, BookOpenCheck, BriefcaseBusiness, CheckCircle2, Layers3, ShieldCheck, Sparkles, UsersRound } from "lucide-react";

const capabilities = [
  ["Learning", "Courses, curricula, learning paths, enrollments and progress.", BookOpenCheck],
  ["Compliance", "Mandatory training, due dates, evidence, expiry and escalations.", ShieldCheck],
  ["Skills", "Competencies, role requirements, skill gaps and development.", Layers3],
  ["Assessments", "Question banks, grading, pass rules and secure attempts.", CheckCircle2],
  ["Credentials", "Certificates, expiry, revocation and public verification.", Award],
  ["Analytics", "Executive, L&D, manager and compliance visibility.", BarChart3],
] as const;

export default function Home() {
  return (
    <main className="marketing-shell">
      <nav className="marketing-nav container">
        <div className="brand-lockup"><span className="brand-mark"><BriefcaseBusiness size={19} /></span><span>Corporate LMS</span></div>
        <div className="nav-actions"><Link className="button button-ghost" href="/login">Sign in</Link><Link className="button button-primary" href="/dashboard">Open platform <ArrowRight size={16} /></Link></div>
      </nav>
      <section className="hero container">
        <div className="hero-copy">
          <span className="eyebrow"><Sparkles size={15} /> Enterprise learning operating system</span>
          <h1>Turn learning into <span>workforce capability.</span></h1>
          <p className="hero-lede">A governed corporate learning platform connecting learning, compliance, skills, assessments, credentials and decision-ready analytics.</p>
          <div className="hero-actions"><Link className="button button-primary button-large" href="/dashboard">Enter workspace <ArrowRight size={18} /></Link><a className="button button-secondary button-large" href="#capabilities">Explore capabilities</a></div>
          <div className="hero-proof"><div><ShieldCheck size={16} /><span>Tenant-aware</span></div><div><UsersRound size={16} /><span>Role-controlled</span></div><div><BarChart3 size={16} /><span>Evidence-driven</span></div></div>
        </div>
        <div className="hero-panel">
          <div className="hero-panel-top"><span>Learning command center</span><span className="status-dot"><i /> Foundation</span></div>
          <div className="hero-metric-grid"><div><strong>Learning</strong><span>Courses & paths</span></div><div><strong>People</strong><span>Employees & managers</span></div><div><strong>Risk</strong><span>Compliance evidence</span></div><div><strong>Capability</strong><span>Skills & development</span></div></div>
          <div className="hero-flow"><span>Assign</span><b>→</b><span>Learn</span><b>→</b><span>Assess</span><b>→</b><span>Evidence</span></div>
          <div className="hero-note"><ShieldCheck size={18} /><div><strong>Built for accountable learning</strong><p>Business records, permissions and auditability are part of the product—not afterthoughts.</p></div></div>
        </div>
      </section>
      <section id="capabilities" className="section container">
        <div className="section-heading"><span className="eyebrow">Core capabilities</span><h2>A single governed learning foundation</h2><p>Designed around HR, L&D, managers, learners, instructors and compliance teams.</p></div>
        <div className="capability-grid">{capabilities.map(([title, description, Icon]) => <article className="capability-card" key={title}><div className="capability-icon"><Icon size={19} /></div><h3>{title}</h3><p>{description}</p></article>)}</div>
      </section>
      <footer className="marketing-footer"><div className="container footer-row"><span>Corporate LMS · Engineering foundation</span><span>WCAG 2.2 AA target · Multi-tenant architecture</span></div></footer>
    </main>
  );
}
