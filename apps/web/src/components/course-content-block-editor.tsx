"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowDown, ArrowUp, FileText, Image as ImageIcon, Link2, Minus, Plus, Trash2, UploadCloud } from "lucide-react";

export type ContentBlockType = "heading" | "paragraph" | "bullets" | "numbered" | "callout" | "image" | "video" | "file" | "link" | "divider";
export type ContentBlock = {
  id: string; type: ContentBlockType; text?: string; level?: 2 | 3 | 4;
  variant?: "info" | "success" | "warning" | "important"; url?: string;
  file_id?: string; alt?: string; caption?: string;
};
export type LessonContent = { version?: 2; blocks: ContentBlock[] };
type FileItem = { id: string; name: string; mime_type: string; size_bytes: number; status: string };

const LABELS: Record<ContentBlockType, string> = {
  heading: "Heading", paragraph: "Paragraph", bullets: "Bulleted list", numbered: "Numbered list",
  callout: "Callout", image: "Image", video: "Video", file: "Document / file", link: "Link", divider: "Divider",
};

function newId() { return `block-${Date.now()}-${Math.random().toString(36).slice(2,8)}`; }
function normalize(value: Record<string, unknown> | undefined): LessonContent {
  const raw = Array.isArray(value?.blocks) ? value.blocks : [];
  if (raw.length) return { version: 2, blocks: raw.map((item, index) => { const source = item as Record<string, unknown>; const { id: _sourceId, ...rest } = source; return { ...(rest as Omit<ContentBlock, "id">), id: typeof _sourceId === "string" ? _sourceId : `legacy-${index}` }; }) };
  const body = typeof value?.body === "string" ? value.body : "";
  return { version: 2, blocks: body ? [{ id: newId(), type: "paragraph", text: body }] : [] };
}
export function CourseContentBlockEditor({
  value,
  onChange,
}: {
  value: Record<string, unknown>;
  onChange: (value: LessonContent) => void;
}) {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [fileError, setFileError] = useState("");
  const [uploading, setUploading] = useState(false);
  const content = useMemo(() => normalize(value), [value]);

  useEffect(() => {
    let active = true;
    fetch("/api/lms/files")
      .then(async (response) => {
        const data = await response.json().catch(() => []);
        if (!response.ok) throw new Error(data.detail || "The content library could not be loaded.");
        if (active && Array.isArray(data)) setFiles(data.filter((item) => item.status === "available"));
      })
      .catch((error) => { if (active) setFileError(error instanceof Error ? error.message : "Content library unavailable."); });
    return () => { active = false; };
  }, []);

  function replace(blockId: string, patch: Partial<ContentBlock>) {
    onChange({ version: 2, blocks: content.blocks.map((block) => block.id === blockId ? { ...block, ...patch } : block) });
  }
  function add(type: ContentBlockType) {
    const defaults: ContentBlock =
      type === "heading" ? { id: newId(), type, level: 2, text: "" } :
      type === "callout" ? { id: newId(), type, variant: "info", text: "" } :
      { id: newId(), type, text: "" };
    onChange({ version: 2, blocks: [...content.blocks, defaults] });
  }
  function remove(id: string) { onChange({ version: 2, blocks: content.blocks.filter((block) => block.id !== id) }); }
  function move(id: string, direction: -1 | 1) {
    const index = content.blocks.findIndex((block) => block.id === id);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= content.blocks.length) return;
    const blocks = [...content.blocks]; [blocks[index], blocks[target]] = [blocks[target], blocks[index]];
    onChange({ version: 2, blocks });
  }
  async function uploadFile(file: File) {
    setUploading(true); setFileError("");
    try {
      const form = new FormData(); form.append("upload", file);
      const response = await fetch("/api/lms/files", { method: "POST", body: form });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Upload failed.");
      const created = data as FileItem;
      if (created.status === "available") setFiles((current) => [created, ...current]);
      setFileError(created.status === "available" ? "" : "The file was stored but remains pending security clearance.");
      return created.status === "available" ? created : null;
    } catch (error) {
      setFileError(error instanceof Error ? error.message : "Upload failed.");
      return null;
    } finally { setUploading(false); }
  }

  return <div className="content-block-editor">
    <div className="content-editor-toolbar" role="toolbar" aria-label="Content blocks">
      {(["heading","paragraph","bullets","numbered","callout","image","video","file","link","divider"] as ContentBlockType[]).map((type) =>
        <button key={type} type="button" className="button button-secondary" onClick={() => add(type)}><Plus size={13}/>{LABELS[type]}</button>
      )}
    </div>
    {fileError && <div className="form-error" role="alert">{fileError}</div>}
    <div className="content-block-list">
      {content.blocks.map((block, index) => <article className="content-block" key={block.id}>
        <div className="content-block-head">
          <div><span className="eyebrow">{LABELS[block.type]}</span><span className="content-block-index">Block {index + 1}</span></div>
          <div className="content-block-actions">
            <button type="button" className="icon-button" aria-label="Move block up" disabled={index === 0} onClick={() => move(block.id,-1)}><ArrowUp size={14}/></button>
            <button type="button" className="icon-button" aria-label="Move block down" disabled={index === content.blocks.length-1} onClick={() => move(block.id,1)}><ArrowDown size={14}/></button>
            <button type="button" className="icon-button danger" aria-label="Delete block" onClick={() => remove(block.id)}><Trash2 size={14}/></button>
          </div>
        </div>
        {block.type === "divider" ? <div className="content-divider-preview"><Minus size={18}/><span>Section divider</span><Minus size={18}/></div> : null}
        {block.type === "heading" && <div className="form-grid">
          <label className="form-field"><span>Level</span><select value={block.level ?? 2} onChange={(e) => replace(block.id,{level:Number(e.target.value) as 2|3|4})}><option value={2}>Heading 2</option><option value={3}>Heading 3</option><option value={4}>Heading 4</option></select></label>
          <label className="form-field full"><span>Heading text</span><input value={block.text ?? ""} maxLength={240} onChange={(e) => replace(block.id,{text:e.target.value})} /></label>
        </div>}
        {block.type === "paragraph" && <label className="form-field"><span>Paragraph text</span><textarea rows={4} value={block.text ?? ""} onChange={(e) => replace(block.id,{text:e.target.value})} placeholder="Write learner-facing content. You can use a blank line to separate ideas." /></label>}
        {(block.type === "bullets" || block.type === "numbered") && <label className="form-field"><span>{block.type === "bullets" ? "List items" : "Numbered items"} — one item per line</span><textarea rows={5} value={block.text ?? ""} onChange={(e) => replace(block.id,{text:e.target.value})} placeholder="First item&#10;Second item&#10;Third item" /></label>}
        {block.type === "callout" && <div className="form-grid">
          <label className="form-field"><span>Style</span><select value={block.variant ?? "info"} onChange={(e) => replace(block.id,{variant:e.target.value as ContentBlock["variant"]})}><option value="info">Information</option><option value="success">Success</option><option value="warning">Warning</option><option value="important">Important</option></select></label>
          <label className="form-field full"><span>Callout message</span><textarea rows={3} value={block.text ?? ""} onChange={(e) => replace(block.id,{text:e.target.value})} /></label>
        </div>}
        {(block.type === "image" || block.type === "file") && <div className="form-grid">
          <label className="form-field full"><span>Governed file</span><select value={block.file_id ?? ""} onChange={(e) => replace(block.id,{file_id:e.target.value || undefined, url:undefined})}><option value="">Use a URL instead</option>{files.map((file) => <option value={file.id} key={file.id}>{file.name} · {file.mime_type}</option>)}</select></label>
          <label className="form-field"><span>Resource URL</span><input type="url" value={block.url ?? ""} onChange={(e) => replace(block.id,{url:e.target.value, file_id:undefined})} placeholder="https://…" /></label>
          <label className="form-field"><span>{block.type === "image" ? "Alternative text" : "Link label"}</span><input value={block.alt ?? ""} maxLength={240} onChange={(e) => replace(block.id,{alt:e.target.value})} /></label>
          {block.type === "image" && <label className="form-field full"><span>Caption</span><input value={block.caption ?? ""} maxLength={240} onChange={(e) => replace(block.id,{caption:e.target.value})} /></label>}
          <label className="upload-inline"><UploadCloud size={14}/><span>{uploading ? "Uploading…" : "Upload to governed library"}</span><input type="file" disabled={uploading} accept={block.type === "image" ? "image/png,image/jpeg" : ".pdf,.docx,.xlsx,.csv,.txt"} onChange={async (e) => { const file=e.target.files?.[0]; if(file){ const created=await uploadFile(file); if(created) replace(block.id,{file_id:created.id,url:undefined}); } e.currentTarget.value=""; }} /></label>
        </div>}
        {block.type === "video" && <div className="form-grid">
          <label className="form-field full"><span>Video URL</span><input type="url" value={block.url ?? ""} onChange={(e) => replace(block.id,{url:e.target.value})} placeholder="https://…" /></label>
          <label className="form-field full"><span>Supporting text</span><textarea rows={3} value={block.text ?? ""} onChange={(e) => replace(block.id,{text:e.target.value})} placeholder="Optional context for the video." /></label>
        </div>}
        {block.type === "link" && <div className="form-grid">
          <label className="form-field"><span>Label</span><input value={block.text ?? ""} onChange={(e) => replace(block.id,{text:e.target.value})} /></label>
          <label className="form-field"><span>URL</span><input type="url" value={block.url ?? ""} onChange={(e) => replace(block.id,{url:e.target.value})} placeholder="https://…" /></label>
        </div>}
      </article>)}
      {!content.blocks.length && <div className="content-block-empty"><FileText size={20}/><strong>Build the learner experience block by block</strong><span>Start with a heading or paragraph, then add media, callouts and governed files.</span></div>}
    </div>
    <small className="form-help"><ImageIcon size={13}/> Images and documents can reference the governed tenant library. <Link2 size={13}/> URLs are validated before publication.</small>
  </div>;
}
