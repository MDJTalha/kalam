"use client";

import { useEffect, useState } from "react";
import { Check, Edit3, FolderTree, Plus, RotateCcw, X } from "lucide-react";
import { Notice, SectionCard } from "./ui";

type Category = {
  id: string;
  name: string;
  description?: string | null;
  active: boolean;
};

export function CourseCategoryAdmin() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [editing, setEditing] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ kind: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/lms/courses/categories?manage=true")
      .then(async (response) => {
        const data = await response.json().catch(() => []);
        if (!response.ok) throw new Error(data.detail || "Categories could not be loaded.");
        if (!cancelled && Array.isArray(data)) setCategories(data);
      })
      .catch((error) => {
        if (!cancelled) setMessage({ kind: "error", text: error instanceof Error ? error.message : "Load failed" });
      });
    return () => { cancelled = true; };
  }, []);

  function beginEdit(category: Category) {
    setEditing(category.id);
    setName(category.name);
    setDescription(category.description ?? "");
    setMessage(null);
  }
  function cancelEdit() {
    setEditing(null);
    setName("");
    setDescription("");
  }

  async function createCategory() {
    if (!newName.trim()) return;
    setBusy(true);
    setMessage(null);
    try {
      const response = await fetch("/api/lms/courses/categories", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName, description: newDescription || null }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Category creation failed.");
      setCategories((current) => [...current, data].sort((a, b) => a.name.localeCompare(b.name)));
      setNewName("");
      setNewDescription("");
      setMessage({ kind: "success", text: "Category created." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "Category creation failed." });
    } finally {
      setBusy(false);
    }
  }

  async function saveCategory() {
    if (!editing || !name.trim()) return;
    setBusy(true);
    setMessage(null);
    try {
      const response = await fetch(`/api/lms/courses/categories/${editing}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, description: description || null }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Category update failed.");
      setCategories((current) => current.map((item) => item.id === data.id ? data : item).sort((a, b) => a.name.localeCompare(b.name)));
      cancelEdit();
      setMessage({ kind: "success", text: "Category updated." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "Category update failed." });
    } finally {
      setBusy(false);
    }
  }

  async function setActive(category: Category, active: boolean) {
    setBusy(true);
    setMessage(null);
    try {
      const response = await fetch(`/api/lms/courses/categories/${category.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Category status update failed.");
      setCategories((current) => current.map((item) => item.id === data.id ? data : item));
      setMessage({ kind: "success", text: active ? "Category reactivated." : "Category deactivated. Existing courses retain their category." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "Category status update failed." });
    } finally {
      setBusy(false);
    }
  }

  return <SectionCard eyebrow="Catalog administration" title="Course categories" meta={`${categories.length} categories`}>
    {message && <Notice kind={message.kind}>{message.text}</Notice>}
    <div className="form-grid">
      <label className="form-field"><span>New category name</span><input value={newName} onChange={(event) => setNewName(event.target.value)} placeholder="e.g. Leadership & Management" /></label>
      <label className="form-field"><span>Description</span><input value={newDescription} onChange={(event) => setNewDescription(event.target.value)} placeholder="Optional catalog description" /></label>
    </div>
    <div className="form-actions"><button type="button" className="button button-primary" onClick={() => void createCategory()} disabled={busy || !newName.trim()}><Plus size={15}/> Add category</button></div>
    <div className="table-wrap category-admin-table">
      <table><thead><tr><th scope="col">Category</th><th scope="col">Description</th><th scope="col">Status</th><th scope="col">Actions</th></tr></thead><tbody>
        {categories.map((category) => <tr key={category.id}>
          <td><strong>{category.name}</strong></td>
          <td>{category.description || "—"}</td>
          <td><span className={category.active ? "status-badge success" : "status-badge"}>{category.active ? "Active" : "Inactive"}</span></td>
          <td><div className="inline-actions"><button className="button button-secondary" type="button" onClick={() => beginEdit(category)} disabled={busy}><Edit3 size={14}/> Edit</button><button className="button button-secondary" type="button" onClick={() => void setActive(category, !category.active)} disabled={busy}>{category.active ? <><X size={14}/> Deactivate</> : <><RotateCcw size={14}/> Reactivate</>}</button></div></td>
        </tr>)}
      </tbody></table>
    </div>
    {!categories.length && <div className="empty-state"><FolderTree size={24}/><p>No course categories have been configured.</p></div>}
    {editing && <div className="modal-backdrop" role="presentation"><div className="modal-panel" role="dialog" aria-modal="true" aria-labelledby="edit-category-title">
      <div className="section-heading compact"><div><span className="eyebrow">Category governance</span><h3 id="edit-category-title">Edit category</h3></div><button className="button button-secondary" type="button" onClick={cancelEdit}><X size={14}/> Close</button></div>
      <label className="form-field"><span>Name</span><input value={name} onChange={(event) => setName(event.target.value)} /></label>
      <label className="form-field"><span>Description</span><textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={4}/></label>
      <div className="form-actions"><button className="button button-primary" type="button" onClick={() => void saveCategory()} disabled={busy || !name.trim()}><Check size={14}/> Save changes</button></div>
    </div></div>}
  </SectionCard>;
}
