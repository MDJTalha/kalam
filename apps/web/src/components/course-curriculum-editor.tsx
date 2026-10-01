"use client";

import { FormEvent, useEffect, useState } from "react";
import { Check, Edit3, History, Plus, RotateCcw, Save } from "lucide-react";
import { Notice, SectionCard } from "./ui";
import { CourseContentBlockEditor } from "./course-content-block-editor";
type Lesson = {
  id: string;
  title: string;
  content_type: string;
  content: Record<string, unknown>;
  position: number;
};

type Module = {
  id: string;
  title: string;
  description?: string | null;
  position: number;
  lessons: Lesson[];
};

type Version = {
  id: string;
  lesson_id: string;
  version_number: number;
  title: string;
  content_type: string;
  content: Record<string, unknown>;
  change_note?: string | null;
  changed_by: string;
  created_at: string;
};

type Props = { courseId: string };

export function CourseCurriculumEditor({ courseId }: Props) {
  const [modules, setModules] = useState<Module[]>([]);
  const [moduleTitle, setModuleTitle] = useState("");
  const [selectedModule, setSelectedModule] = useState("");
  const [lessonTitle, setLessonTitle] = useState("");
  const [lessonType, setLessonType] = useState("rich_text");
  const [lessonBody, setLessonBody] = useState("");
  const [lessonContent, setLessonContent] = useState<Record<string, unknown>>({ version: 2, blocks: [] });
  const [editingLesson, setEditingLesson] = useState<Lesson | null>(null);
  const [changeNote, setChangeNote] = useState("");
  const [versions, setVersions] = useState<Record<string, Version[]>>({});
  const [editingModule, setEditingModule] = useState<string | null>(null);
  const [editingModuleTitle, setEditingModuleTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ kind: "success" | "error"; text: string } | null>(null);

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
    let cancelled = false;
    fetch("/api/lms/courses/" + courseId)
      .then(async (response) => {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.detail || "The action could not be completed.");
        if (!cancelled) {
          setModules(Array.isArray(data.modules) ? data.modules : []);
          setSelectedModule((current) => current || data.modules?.[0]?.id || "");
        }
      })
      .catch((error) => {
        if (!cancelled) setMessage({ kind: "error", text: error instanceof Error ? error.message : "Curriculum load failed." });
      });
    return () => { cancelled = true; };
  }, [courseId]);

  async function addModule(event: FormEvent) {
    event.preventDefault();
    if (!moduleTitle.trim()) return;
    setBusy(true);
    setMessage(null);
    try {
      const position = modules.length + 1;
      const data = await request("/api/lms/courses/" + courseId + "/modules", {
        method: "POST",
        body: JSON.stringify({ title: moduleTitle.trim(), position }),
      });
      const newModule = { ...data, lessons: [], position };
      setModules((current) => [...current, newModule]);
      setSelectedModule(data.id);
      setModuleTitle("");
      setMessage({ kind: "success", text: "Module added." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "Module creation failed." });
    } finally {
      setBusy(false);
    }
  }

  async function saveModule(moduleId: string) {
    if (!editingModuleTitle.trim()) return;
    setBusy(true);
    setMessage(null);
    try {
      const data = await request("/api/lms/courses/" + courseId + "/modules/" + moduleId, {
        method: "PATCH",
        body: JSON.stringify({ title: editingModuleTitle.trim() }),
      });
      setModules((current) => current.map((item) => item.id === moduleId ? { ...item, ...data } : item));
      setEditingModule(null);
      setMessage({ kind: "success", text: "Module updated." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "Module update failed." });
    } finally {
      setBusy(false);
    }
  }

  async function addLesson(event: FormEvent) {
    event.preventDefault();
    if (!selectedModule || !lessonTitle.trim()) return;
    setBusy(true);
    setMessage(null);
    try {
      const selectedModuleData = modules.find((item) => item.id === selectedModule);
      const position = (selectedModuleData?.lessons.length ?? 0) + 1;
      const body = lessonType === "rich_text" ? lessonContent : { url: lessonBody };
      const data = await request(
        "/api/lms/courses/" + courseId + "/modules/" + selectedModule + "/lessons",
        {
          method: "POST",
          body: JSON.stringify({
            title: lessonTitle.trim(),
            position,
            content_type: lessonType,
            content: body,
            change_note: changeNote || "Initial lesson version",
          }),
        },
      );
      const lesson = { ...data, content: body, position };
      setModules((current) => current.map((item) =>
        item.id === selectedModule ? { ...item, lessons: [...item.lessons, lesson] } : item,
      ));
      setLessonTitle("");
      setLessonBody("");
      setLessonContent({ version: 2, blocks: [] });
      setChangeNote("");
      setMessage({ kind: "success", text: "Lesson created with version 1." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "Lesson creation failed." });
    } finally {
      setBusy(false);
    }
  }
  function beginLessonEdit(lesson: Lesson) {
    setEditingLesson(lesson);
    setLessonTitle(lesson.title);
    setLessonType(lesson.content_type);
    if (lesson.content_type === "rich_text") {
      setLessonContent(lesson.content);
      setLessonBody("");
    } else {
      setLessonContent({ version: 2, blocks: [] });
      setLessonBody(String(lesson.content.url ?? ""));
    }
    setChangeNote("");
    setMessage(null);
  }

  async function saveLesson() {
    if (!editingLesson || !lessonTitle.trim()) return;
    if (lessonType === "rich_text") {
      const blocks = Array.isArray(lessonContent.blocks) ? lessonContent.blocks : [];
      if (!blocks.length) {
        setMessage({ kind: "error", text: "Add at least one learner-facing content block." }); return;
      }
    } else if (!lessonBody.trim() || !/^https?:\/\/[^\s/]+/i.test(lessonBody.trim())) {
      setMessage({ kind: "error", text: "Add a valid http(s) resource URL." }); return;
    }
    setBusy(true);
    setMessage(null);
    try {
      const content = lessonType === "rich_text" ? lessonContent : { url: lessonBody };
      const owningModule = modules.find((item) => item.lessons.some((lesson) => lesson.id === editingLesson.id));
      if (!owningModule) throw new Error("Module not found.");
      const data = await request(
        "/api/lms/courses/" + courseId + "/modules/" + owningModule.id + "/lessons/" + editingLesson.id,
        {
          method: "PATCH",
          body: JSON.stringify({
            title: lessonTitle.trim(),
            content_type: lessonType,
            content,
            change_note: changeNote || "Lesson content updated",
          }),
        },
      );
      setModules((current) => current.map((item) => item.id !== owningModule.id ? item : {
        ...item,
        lessons: item.lessons.map((lesson) => lesson.id === editingLesson.id ? { ...lesson, ...data } : lesson),
      }));
      setEditingLesson(null);
      setLessonContent({ version: 2, blocks: [] });
      setMessage({ kind: "success", text: "Lesson saved and a new content version was recorded." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "Lesson save failed." });
    } finally {
      setBusy(false);
    }
  }

  async function showHistory(moduleId: string, lessonId: string) {
    try {
      const data = await request(
        "/api/lms/courses/" + courseId + "/modules/" + moduleId + "/lessons/" + lessonId + "/versions",
      );
      setVersions((current) => ({ ...current, [lessonId]: Array.isArray(data) ? data : [] }));
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "Version history failed to load." });
    }
  }

  async function restoreVersion(moduleId: string, lessonId: string, versionNumber: number) {
    setBusy(true);
    setMessage(null);
    try {
      const data = await request(
        "/api/lms/courses/" + courseId + "/modules/" + moduleId + "/lessons/" + lessonId + "/versions/" + versionNumber + "/restore",
        { method: "POST" },
      );
      setModules((current) => current.map((item) => item.id !== moduleId ? item : {
        ...item,
        lessons: item.lessons.map((lesson) => lesson.id === lessonId ? { ...lesson, ...data } : lesson),
      }));
      await showHistory(moduleId, lessonId);
      setMessage({ kind: "success", text: "Version restored. A new audit/version entry was created." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "Version restore failed." });
    } finally {
      setBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Curriculum" title="Modules & lessons" meta={String(modules.length) + " module" + (modules.length === 1 ? "" : "s")}>
      {message && <Notice kind={message.kind}>{message.text}</Notice>}

      <form className="inline-form" onSubmit={addModule}>
        <input value={moduleTitle} onChange={(event) => setModuleTitle(event.target.value)} placeholder="Module title" required />
        <button className="button button-secondary" disabled={busy}>
          <Plus size={15} /> Add module
        </button>
      </form>

      <div className="compact-list" style={{ marginTop: 16 }}>
        {modules.map((module) => (
          <section className="curriculum-module" key={module.id}>
            <div className="curriculum-heading">
              <span>{String(module.position).padStart(2, "0")}</span>
              <div style={{ flex: 1 }}>
                {editingModule === module.id ? (
                  <div className="inline-form">
                    <input value={editingModuleTitle} onChange={(event) => setEditingModuleTitle(event.target.value)} />
                    <button className="button button-secondary" type="button" onClick={() => void saveModule(module.id)} disabled={busy}><Save size={14} /> Save</button>
                    <button className="button button-secondary" type="button" onClick={() => setEditingModule(null)}>Cancel</button>
                  </div>
                ) : (
                  <><strong>{module.title}</strong><small>{module.lessons.length} lesson{module.lessons.length === 1 ? "" : "s"}</small></>
                )}
              </div>
              {editingModule !== module.id && (
                <button className="button button-secondary" type="button" onClick={() => { setEditingModule(module.id); setEditingModuleTitle(module.title); }}>
                  <Edit3 size={14} /> Edit
                </button>
              )}
            </div>
            <div className="compact-list">
              {module.lessons.map((lesson) => (
                <article className="compact-row" key={lesson.id}>
                  <div style={{ flex: 1 }}>
                    <strong>{lesson.title}</strong>
                    <small>{lesson.content_type} · version history available</small>
                    <div className="inline-actions" style={{ marginTop: 8 }}>
                      <button className="button button-secondary" type="button" onClick={() => beginLessonEdit(lesson)}>
                        <Edit3 size={14} /> Edit content
                      </button>
                      <button className="button button-secondary" type="button" onClick={() => void showHistory(module.id, lesson.id)}>
                        <History size={14} /> History
                      </button>
                    </div>
                    {versions[lesson.id]?.length > 0 && (
                      <div className="soft-panel" style={{ marginTop: 8 }}>
                        <strong>Content history</strong>
                        {versions[lesson.id].map((version) => (
                          <div className="compact-row" key={version.id}>
                            <div>
                              <strong>Version {version.version_number}</strong>
                              <small>{version.change_note || "No change note"} · {new Date(version.created_at).toLocaleString()}</small>
                            </div>
                            <button className="button button-secondary" type="button" disabled={busy} onClick={() => void restoreVersion(module.id, lesson.id, version.version_number)}>
                              <RotateCcw size={14} /> Restore
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <Check size={16} className="success-icon" />
                </article>
              ))}
              {!module.lessons.length && <div className="empty-state"><p>No lessons yet.</p></div>}
            </div>
          </section>
        ))}
        {!modules.length && <div className="empty-state"><p>Create the first module, then add a learner-facing lesson.</p></div>}
      </div>

      {selectedModule && (
        <form className="soft-panel" onSubmit={addLesson} style={{ marginTop: 16 }}>
          <div className="section-heading compact"><div><span className="eyebrow">Lesson authoring</span><h3>Add lesson</h3></div></div>
          <label className="form-field"><span>Module</span><select value={selectedModule} onChange={(event) => setSelectedModule(event.target.value)}>{modules.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label>
          <div className="form-grid">
            <label className="form-field"><span>Lesson title</span><input value={lessonTitle} onChange={(event) => setLessonTitle(event.target.value)} required /></label>
            <label className="form-field"><span>Content type</span><select value={lessonType} onChange={(event) => setLessonType(event.target.value)}><option value="rich_text">Structured lesson</option><option value="video">Video</option><option value="document">Document</option><option value="link">External link</option></select></label>
          </div>
          {lessonType === "rich_text" ? <CourseContentBlockEditor value={lessonContent} onChange={setLessonContent} /> : <label className="form-field full"><span>Resource URL</span><input required type="url" pattern="https?://.+" value={lessonBody} onChange={(event) => setLessonBody(event.target.value)} placeholder="https://example.com/resource" /></label>}
          <label className="form-field full"><span>Change note</span><input value={changeNote} onChange={(event) => setChangeNote(event.target.value)} placeholder="What changed in this version?" /></label>
          <div className="form-actions"><button className="button button-primary" disabled={busy || !lessonTitle.trim()}><Plus size={15} /> Add lesson</button></div>
        </form>
      )}

      {editingLesson && (
        <div className="modal-backdrop" role="presentation">
          <div className="modal-panel" role="dialog" aria-modal="true" aria-labelledby="edit-lesson-title">
            <div className="section-heading compact">
              <div><span className="eyebrow">Content control</span><h3 id="edit-lesson-title">Edit lesson</h3></div>
              <button className="button button-secondary" type="button" onClick={() => setEditingLesson(null)}>Close</button>
            </div>
            <div className="form-grid">
              <label className="form-field"><span>Lesson title</span><input value={lessonTitle} onChange={(event) => setLessonTitle(event.target.value)} /></label>
              <label className="form-field"><span>Content type</span><select value={lessonType} onChange={(event) => setLessonType(event.target.value)}><option value="rich_text">Structured lesson</option><option value="video">Video</option><option value="document">Document</option><option value="link">External link</option></select></label>
            </div>
            {lessonType === "rich_text" ? <CourseContentBlockEditor value={lessonContent} onChange={setLessonContent} /> : <label className="form-field full"><span>Resource URL</span><input type="url" value={lessonBody} onChange={(event) => setLessonBody(event.target.value)} /></label>}
            <label className="form-field full"><span>Change note</span><input value={changeNote} onChange={(event) => setChangeNote(event.target.value)} placeholder="Describe this revision for audit/history." /></label>
            <div className="form-actions"><button className="button button-primary" type="button" onClick={() => void saveLesson()} disabled={busy}><Save size={15} /> Save revision</button></div>
          </div>
        </div>
      )}
    </SectionCard>
  );
}
