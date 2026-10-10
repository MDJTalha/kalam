"use client";

import Link from "next/link";
import { BookOpenCheck, CheckCircle2, Clock3, Search, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";

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
  enrollment_status?: string | null;
};

type Props = {
  courses: Course[];
  total: number;
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

export function LearnerCatalogBrowser({ courses: initialCourses, total: initialTotal }: Props) {
  const [query, setQuery] = useState("");
  const [scope, setScope] = useState<"all" | "learning" | "available">("all");
  const [courses, setCourses] = useState(initialCourses);
  const [total, setTotal] = useState(initialTotal);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const firstRender = useRef(true);
  const activeFilter = useRef({ query, scope });

  useEffect(() => {
    activeFilter.current = { query, scope };
    if (firstRender.current) { firstRender.current = false; return; }
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setLoading(true); setError("");
      try {
        const params = new URLSearchParams({ page: "1", page_size: "24", q: query, scope });
        const response = await fetch(`/api/v1/courses/page?${params}`, { signal: controller.signal, cache: "no-store" });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.detail || "Catalog search failed.");
        setCourses(Array.isArray(data.items) ? data.items : []); setTotal(Number(data.total) || 0); setPage(1);
      } catch (reason) {
        if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "Catalog search failed.");
      } finally { if (!controller.signal.aborted) setLoading(false); }
    }, 250);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [query, scope]);

  async function loadMore() {
    if (loading || courses.length >= total) return;
    const filterAtRequest = JSON.stringify(activeFilter.current);
    setLoading(true); setError("");
    try {
      const nextPage = page + 1;
      const params = new URLSearchParams({ page: String(nextPage), page_size: "24", q: query, scope });
      const response = await fetch(`/api/v1/courses/page?${params}`, { cache: "no-store" });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "More courses could not be loaded.");
      if (filterAtRequest !== JSON.stringify(activeFilter.current)) return;
      setCourses(current => [...current, ...(Array.isArray(data.items) ? data.items : [])]);
      setTotal(Number(data.total) || 0); setPage(nextPage);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "More courses could not be loaded."); }
    finally { setLoading(false); }
  }


  return (
    <section className="learner-catalog" aria-labelledby="learner-catalog-title">
      <div className="learner-catalog-heading">
        <div>
          <span className="eyebrow">Find your next capability</span>
          <h2 id="learner-catalog-title">Learning catalog</h2>
          <p>Discover assigned and self-service learning in one place, with progress-aware status and clear next actions.</p>
        </div>
        <div className="learner-catalog-stat" aria-label="Catalog summary">
            <strong>{total}</strong>
            <span>Matching published courses</span>
        </div>
      </div>

      <div className="learner-catalog-toolbar">
        <label className="learner-search">
          <Search size={16} aria-hidden="true" />
          <span className="sr-only">Search courses</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by title or description"
            type="search"
          />
        </label>
        <div className="learner-scope-tabs" role="group" aria-label="Filter courses by learning status">
          <button type="button" className={scope === "all" ? "active" : ""} onClick={() => setScope("all")} aria-pressed={scope === "all"}>All</button>
          <button type="button" className={scope === "learning" ? "active" : ""} onClick={() => setScope("learning")} aria-pressed={scope === "learning"}>My learning</button>
          <button type="button" className={scope === "available" ? "active" : ""} onClick={() => setScope("available")} aria-pressed={scope === "available"}>Available</button>
        </div>
      </div>

      <div className="learner-catalog-results" aria-live="polite">
        <div className="learner-results-meta">
          <span>{courses.length} of {total} {total === 1 ? "course" : "courses"} shown{loading ? " · Updating…" : ""}</span>
          {query && <span>Search: “{query}”</span>}
        </div>
        {courses.length ? (
          <div className="learner-course-grid">
            {courses.map((course) => {
              const enrollment = course.enrollment_status ?? undefined;
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
            <h3>{query || scope !== "all" ? "No matching courses" : "No courses available"}</h3>
            <p>{query || scope !== "all" ? "Try a broader search or switch the learning scope." : "Published courses will appear here when available to your organization."}</p>
          </div>
        )}
        {error && <p className="form-error" role="alert">{error}</p>}
        {courses.length < total && <button className="button button-secondary" type="button" disabled={loading} onClick={() => void loadMore()}>{loading ? "Loading…" : `Load more (${courses.length} of ${total})`}</button>}
      </div>
    </section>
  );
}
