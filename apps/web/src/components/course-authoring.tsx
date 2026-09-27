"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { BookOpenCheck, Check, Plus, Send, Sparkles } from "lucide-react";
import { Notice, SectionCard } from "./ui";
import { CourseEnrollmentPanel } from "./course-enrollment-panel";
import { CourseCurriculumEditor } from "./course-curriculum-editor";

type Person = { id: string; first_name: string; last_name: string; email: string; is_active: boolean };
type Category = { id: string; name: string; description?: string | null; active: boolean };
type OrgUnit = { id: string; name: string; unit_type: string; code?: string | null };
type Course = {
  id: string;
  title: string;
  slug: string;
  description?: string | null;
  estimated_minutes?: number | null;
  status: string;
  category_id?: string | null;
  owner_id?: string | null;
  visibility?: "tenant" | "private";
  enrollment_policy?: "open" | "approval" | "assignment_only";
  capacity?: number | null;
  audience_org_units?: string[];
  tags?: string[];
  prerequisites?: string[];
};

type Props = { initial?: Course; mode: "create" | "build" };

export function CourseAuthoring({ initial, mode }: Props) {
  const router = useRouter();
  const [course, setCourse] = useState<Course | null>(initial ?? null);
  const [title, setTitle] = useState(initial?.title ?? "");
  const [slug, setSlug] = useState(initial?.slug ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [minutes, setMinutes] = useState(String(initial?.estimated_minutes ?? ""));
  const [categoryId, setCategoryId] = useState(initial?.category_id ?? "");
  const [ownerId, setOwnerId] = useState(initial?.owner_id ?? "");
  const [visibility, setVisibility] = useState<"tenant" | "private">(initial?.visibility ?? "tenant");
  const [enrollmentPolicy, setEnrollmentPolicy] = useState<"open" | "approval" | "assignment_only">(initial?.enrollment_policy ?? "open");
  const [capacity, setCapacity] = useState(String(initial?.capacity ?? ""));
  const [audienceOrgUnits, setAudienceOrgUnits] = useState<string[]>(initial?.audience_org_units ?? []);
  const [tags, setTags] = useState((initial?.tags ?? []).join(", "));
  const [prerequisites, setPrerequisites] = useState<string[]>(initial?.prerequisites ?? []);
  const [people, setPeople] = useState<Person[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [orgUnits, setOrgUnits] = useState<OrgUnit[]>([]);
  const [availableCourses, setAvailableCourses] = useState<Course[]>([]);
  const [newCategory, setNewCategory] = useState("");
  const [message, setMessage] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function request(url: string, init: RequestInit = {}) {
    const response = await fetch(url, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init.headers || {}) },
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "The action could not be completed.");
    return data;
  }

  useEffect(() => {
    let active = true;
    async function loadGovernance() {
      try {
        const [categoryResponse, courseResponse, orgResponse, peopleResponse, meResponse] = await Promise.all([
          fetch("/api/lms/courses/categories"),
          fetch("/api/lms/courses?manage=true"),
          fetch("/api/lms/courses/audience-options"),
          fetch("/api/lms/people"),
          fetch("/api/lms/auth/me"),
        ]);
        const [categoryData, courseData, orgUnitData, peopleData, meData] = await Promise.all([
          categoryResponse.json().catch(() => []),
          courseResponse.json().catch(() => []),
          orgResponse.json().catch(() => []),
          peopleResponse.json().catch(() => []),
          meResponse.json().catch(() => null),
        ]);
        if (!active) return;
        if (Array.isArray(categoryData)) setCategories(categoryData);
        if (Array.isArray(courseData)) setAvailableCourses(courseData);
        if (Array.isArray(orgUnitData)) setOrgUnits(orgUnitData);
        if (Array.isArray(peopleData)) setPeople(peopleData);
        if (!ownerId && meData?.id) setOwnerId(meData.id);
      } catch {
        // Governance controls remain usable with the current course owner as the fallback.
      }
    }
    void loadGovernance();
    return () => { active = false; };
  }, [ownerId]);

  const prerequisiteOptions = useMemo(
    () => availableCourses.filter((item) => item.id !== course?.id),
    [availableCourses, course?.id],
  );

  function governancePayload() {
    return {
      category_id: categoryId || null,
      owner_id: ownerId || null,
      visibility,
      tags: tags.split(",").map((item) => item.trim()).filter(Boolean),
      prerequisites,
      enrollment_policy: enrollmentPolicy,
      capacity: capacity ? Number(capacity) : null,
      audience_org_units: audienceOrgUnits,
    };
  }

  async function createCourse(event: FormEvent) {
    event.preventDefault();
    setBusy(true); setMessage(null);
    try {
      const data = await request("/api/lms/courses", {
        method: "POST",
        body: JSON.stringify({
          title,
          slug,
          description: description || null,
          estimated_minutes: minutes ? Number(minutes) : null,
          ...governancePayload(),
        }),
      });
      setCourse(data);
      setCategoryId(data.category_id ?? "");
      setOwnerId(data.owner_id ?? "");
      setVisibility(data.visibility ?? "tenant");
      setEnrollmentPolicy(data.enrollment_policy ?? "open");
      setCapacity(String(data.capacity ?? ""));
      setAudienceOrgUnits(data.audience_org_units ?? []);
      setTags((data.tags ?? []).join(", "));
      setPrerequisites(data.prerequisites ?? []);
      router.push(`/dashboard/course-studio/${data.id}`);
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "Course creation failed" });
    } finally { setBusy(false); }
  }
  async function saveGovernance() {
    if (!course) return;
    setBusy(true); setMessage(null);
    try {
      const data = await request(`/api/lms/courses/${course.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          title,
          description: description || null,
          estimated_minutes: minutes ? Number(minutes) : null,
          ...governancePayload(),
        }),
      });
      setCourse((current) => ({ ...current, ...data }));
      setMessage({ kind: "success", text: "Course governance and details saved." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "Save failed" });
    } finally { setBusy(false); }
  }

  async function createCategory() {
    if (!newCategory.trim()) return;
    setBusy(true); setMessage(null);
    try {
      const data = await request("/api/lms/courses/categories", {
        method: "POST",
        body: JSON.stringify({ name: newCategory.trim() }),
      });
      setCategories((current) => [...current, data].sort((a, b) => a.name.localeCompare(b.name)));
      setCategoryId(data.id);
      setNewCategory("");
      setMessage({ kind: "success", text: "Category created and selected." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "Category creation failed" });
    } finally { setBusy(false); }
  }

  async function publish() {
    if (!course) return; setBusy(true); setMessage(null);
    try {
      const data = await request(`/api/lms/courses/${course.id}/publish`, { method: "POST" });
      setCourse((current) => current ? { ...current, status: data.status } : current);
      setMessage({ kind: "success", text: "Course published and available to authorized learners." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "Publish failed" });
    } finally { setBusy(false); }
  }

  function togglePrerequisite(id: string) {
    setPrerequisites((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  }

  function toggleAudienceOrgUnit(id: string) {
    setAudienceOrgUnits((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  }
  const governanceFields = <SectionCard eyebrow="Catalog governance" title="Ownership & discoverability" meta="Controlled by courses.manage">
    <div className="form-grid">
      {course && <><label className="form-field"><span>Course title</span><input required minLength={3} value={title} onChange={event => setTitle(event.target.value)} /></label>
        <label className="form-field"><span>Estimated minutes</span><input type="number" min={1} value={minutes} onChange={event => setMinutes(event.target.value)} /></label>
        <label className="form-field full"><span>Description</span><textarea rows={3} value={description} onChange={event => setDescription(event.target.value)} /></label></>}
      <label className="form-field">
        <span>Category</span>
        <select value={categoryId} onChange={(event) => setCategoryId(event.target.value)}>
          <option value="">No category</option>
          {categories.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}
        </select>
      </label>
      <label className="form-field">
        <span>Owner</span>
        <select value={ownerId} onChange={(event) => setOwnerId(event.target.value)}>
          <option value="">Current administrator</option>
          {people.filter((item) => item.is_active).map((item) => (
            <option value={item.id} key={item.id}>{item.first_name} {item.last_name} · {item.email}</option>
          ))}
        </select>
      </label>
      <label className="form-field">
        <span>Visibility</span>
        <select value={visibility} onChange={(event) => setVisibility(event.target.value as "tenant" | "private")}>
          <option value="tenant">Tenant catalog — discoverable to learners</option>
          <option value="private">Private — direct/enrolled access only</option>
        </select>
      </label>
      <label className="form-field">
        <span>Enrollment policy</span>
        <select value={enrollmentPolicy} onChange={(event) => setEnrollmentPolicy(event.target.value as "open" | "approval" | "assignment_only")}>
          <option value="open">Open self-enrollment</option>
          <option value="approval">Request approval</option>
          <option value="assignment_only">Assignment only</option>
        </select>
      </label>
      <label className="form-field">
        <span>Capacity</span>
        <input type="number" min={1} value={capacity} onChange={(event) => setCapacity(event.target.value)} placeholder="Unlimited" />
      </label>
      <label className="form-field">
        <span>Tags</span>
        <input value={tags} onChange={(event) => setTags(event.target.value)} placeholder="leadership, compliance, onboarding" />
      </label>
      <div className="form-field full">
        <span>Audience targeting</span>
        <div className="tag-list">
          {orgUnits.map((unit) => (
            <label className="tag" key={unit.id}>
              <input type="checkbox" checked={audienceOrgUnits.includes(unit.id)} onChange={() => toggleAudienceOrgUnit(unit.id)} />
              {unit.name}{unit.code ? " · " + unit.code : ""}
            </label>
          ))}
          {!orgUnits.length && <small>All tenant learners are eligible when no audience is selected.</small>}
        </div>
      </div>
      <div className="form-field full">
        <span>Prerequisites</span>
        <div className="tag-list">
          {prerequisiteOptions.map((item) => (
            <label className="tag" key={item.id}>
              <input type="checkbox" checked={prerequisites.includes(item.id)} onChange={() => togglePrerequisite(item.id)} />
              {item.title}
            </label>
          ))}
          {!prerequisiteOptions.length && <small>No other courses are available as prerequisites yet.</small>}
        </div>
      </div>
      <div className="form-field full">
        <span>Create category</span>
        <div className="inline-form"><input aria-label="New category name" value={newCategory} onChange={(event) => setNewCategory(event.target.value)} placeholder="e.g. Leadership & Management" /><button type="button" className="button button-secondary" onClick={() => void createCategory()} disabled={busy || !newCategory.trim()}><Plus size={15}/> Add category</button></div>
      </div>
    </div>
    {course && <div className="form-actions"><button className="button button-secondary" onClick={() => void saveGovernance()} disabled={busy}><Check size={15}/> Save governance</button></div>}
  </SectionCard>;

  if (mode === "create" && !course) return <SectionCard eyebrow="Course authoring" title="Create a course" meta="Draft → governance → curriculum">
    <form className="studio-form" onSubmit={createCourse}>
      <div className="form-grid">
        <label className="form-field"><span>Course title</span><input value={title} onChange={(e) => setTitle(e.target.value)} minLength={3} required /></label>
        <label className="form-field"><span>Slug</span><input value={slug} onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "-"))} required /></label>
        <label className="form-field"><span>Estimated minutes</span><input type="number" min={1} value={minutes} onChange={(e) => setMinutes(e.target.value)} /></label>
        <label className="form-field full"><span>Description</span><textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={5} /></label>
      </div>
      {governanceFields}
      {message && <Notice kind={message.kind}>{message.text}</Notice>}
      <button className="button button-primary" disabled={busy}><Plus size={16}/>{busy ? "Creating…" : "Create draft"}</button>
    </form>
  </SectionCard>;

  return <div className="studio-grid">
    <div>
      <SectionCard eyebrow="Course studio" title={course?.title ?? title} meta={<span className="tag">{course?.status ?? "draft"}</span>}
        actions={course && course.status !== "published" ? <button className="button button-primary" onClick={() => void publish()} disabled={busy}><Send size={15}/> Publish</button> : <span className="status-badge success">Published</span>}>
        {message && <Notice kind={message.kind}>{message.text}</Notice>}
        <div className="studio-flow"><div className="studio-step complete"><Check size={14}/> Course shell</div><div className="studio-line"/><div className="studio-step complete"><Check size={14}/> Governance</div><div className="studio-line"/><div className="studio-step"><BookOpenCheck size={14}/> Curriculum</div><div className="studio-line"/><div className="studio-step"><Sparkles size={14}/> Readiness</div></div>
        <div className="detail-grid"><span><b>Slug</b>{course?.slug ?? slug}</span><span><b>Duration</b>{course?.estimated_minutes ?? minutes} min</span><span><b>Visibility</b>{course?.visibility ?? visibility}</span><span><b>Tags</b>{course?.tags?.join(", ") || tags || "—"}</span></div>
      </SectionCard>
      {governanceFields}
    </div>
    {course && <CourseCurriculumEditor courseId={course.id} />}    {course && <div className="studio-wide"><CourseEnrollmentPanel courseId={course.id} courseTitle={course.title} /></div>}
  </div>;
}