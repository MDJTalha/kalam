"use client";

import Link from "next/link";
import { BookOpenCheck, CheckCircle2, Clock3, Search, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";

type Course = {
  id: string;
  title: string;
  slug: string;
  description?: string | null;
  status: string;
  estimated_minutes?: number | null;
  enrollment_policy?: string;
  visibility?: string;
  tags?: string[];
};

type Props = {
  courses: Course[];
  enrollmentStatus: Record<string, string>;
};

const statusLabel: Record<string, string> = {
  enrolled: "In progress",
  in_progress: "In progress",
  completed: "Completed",
  pending_approval: "Pending approval",
  waitlisted: "Waitlisted",
  rejected: "Request declined",
  available: "Available",
};

export function LearnerCatalogBrowser({ courses, enrollmentStatus }: Props) {
  const [query, setQuery] = useState("");
  const [scope, setScope] = useState<"all" | "learning" | "available">("all");

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return courses.filter((course) => {
      const enrollment = enrollmentStatus[course.id];
      const matchesQuery = !normalized ||
        course.title.toLowerCase().includes(normalized) ||
        course.description?.toLowerCase().includes(normalized) ||
        course.slug.toLowerCase().includes(normalized) ||
        course.tags?.some(tag => tag.toLowerCase().includes(normalized));
      const learning = Boolean(enrollment && enrollment !== "rejected");
      const matchesScope =
        scope === "all" ||
        (scope === "learning" && learning) ||
        (scope === "available" && !learning);
      return matchesQuery && matchesScope;
    });
  }, [courses, enrollmentStatus, query, scope]);

  const learningCount = courses.filter((course) => Boolean(enrollmentStatus[course.id] && enrollmentStatus[course.id] !== "rejected")).length;
  const availableCount = courses.length - learningCount;

  return (
    <section className="learner-catalog" aria-labelledby="learner-catalog-title">
      <div className="learner-catalog-heading">
        <div>
          <span className="eyebrow">Find your next capability</span>
          <h2 id="learner-catalog-title">Learning catalog</h2>
          <p>Discover assigned and self-service learning in one place, with progress-aware status and clear next actions.</p>
        </div>
        <div className="learner-catalog-stat" aria-label="Catalog summary">
          <strong>{courses.length}</strong>
          <span>Published courses</span>
        </div>
      </div>

      <div className="learner-catalog-toolbar">
        <label className="learner-search">
          <Search size={16} aria-hidden="true" />
          <span className="sr-only">Search courses</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by title, topic or keyword"
            type="search"
          />
        </label>
        <div className="learner-scope-tabs" role="group" aria-label="Filter courses by learning status">
          <button type="button" className={scope === "all" ? "active" : ""} onClick={() => setScope("all")} aria-pressed={scope === "all"}>All <span>{courses.length}</span></button>
          <button type="button" className={scope === "learning" ? "active" : ""} onClick={() => setScope("learning")} aria-pressed={scope === "learning"}>My learning <span>{learningCount}</span></button>
          <button type="button" className={scope === "available" ? "active" : ""} onClick={() => setScope("available")} aria-pressed={scope === "available"}>Available <span>{availableCount}</span></button>
        </div>
      </div>

      <div className="learner-catalog-results" aria-live="polite">
        <div className="learner-results-meta">
          <span>{filtered.length} {filtered.length === 1 ? "course" : "courses"} shown</span>
          {query && <span>Search: “{query}”</span>}
        </div>
        {filtered.length ? (
          <div className="learner-course-grid">
            {filtered.map((course) => {
              const enrollment = enrollmentStatus[course.id];
              const label = statusLabel[enrollment ?? "available"] ?? enrollment ?? "Available";
              const completed = enrollment === "completed";
              const action = completed ? "Review course" : enrollment === "pending_approval" ? "View request" : enrollment === "waitlisted" ? "View waitlist" : enrollment === "rejected" ? "Request again" : enrollment ? "Continue learning" : course.enrollment_policy === "assignment_only" ? "View course" : course.enrollment_policy === "approval" ? "Request access" : "Explore course";
              return (
                <Link className="learner-course-card" href={"/dashboard/catalog/" + course.id} key={course.id}>
                  <div className="learner-course-icon"><BookOpenCheck size={20} aria-hidden="true" /></div>
                  <div className="learner-course-main">
                    <div className="learner-course-meta">
                      <span className={completed ? "status-badge success" : enrollment ? "status-badge warning" : "status-badge muted"}>{label}</span>
                      <span>{course.visibility === "private" ? "Assigned course" : course.enrollment_policy === "assignment_only" ? "Assignment only" : course.enrollment_policy === "approval" ? "Approval required" : "Self enrollment"}</span>
                    </div>
                    <h3>{course.title}</h3>
                    <p>{course.description || "No course description provided."}</p>
                    <div className="learner-course-footer">
                      <span><Clock3 size={13} aria-hidden="true" /> {course.estimated_minutes ?? "—"} min</span>
                      <span>{enrollment ? <CheckCircle2 size={13} aria-hidden="true" /> : <Sparkles size={13} aria-hidden="true" />} {action}</span>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        ) : (
          <div className="empty-state" role="status">
            <Search size={24} aria-hidden="true" />
            <h3>{courses.length ? "No matching courses" : "No courses available"}</h3>
            <p>{courses.length ? "Try a broader topic or switch the learning scope." : "Published courses will appear here when available to your organization."}</p>
          </div>
        )}
      </div>
    </section>
  );
}
