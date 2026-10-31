import { notFound } from "next/navigation";
import { AssessmentRunner } from "@/components/assessment-runner";
import { DashboardShell } from "@/components/dashboard-shell";
import { requireUser } from "@/lib/server-api";

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
  const assessment = await apiJsonResult<Assessment>(`/api/v1/assessments/${id}`).then((result) => result.ok ? result.data : null);
  if (!assessment) notFound();
  return (
    <DashboardShell title={assessment.title} eyebrow="Assessment player">
      <AssessmentRunner assessment={assessment} />
    </DashboardShell>
  );
}
