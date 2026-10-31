import { notFound, redirect } from "next/navigation";
import { AssessmentRunner } from "@/components/assessment-runner";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJson, requireUser } from "@/lib/server-api";

type Assessment = {
  id: string;
  title: string;
  passing_score: number;
  max_attempts?: number | null;
  time_limit_minutes?: number | null;
  questions: Array<{ id: string; question_type: string; prompt: string; options: string[]; points: number; position: number }>;
};

export default async function AssessmentPage({ params }: { params: Promise<{ id: string }> }) {
  const user=await requireUser<{permissions?:string[]}>();
  const { id } = await params;
  if(user.permissions?.includes("assessments.grade_assigned")&&!user.permissions?.includes("assessments.manage")) {
    redirect(`/dashboard/assessments/review/${id}`);
  }
  const assessment = await apiJson<Assessment>(`/api/v1/assessments/${id}`);
  if (!assessment) notFound();
  return (
    <DashboardShell title={assessment.title} eyebrow="Assessment player">
      <AssessmentRunner assessment={assessment} />
    </DashboardShell>
  );
}
