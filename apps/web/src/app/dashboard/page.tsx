import Link from "next/link";
import {
  Award,
  BarChart3,
  BookOpenCheck,
  CheckCircle2,
  ClipboardCheck,
  FileText,
  Layers3,
  ShieldCheck,
  UsersRound,
} from "lucide-react";

import { DashboardShell } from "@/components/dashboard-shell";
import { apiJson, requireUser } from "@/lib/server-api";

type Summary = {
  users: number;
  courses: number;
  enrollments: number;
  completed_enrollments: number;
  certificates: number;
  compliance_assignments: number;
};

type Course = {
  id: string;
  title: string;
  slug: string;
  description?: string | null;
  status: string;
  estimated_minutes?: number | null;
};

type Enrollment = {
  id: string;
  course_id: string;
  status: string;
  due_at?: string | null;
  completed_at?: string | null;
};

type ComplianceAssignment = {
  id: string;
  requirement: string;
  status: string;
};

type CertificateSummary = {
  id: string;
  course: string;
  verification_code: string;
};

const modules = [
  ["Learning catalog", "Courses, modules, lessons and publishing", "/dashboard/catalog", BookOpenCheck],
  ["Learners & teams", "People, teams and manager visibility", "/dashboard/people", UsersRound],
  ["Assessments", "Question banks, exams and grading", "/dashboard/assessments", ClipboardCheck],
  ["Credentials", "Certificates, expiry and verification", "/dashboard/certificates", Award],
  ["Compliance", "Mandatory learning and evidence", "/dashboard/compliance", ShieldCheck],
  ["Skills & development", "Competencies and development plans", "/dashboard/skills", Layers3],
  ["Analytics", "Learning and capability reporting", "/dashboard/reports", BarChart3],
  ["Reports", "Exports and operational evidence", "/dashboard/reports", FileText],
] as const;

export default async function DashboardPage() {
  const user = await requireUser<{
    first_name: string;
    last_name: string;
    email: string;
    job_title?: string | null;
  }>();

  const [summary, courses, enrollments, compliance, skills, certificates] =
    await Promise.all([
      apiJson<Summary>("/api/v1/reports/summary"),
      apiJson<Course[]>("/api/v1/courses"),
      apiJson<Enrollment[]>("/api/v1/courses/my/enrollments"),
      apiJson<ComplianceAssignment[]>("/api/v1/compliance/my"),
      apiJson<{ id: string }[]>("/api/v1/skills/my"),
      apiJson<CertificateSummary[]>("/api/v1/certificates/my"),
    ]);

  const activeCourses = courses?.length ?? 0;
  const assigned = enrollments?.length ?? 0;
  const completed = enrollments?.filter((item) => item.status === "completed").length ?? 0;
  const complianceOpen = compliance?.filter((item) => item.status !== "completed").length ?? 0;

  return (
    <DashboardShell title="Learning command center" eyebrow="Executive workspace">
      <section className="dashboard-hero">
        <div>
          <span className="eyebrow">Corporate capability</span>
          <h2>Welcome, {user.first_name}.</h2>
          <p>
            {user.job_title || "Learning workspace"} · {user.email}. Your dashboard is now connected to persisted LMS records.
          </p>
        </div>
        <div className="hero-status-card">
          <strong>Live data</strong>
          <span>Connected to platform services</span>
          <small>Permissions and tenant scope are enforced by the API.</small>
        </div>
      </section>

      <section className="stat-grid" aria-label="Learning metrics">
        <div className="stat-card"><span>My courses</span><strong>{assigned}</strong><small>{completed} completed</small></div>
        <div className="stat-card"><span>Available learning</span><strong>{activeCourses}</strong><small>Published courses</small></div>
        <div className="stat-card"><span>Compliance</span><strong>{complianceOpen}</strong><small>Open requirements</small></div>
        <div className="stat-card"><span>Skills</span><strong>{skills?.length ?? 0}</strong><small>Recorded capabilities</small></div>
      </section>

      {summary && (
        <section className="data-panel">
          <div className="section-heading compact">
            <div><span className="eyebrow">Authorized reporting</span><h2>Organization snapshot</h2></div>
            <span className="section-meta">{summary.users} people · {summary.courses} courses</span>
          </div>
          <div className="metric-strip">
            <span><b>{summary.enrollments}</b> enrollments</span>
            <span><b>{summary.completed_enrollments}</b> completions</span>
            <span><b>{summary.certificates}</b> certificates</span>
            <span><b>{summary.compliance_assignments}</b> compliance assignments</span>
          </div>
        </section>
      )}

      <section className="module-section">
        <div className="section-heading compact">
          <div><span className="eyebrow">Module map</span><h2>Operational domains</h2></div>
          <span className="section-meta">Live service surfaces</span>
        </div>
        <div className="module-grid">
          {modules.map(([title, description, href, Icon]) => (
            <Link className="module-card" href={href} key={title}>
              <div className="module-icon"><Icon size={20} /></div>
              <div><h3>{title}</h3><p>{description}</p></div>
              <span className="module-arrow">→</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="data-panel">
        <div className="section-heading compact">
          <div><span className="eyebrow">Recent learning</span><h2>Available courses</h2></div>
          <Link className="text-link" href="/dashboard/catalog">Open catalog →</Link>
        </div>
        {courses?.length ? (
          <div className="compact-list">
            {courses.slice(0, 5).map((course) => (
              <Link href={`/dashboard/catalog/${course.id}`} key={course.id} className="compact-row">
                <div><strong>{course.title}</strong><small>{course.estimated_minutes ?? "—"} min · {course.status}</small></div>
                <CheckCircle2 size={17} />
              </Link>
            ))}
          </div>
        ) : (
          <div className="empty-state"><BookOpenCheck size={24} /><p>No published courses are currently available.</p></div>
        )}
      </section>

      {certificates?.length ? (
        <section className="data-panel">
          <div className="section-heading compact">
            <div><span className="eyebrow">Credentials</span><h2>Latest certificates</h2></div>
            <Link className="text-link" href="/dashboard/certificates">View all →</Link>
          </div>
          <div className="compact-list">
            {certificates.slice(0, 3).map((certificate) => (
              <div className="compact-row" key={certificate.id}>
                <div><strong>{certificate.course}</strong><small>Verification: {certificate.verification_code}</small></div>
                <Award size={17} />
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </DashboardShell>
  );
}
