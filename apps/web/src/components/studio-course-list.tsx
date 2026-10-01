"use client";
import Link from "next/link";
import { useMemo, useState } from "react";
type Course = { id: string; title: string; description?: string | null; status: string; slug: string; estimated_minutes?: number | null; visibility?: string };
export function StudioCourseList({ courses }: { courses: Course[] }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const filtered = useMemo(() => courses.filter(course =>
    (status === "all" || course.status === status) &&
    (!query.trim() || `${course.title} ${course.slug} ${course.description ?? ""}`.toLowerCase().includes(query.trim().toLowerCase()))
  ), [courses, query, status]);
  return <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Library</span><h2>Courses</h2></div><span className="section-meta">{filtered.length} of {courses.length}</span></div>
    <div className="form-grid"><label className="form-field"><span>Search courses</span><input type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Title, slug, or topic" /></label>
      <label className="form-field"><span>Status</span><select value={status} onChange={event => setStatus(event.target.value)}><option value="all">All statuses</option><option value="draft">Draft</option><option value="published">Published</option></select></label></div>
    {filtered.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th scope="col">Course</th><th scope="col">Status</th><th scope="col">Visibility</th><th scope="col">Duration</th><th scope="col">Action</th></tr></thead><tbody>{filtered.map(course =>
      <tr key={course.id}><td><strong>{course.title}</strong><small>{course.description || course.slug}</small></td><td><span className="status-badge">{course.status}</span></td><td>{course.visibility ?? "tenant"}</td><td>{course.estimated_minutes ? `${course.estimated_minutes} min` : "—"}</td><td><Link href={`/dashboard/course-studio/${course.id}`} className="text-link">Open studio →</Link></td></tr>
    )}</tbody></table></div> : <div className="empty-state"><h3>{courses.length ? "No matching courses" : "No courses yet"}</h3><p>{courses.length ? "Try another search or status." : "Create a draft course to begin authoring."}</p></div>}
  </section>;
}
