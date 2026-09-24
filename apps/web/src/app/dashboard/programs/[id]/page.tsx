import Link from "next/link";
import { ArrowLeft, Layers3, UsersRound } from "lucide-react";
import { notFound } from "next/navigation";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJson, requireUser } from "@/lib/server-api";

type Course = { id: string; title: string; position: number; is_required: boolean };
type Program = { id: string; title: string; slug: string; description?: string | null; status: string; courses: Course[] };

export default async function ProgramDetailPage({ params }: { params: Promise<{ id: string }> }) {
  await requireUser();
  const { id } = await params;
  const program = await apiJson<Program>("/api/v1/programs/" + id);
  if (!program) notFound();

  return (
    <DashboardShell title={program.title} eyebrow="Program detail">
      <div className="data-panel">
        <Link href="/dashboard/programs" className="text-link"><ArrowLeft size={15}/> Back to programs</Link>
        <div className="section-heading">
          <span className="eyebrow">{program.status} · {program.slug}</span>
          <h2>{program.title}</h2>
          <p>{program.description || "No description has been published."}</p>
        </div>
        <div className="metric-strip">
          <span><b>{program.courses?.length ?? 0}</b> courses</span>
          <span><b>{program.courses?.filter((course) => course.is_required).length ?? 0}</b> required</span>
        </div>
      </div>

      <div className="data-panel">
        <div className="section-heading compact"><div><span className="eyebrow">Curriculum</span><h2>Program courses</h2></div><Layers3 size={20}/></div>
        {program.courses?.length ? (
          <div className="compact-list">
            {program.courses.map((course) => (
              <div className="compact-row" key={course.id}>
                <div><strong>{course.position}. {course.title}</strong><small>{course.is_required ? "Required component" : "Elective component"}</small></div>
              </div>
            ))}
          </div>
        ) : <div className="empty-state"><p>No courses have been added to this program.</p></div>}
      </div>

      <div className="data-panel">
        <div className="section-heading compact"><div><span className="eyebrow">Delivery</span><h2>Cohort management</h2></div><UsersRound size={20}/></div>
        <p>Use cohorts to group learners, enforce capacity, and launch program course enrollments as one controlled delivery operation.</p>
      </div>
    </DashboardShell>
  );
}
