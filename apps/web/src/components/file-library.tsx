"use client";
import { ChangeEvent, useState } from "react";
import { FileArchive, UploadCloud } from "lucide-react";
import { Notice, SectionCard, StatusBadge } from "./ui";

type FileItem={id:string;name:string;mime_type:string;size_bytes:number;status:string;created_at:string};
export function FileLibrary({initial}:{initial:FileItem[]}){
  const [items,setItems]=useState(initial);const [busy,setBusy]=useState(false);const [message,setMessage]=useState<string|null>(null);
  async function upload(e:ChangeEvent<HTMLInputElement>){
    const file=e.target.files?.[0];if(!file)return;setBusy(true);setMessage(null);
    try{
      const form=new FormData();form.append("upload",file);
      const r=await fetch("/api/lms/files",{method:"POST",body:form});const d=await r.json();
      if(!r.ok)throw new Error(d.detail||"Upload failed");
      setItems([d,...items]);setMessage("File uploaded and queued for security scanning.");
    }catch(err){setMessage(err instanceof Error?err.message:"Upload failed")}
    finally{setBusy(false);e.target.value=""}
  }
  return <>
    <SectionCard eyebrow="Content security" title="Upload content">
      <label className="upload-zone"><UploadCloud size={24}/><strong>{busy?"Uploading…":"Choose a file"}</strong><small>PDF, office documents, images and controlled archives. Files remain unavailable until cleared.</small><input type="file" onChange={upload} hidden/></label>
      {message&&<Notice kind={message.startsWith("File")?"success":"error"}>{message}</Notice>}
    </SectionCard>
    <SectionCard eyebrow="Tenant library" title="Content files" meta={items.length+" records"}>
      <div className="table-wrap"><table className="data-table"><thead><tr><th>File</th><th>Type</th><th>Size</th><th>Status</th><th>Created</th></tr></thead><tbody>{items.map(item=><tr key={item.id}><td><strong>{item.name}</strong><small>{item.id}</small></td><td>{item.mime_type}</td><td>{Math.round(item.size_bytes/1024)} KB</td><td><StatusBadge status={item.status}/></td><td>{new Date(item.created_at).toLocaleString()}</td></tr>)}</tbody></table></div>
      {!items.length&&<div className="empty-state"><FileArchive size={25}/><p>No content files uploaded yet.</p></div>}
    </SectionCard>
  </>;
}