"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

type Course = { id: string; title: string; description?: string | null; status: string; slug: string; estimated_minutes?: number | null; visibility?: string };

export function StudioCourseList({ courses: initialCourses, total: initialTotal }: { courses: Course[]; total: number }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [courses, setCourses] = useState(initialCourses);
  const [total, setTotal] = useState(initialTotal);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const firstRender = useRef(true);
  const activeFilter = useRef({ query, status });

  useEffect(() => {
    activeFilter.current = { query, status };
    if (firstRender.current) { firstRender.current = false; return; }
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setLoading(true); setError("");
      try {
        const params = new URLSearchParams({ page: "1", page_size: "25", manage: "true", q: query, status });
        const response = await fetch(`/api/v1/courses/page?${params}`, { signal: controller.signal, cache: "no-store" });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.detail || "Course search failed.");
        setCourses(Array.isArray(data.items) ? data.items : []); setTotal(Number(data.total) || 0); setPage(1);
      } catch (reason) {
        if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "Course search failed.");
      } finally { if (!controller.signal.aborted) setLoading(false); }
    }, 250);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [query, status]);

  async function loadMore() {
    if (loading || courses.length >= total) return;
    const filterAtRequest = JSON.stringify(activeFilter.current);
    setLoading(true); setError("");
    try {
      const nextPage = page + 1;
      const params = new URLSearchParams({ page: String(nextPage), page_size: "25", manage: "true", q: query, status });
      const response = await fetch(`/api/v1/courses/page?${params}`, { cache: "no-store" });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "More courses could not be loaded.");
      if (filterAtRequest !== JSON.stringify(activeFilter.current)) return;
      setCourses(current => [...current, ...(Array.isArray(data.items) ? data.items : [])]);
      setTotal(Number(data.total) || 0); setPage(nextPage);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "More courses could not be loaded."); }
    finally { setLoading(false); }
  }

  return <section className="data-panel">
    <div className="section-heading compact"><div><span className="eyebrow">Library</span><h2>Courses</h2></div><span className="section-meta">{courses.length} of {total}{loading ? " · Updating…" : ""}</span></div>
    <div className="form-grid">
      <label className="form-field"><span>Search courses</span><input type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Title, slug, or description" /></label>
      <label className="form-field"><span>Status</span><select value={status} onChange={event => setStatus(event.target.value)}><option value="all">All statuses</option><option value="draft">Draft</option><option value="review">In review</option><option value="published">Published</option><option value="archived">Archived</option></select></label>
    </div>
    {courses.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th scope="col">Course</th><th scope="col">Status</th><th scope="col">Visibility</th><th scope="col">Duration</th><th scope="col">Action</th></tr></thead><tbody>{courses.map(course =>
      <tr key={course.id}><td><strong>{course.title}</strong><small>{course.description || course.slug}</small></td><td><span className="status-badge">{course.status}</span></td><td>{course.visibility ?? "tenant"}</td><td>{course.estimated_minutes ? `${course.estimated_minutes} min` : "—"}</td><td><Link href={`/dashboard/course-studio/${course.id}`} className="text-link">Open studio →</Link></td></tr>
    )}</tbody></table></div> : <div className="empty-state"><h3>{query || status !== "all" ? "No matching courses" : "No courses yet"}</h3><p>{query || status !== "all" ? "Try another search or status." : "Create a draft course to begin authoring."}</p></div>}
    {error && <p className="form-error" role="alert">{error}</p>}
    {courses.length < total && <button type="button" className="button button-secondary" disabled={loading} onClick={() => void loadMore()}>{loading ? "Loading…" : `Load more (${courses.length} of ${total})`}</button>}
  </section>;
}
