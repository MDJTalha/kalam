import Link from "next/link";
import { notFound } from "next/navigation";
import { AssessmentRunner } from "@/components/assessment-runner";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type Assessment = {
  id: string;
  title: string;
  passing_score: number;
  max_attempts?: number | null;
  time_limit_minutes?: number | null;
  questions: Array<{ id: string; question_type: string; prompt: string; options: string[]; points: number; position: number }>;
};

export default async function AssessmentPage({ params }: { params: Promise<{ id: string }> }) {
  await requireUser();
  const { id } = await params;
  if (!/^[0-9a-fA-F-]{36}$/.test(id)) notFound();
  const result = await apiJsonResult<Assessment>(`/api/v1/assessments/${id}`);
  if (result.status === 404) notFound();
  if (!result.ok || !result.data) {
    const restricted = result.status === 403;
    return <DashboardShell title="Assessment unavailable" eyebrow="Assessment player">
      <section className="data-panel" role="alert">
        <h2>{restricted ? "Assessment access restricted" : "Assessment could not be loaded"}</h2>
        <p>{restricted ? "Your role does not have access to this assessment." : result.error || "The assessment service is unavailable. Try again shortly."}</p>
        <Link className="text-link" href="/dashboard/assessments">Return to assessments</Link>
      </section>
    </DashboardShell>;
  }
  const assessment = result.data;
  return (
    <DashboardShell title={assessment.title} eyebrow="Assessment player">
      <AssessmentRunner assessment={assessment} />
    </DashboardShell>
  );
}
