"use client";

import { FormEvent, useMemo, useState } from "react";
import { BookOpenCheck, CheckCircle2, ChevronDown, ChevronUp, Edit3, Eye, History, Plus, Save, Send, Trash2, X } from "lucide-react";

type Lesson = { id: string; title: string; content_type: string; content: Record<string, unknown>; position: number };
type Module = { id: string; title: string; description?: string | null; position: number; lessons: Lesson[] };
type Course = { id: string; title: string; slug: string; description?: string | null; status: string; estimated_minutes?: number | null; modules: Module[] };
type Version = { id: string; version_number: number; title: string; content_type: string; content: Record<string, unknown>; change_note?: string | null; created_at: string };

export function CourseStudio({ initialCourse }: { initialCourse: Course }) {
  const [course, setCourse] = useState(initialCourse);
  const [title, setTitle] = useState(initialCourse.title);
  const [description, setDescription] = useState(initialCourse.description ?? "");
  const [minutes, setMinutes] = useState(String(initialCourse.estimated_minutes ?? ""));
  const [moduleTitle, setModuleTitle] = useState("");
  const [lesson, setLesson] = useState({ moduleId: "", title: "", content: "", type: "rich_text", changeNote: "" });
  const [editingModule, setEditingModule] = useState<{ id: string; title: string; description: string } | null>(null);
  const [editingLesson, setEditingLesson] = useState<{ moduleId: string; id: string; title: string; content: string; type: string; changeNote: string } | null>(null);
  const [versions, setVersions] = useState<Version[]>([]);
  const [versionTarget, setVersionTarget] = useState<{ moduleId: string; lessonId: string } | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewLessonId, setPreviewLessonId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const publishIssues = useMemo(() => {
    const issues: string[] = [];
    if (!title.trim()) issues.push("Add a course title.");
    if (!course.modules.length) issues.push("Add at least one module.");
    course.modules.forEach((module) => {
      if (!module.title.trim()) issues.push("Module " + module.position + " needs a title.");
      if (!module.lessons.length) issues.push("Module \"" + module.title + "\" needs at least one lesson.");
      module.lessons.forEach((item) => {
        const value = typeof item.content?.body === "string" ? item.content.body : typeof item.content?.url === "string" ? item.content.url : "";
        if (!value.trim()) issues.push("Lesson \"" + item.title + "\" needs content.");
      });
    });
    return issues;
  }, [course.modules, title]);

  async function request<T = Record<string, unknown>>(url: string, init: RequestInit = {}) {
    const response = await fetch(url, { ...init, headers: { "Content-Type": "application/json", ...(init.headers || {}) } });
    const data = await response.json().catch(() => ({} as T));
    if (!response.ok) throw new Error(typeof data === "object" && data && "detail" in data ? String((data as { detail?: unknown }).detail) : "The action could not be completed.");
    return data as T;
  }

  async function refreshCourse() {
    const data = await request<Course>("/api/lms/courses/" + course.id);
    setCourse(data);
    setTitle(data.title);
    setDescription(data.description ?? "");
    setMinutes(String(data.estimated_minutes ?? ""));
  }

  function clearState() { setError(""); setMessage(""); }

  async function saveCourse(event: FormEvent) {
    event.preventDefault(); setBusy(true); clearState();
    try { await request("/api/lms/courses/" + course.id, { method: "PATCH", body: JSON.stringify({ title, description: description || null, estimated_minutes: minutes ? Number(minutes) : null }) }); await refreshCourse(); setMessage("Course details saved."); }
    catch (e) { setError(e instanceof Error ? e.message : "Save failed."); } finally { setBusy(false); }
  }

  async function addModule(event: FormEvent) {
    event.preventDefault(); if (!moduleTitle.trim()) return; setBusy(true); clearState();
    try { await request("/api/lms/courses/" + course.id + "/modules", { method: "POST", body: JSON.stringify({ title: moduleTitle.trim(), position: course.modules.length + 1 }) }); setModuleTitle(""); await refreshCourse(); setMessage("Module added."); }
    catch (e) { setError(e instanceof Error ? e.message : "Unable to add module."); } finally { setBusy(false); }
  }


  async function addLesson(event: FormEvent) {
    event.preventDefault(); if (!lesson.moduleId || !lesson.title.trim()) return; setBusy(true); clearState();
    const content = lesson.type === "rich_text" ? { body: lesson.content } : { url: lesson.content };
    try { await request("/api/lms/courses/" + course.id + "/modules/" + lesson.moduleId + "/lessons", { method: "POST", body: JSON.stringify({ title: lesson.title.trim(), content_type: lesson.type, content, position: (course.modules.find(item => item.id === lesson.moduleId)?.lessons.length ?? 0) + 1, change_note: lesson.changeNote || null }) }); await refreshCourse(); setLesson({ moduleId: lesson.moduleId, title: "", content: "", type: "rich_text", changeNote: "" }); setMessage("Lesson added."); }
    catch (e) { setError(e instanceof Error ? e.message : "Unable to add lesson."); } finally { setBusy(false); }
  }

  async function updateModule(event: FormEvent) {
    event.preventDefault(); if (!editingModule) return; setBusy(true); clearState();
    try { await request("/api/lms/courses/" + course.id + "/modules/" + editingModule.id, { method: "PATCH", body: JSON.stringify({ title: editingModule.title.trim(), description: editingModule.description || null }) }); setEditingModule(null); await refreshCourse(); setMessage("Module updated."); }
    catch (e) { setError(e instanceof Error ? e.message : "Unable to update module."); } finally { setBusy(false); }
  }

  async function updateLesson(event: FormEvent) {
    event.preventDefault(); if (!editingLesson) return; setBusy(true); clearState();
    const content = editingLesson.type === "rich_text" ? { body: editingLesson.content } : { url: editingLesson.content };
    try {
      await request("/api/lms/courses/" + course.id + "/modules/" + editingLesson.moduleId + "/lessons/" + editingLesson.id, {
        method: "PATCH", body: JSON.stringify({ title: editingLesson.title.trim(), content_type: editingLesson.type, content, change_note: editingLesson.changeNote || "Lesson content updated" })
      });
      setEditingLesson(null); await refreshCourse(); setMessage("Lesson updated and versioned.");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to update lesson."); } finally { setBusy(false); }
  }

  async function deleteModule(moduleId: string, moduleTitle: string) {
    if (!window.confirm("Delete module \"" + moduleTitle + "\" and all of its lessons? This action cannot be undone.")) return;
    setBusy(true); clearState();
    try { await request("/api/lms/courses/" + course.id + "/modules/" + moduleId, { method: "DELETE" }); await refreshCourse(); setMessage("Module deleted."); }
    catch (e) { setError(e instanceof Error ? e.message : "Unable to delete module."); } finally { setBusy(false); }
  }

  async function deleteLesson(moduleId: string, lessonId: string, lessonTitle: string) {
    if (!window.confirm("Delete lesson \"" + lessonTitle + "\"? This action cannot be undone.")) return;
    setBusy(true); clearState();
    try { await request("/api/lms/courses/" + course.id + "/modules/" + moduleId + "/lessons/" + lessonId, { method: "DELETE" }); await refreshCourse(); setMessage("Lesson deleted."); }
    catch (e) { setError(e instanceof Error ? e.message : "Unable to delete lesson."); } finally { setBusy(false); }
  }

  async function moveModule(module: Module, direction: -1 | 1) {
    const ordered = [...course.modules].sort((a, b) => a.position - b.position);
    const index = ordered.findIndex(item => item.id === module.id); const target = ordered[index + direction];
    if (!target) return; setBusy(true); clearState();
    try {
      await request("/api/lms/courses/" + course.id + "/modules/" + module.id + "/position", { method: "PATCH", body: JSON.stringify({ position: target.position }) });
      await refreshCourse(); setMessage("Module order updated.");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to reorder module."); } finally { setBusy(false); }
  }

  async function moveLesson(module: Module, lesson: Lesson, direction: -1 | 1) {
    const ordered = [...module.lessons].sort((a, b) => a.position - b.position);
    const index = ordered.findIndex(item => item.id === lesson.id); const target = ordered[index + direction];
    if (!target) return; setBusy(true); clearState();
    try {
      await request("/api/lms/courses/" + course.id + "/modules/" + module.id + "/lessons/" + lesson.id + "/position", { method: "PATCH", body: JSON.stringify({ position: target.position }) });
      await refreshCourse(); setMessage("Lesson order updated.");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to reorder lesson."); } finally { setBusy(false); }
  }

  async function openVersions(moduleId: string, lessonId: string) {
    clearState(); setVersionTarget({ moduleId, lessonId }); setVersions([]);
    try { const data = await request<Version[]>("/api/lms/courses/" + course.id + "/modules/" + moduleId + "/lessons/" + lessonId + "/versions"); setVersions(data); }
    catch (e) { setError(e instanceof Error ? e.message : "Unable to load version history."); }
  }

  async function restoreVersion(version: Version) {
    if (!versionTarget || !window.confirm("Restore version " + version.version_number + " of this lesson? A new version will be recorded.")) return;
    setBusy(true); clearState();
    try {
      await request("/api/lms/courses/" + course.id + "/modules/" + versionTarget.moduleId + "/lessons/" + versionTarget.lessonId + "/versions/" + version.version_number + "/restore", { method: "POST" });
      setVersionTarget(null); setVersions([]); await refreshCourse(); setMessage("Lesson version restored.");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to restore version."); } finally { setBusy(false); }
  }

  async function publish() {
    if (publishIssues.length) { setError("Resolve " + publishIssues.length + " publish-readiness issue(s) before publishing."); return; }
    setBusy(true); clearState();
    try { await request("/api/lms/courses/" + course.id + "/publish", { method: "POST" }); await refreshCourse(); setMessage("Course published and available to learners."); }
    catch (e) { setError(e instanceof Error ? e.message : "Publishing failed."); } finally { setBusy(false); }
  }

  function preview() {
    const firstLesson = course.modules.flatMap(item => item.lessons).find(() => true);
    setPreviewLessonId(firstLesson?.id ?? null); setPreviewOpen(true);
  }

  const previewLesson = course.modules.flatMap(item => item.lessons).find(item => item.id === previewLessonId) ?? null;
  const contentValue = (item: Lesson) => typeof item.content?.body === "string" ? item.content.body : typeof item.content?.url === "string" ? item.content.url : "";

  return (
    <div className="course-studio-workspace">
      <div className="data-panel">
        <div className="page-heading">
          <div><span className="eyebrow">Controlled authoring</span><h2>{course.title}</h2><p>Create, validate and publish learner content without leaving the governed authoring workspace.</p></div>
          <div className="page-heading-actions"><span className="status-badge">{course.status}</span><button className="button button-secondary" type="button" onClick={preview} disabled={!course.modules.length}><Eye size={15}/> Preview learner view</button><button className="button button-primary" type="button" onClick={() => void publish()} disabled={busy || course.status === "published"}><Send size={15}/> Publish</button></div>
        </div>
        {error && <div className="form-error" role="alert">{error}</div>}
        {message && <div className="form-success" role="status"><CheckCircle2 size={14}/>{message}</div>}
        {publishIssues.length ? <div className="callout warning"><BookOpenCheck size={16}/><div><strong>Publish readiness</strong><p>{publishIssues.slice(0, 3).join(" · ")}{publishIssues.length > 3 ? " · +" + (publishIssues.length - 3) + " more" : ""}</p></div></div> : <div className="callout success"><CheckCircle2 size={16}/><div><strong>Ready to publish</strong><p>Required structure and content checks are clear. Server-side validation remains the final gate.</p></div></div>}

        <form className="form-grid" onSubmit={saveCourse}>
          <label className="form-field"><span>Course title</span><input value={title} onChange={e => setTitle(e.target.value)} required /></label>
          <label className="form-field"><span>Duration (minutes)</span><input type="number" min="1" value={minutes} onChange={e => setMinutes(e.target.value)} /></label>
          <label className="form-field full"><span>Description</span><textarea value={description} onChange={e => setDescription(e.target.value)} /></label>
          <div className="form-actions full"><button className="button button-secondary" disabled={busy}><Save size={15}/> Save course</button></div>
        </form>
        <div className="section-heading compact"><div><span className="eyebrow">Curriculum architecture</span><h2>Modules & lessons</h2></div><span className="meta-note">{course.modules.length} module(s)</span></div>
        <div className="compact-list">
          {course.modules.map((module, moduleIndex) => <section className="curriculum-module" key={module.id}>
            <div className="curriculum-heading">
              <span>{String(module.position).padStart(2, "0")}</span>
              <div><strong>{module.title}</strong><small>{module.lessons.length} lesson(s){module.description ? " · " + module.description : ""}</small></div>
              <div className="button-row">
                <button className="icon-button" type="button" aria-label="Move module up" disabled={busy || moduleIndex === 0} onClick={() => void moveModule(module, -1)}><ChevronUp size={15}/></button>
                <button className="icon-button" type="button" aria-label="Move module down" disabled={busy || moduleIndex === course.modules.length - 1} onClick={() => void moveModule(module, 1)}><ChevronDown size={15}/></button>
                <button className="icon-button" type="button" aria-label="Edit module" onClick={() => setEditingModule({ id: module.id, title: module.title, description: module.description ?? "" })}><Edit3 size={15}/></button>
                <button className="icon-button danger" type="button" aria-label="Delete module" disabled={busy} onClick={() => void deleteModule(module.id, module.title)}><Trash2 size={15}/></button>
              </div>
            </div>
            {module.lessons.length ? <div className="compact-list">{module.lessons.map((item, lessonIndex) => <div className="compact-row course-studio-lesson" key={item.id}>
              <div><strong>{item.title}</strong><small>{item.content_type} · {contentValue(item) ? "content configured" : "content missing"}</small></div>
              <div className="button-row">
                <button className="icon-button" type="button" aria-label="Move lesson up" disabled={busy || lessonIndex === 0} onClick={() => void moveLesson(module, item, -1)}><ChevronUp size={14}/></button>
                <button className="icon-button" type="button" aria-label="Move lesson down" disabled={busy || lessonIndex === module.lessons.length - 1} onClick={() => void moveLesson(module, item, 1)}><ChevronDown size={14}/></button>
                <button className="icon-button" type="button" aria-label="Edit lesson" onClick={() => setEditingLesson({ moduleId: module.id, id: item.id, title: item.title, content: contentValue(item), type: item.content_type, changeNote: "" })}><Edit3 size={14}/></button>
                <button className="icon-button" type="button" aria-label="Version history" onClick={() => void openVersions(module.id, item.id)}><History size={14}/></button>
                <button className="icon-button danger" type="button" aria-label="Delete lesson" disabled={busy} onClick={() => void deleteLesson(module.id, item.id, item.title)}><Trash2 size={14}/></button>
              </div>
            </div>)}</div> : <div className="empty-state"><BookOpenCheck size={19}/><p>No lessons yet. Add the first learner-facing lesson from the authoring panel.</p></div>}
          </section>)}
          {!course.modules.length && <div className="empty-state"><BookOpenCheck size={25}/><h3>Build the first module</h3><p>Published courses require at least one module and one valid lesson.</p></div>}
        </div>

      </div>
      <aside className="data-panel">
        <div className="section-heading compact"><div><span className="eyebrow">Authoring controls</span><h2>Build content</h2></div></div>
        <form className="soft-panel" onSubmit={addModule}>
          <label className="form-field"><span>New module</span><input placeholder="e.g. Module 1 — Foundations" value={moduleTitle} onChange={e => setModuleTitle(e.target.value)} required /></label>
          <div className="form-actions"><button className="button button-primary" disabled={busy}><Plus size={15}/> Add module</button></div>
        </form>
        <form className="soft-panel course-studio-builder" onSubmit={addLesson}>
          <label className="form-field"><span>Module</span><select value={lesson.moduleId} onChange={e => setLesson({ ...lesson, moduleId: e.target.value })} required><option value="">Select module…</option>{course.modules.map(item => <option value={item.id} key={item.id}>{item.title}</option>)}</select></label>
          <label className="form-field"><span>Lesson title</span><input value={lesson.title} onChange={e => setLesson({ ...lesson, title: e.target.value })} required /></label>
          <label className="form-field"><span>Content type</span><select value={lesson.type} onChange={e => setLesson({ ...lesson, type: e.target.value })}><option value="rich_text">Rich text</option><option value="video">Video URL</option><option value="document">Document URL</option><option value="link">External link</option></select></label>
          <label className="form-field"><span>{lesson.type === "rich_text" ? "Learner content" : "Resource URL"}</span><textarea placeholder={lesson.type === "rich_text" ? "Write the learner-facing content." : "https://…"} value={lesson.content} onChange={e => setLesson({ ...lesson, content: e.target.value })} /></label>
          <label className="form-field"><span>Change note <small>(optional)</small></span><input value={lesson.changeNote} onChange={e => setLesson({ ...lesson, changeNote: e.target.value })} placeholder="Why this content changed" /></label>
          <div className="form-actions"><button className="button button-primary" disabled={busy || !course.modules.length}><Plus size={15}/> Add lesson</button></div>
        </form>
        <div className="callout"><Eye size={15}/><div><strong>Governed preview</strong><p>Draft content remains inside authoring until publishing passes server-side validation.</p></div></div>
        {editingModule ? <div className="course-studio-modal-inline"><div className="section-heading compact"><h3>Edit module</h3><button className="icon-button" type="button" onClick={() => setEditingModule(null)}><X size={15}/></button></div><form onSubmit={updateModule} className="form-stack"><label className="form-field"><span>Title</span><input value={editingModule.title} onChange={e => setEditingModule({ ...editingModule, title: e.target.value })} required /></label><label className="form-field"><span>Description</span><textarea value={editingModule.description} onChange={e => setEditingModule({ ...editingModule, description: e.target.value })} /></label><button className="button button-primary" disabled={busy}><Save size={15}/> Save module</button></form></div> : null}
        {editingLesson ? <div className="course-studio-modal-inline"><div className="section-heading compact"><h3>Edit lesson</h3><button className="icon-button" type="button" onClick={() => setEditingLesson(null)}><X size={15}/></button></div><form onSubmit={updateLesson} className="form-stack"><label className="form-field"><span>Title</span><input value={editingLesson.title} onChange={e => setEditingLesson({ ...editingLesson, title: e.target.value })} required /></label><label className="form-field"><span>Type</span><select value={editingLesson.type} onChange={e => setEditingLesson({ ...editingLesson, type: e.target.value })}><option value="rich_text">Rich text</option><option value="video">Video URL</option><option value="document">Document URL</option><option value="link">External link</option></select></label><label className="form-field"><span>{editingLesson.type === "rich_text" ? "Learner content" : "Resource URL"}</span><textarea value={editingLesson.content} onChange={e => setEditingLesson({ ...editingLesson, content: e.target.value })} /></label><label className="form-field"><span>Change note</span><input value={editingLesson.changeNote} onChange={e => setEditingLesson({ ...editingLesson, changeNote: e.target.value })} placeholder="Describe the authoring change" /></label><button className="button button-primary" disabled={busy}><Save size={15}/> Save lesson</button></form></div> : null}
      </aside>
      {versionTarget ? <div className="course-studio-overlay" role="dialog" aria-modal="true" aria-labelledby="course-version-title">
        <div className="course-studio-dialog">
          <div className="page-heading"><div><span className="eyebrow">Content governance</span><h2 id="course-version-title">Version history</h2><p>Restore any saved lesson version without losing the audit trail.</p></div><button className="icon-button" type="button" onClick={() => setVersionTarget(null)} aria-label="Close version history"><X size={16}/></button></div>
          {versions.length ? <div className="compact-list">{versions.map(version => <div className="compact-row" key={version.id}><div><strong>Version {version.version_number} · {version.title}</strong><small>{new Date(version.created_at).toLocaleString()} · {version.change_note || "No change note"}</small></div><button className="button button-secondary" type="button" disabled={busy} onClick={() => void restoreVersion(version)}>Restore</button></div>)}</div> : <div className="empty-state"><History size={22}/><h3>No versions available</h3><p>Version history will appear after the first saved content change.</p></div>}
        </div>
      </div> : null}
      {previewOpen ? <div className="course-studio-overlay" role="dialog" aria-modal="true" aria-labelledby="course-preview-title">
        <div className="course-studio-dialog course-studio-preview">
          <div className="page-heading"><div><span className="eyebrow">Learner preview</span><h2 id="course-preview-title">{course.title}</h2><p>{course.description || "Preview the learner-facing curriculum structure and current lesson content."}</p></div><button className="icon-button" type="button" onClick={() => setPreviewOpen(false)} aria-label="Close preview"><X size={16}/></button></div>
          <div className="course-preview-grid">
            <nav className="data-panel course-preview-nav" aria-label="Preview lessons">{course.modules.map(module => <div key={module.id}><strong>{module.position}. {module.title}</strong>{module.lessons.map(item => <button className={previewLessonId === item.id ? "lesson-nav-row selected" : "lesson-nav-row"} type="button" key={item.id} onClick={() => setPreviewLessonId(item.id)}>{item.title}<small>{item.content_type}</small></button>)}</div>)}</nav>
            <article className="data-panel course-preview-content">{previewLesson ? <><span className="eyebrow">{previewLesson.content_type}</span><h3>{previewLesson.title}</h3>{previewLesson.content_type === "rich_text" ? <p className="course-preview-body">{contentValue(previewLesson)}</p> : <a className="button button-primary" href={contentValue(previewLesson)} target="_blank" rel="noreferrer">{previewLesson.content_type === "video" ? "Open video" : previewLesson.content_type === "document" ? "Open document" : "Open resource"} </a>}</> : <div className="empty-state"><Eye size={22}/><h3>Select a lesson</h3><p>Choose a lesson from the preview navigation.</p></div>}</article>
          </div>
        </div>
      </div> : null}
    </div>
  );
}
