import { DashboardShell } from "@/components/dashboard-shell";
import { FileUpload } from "@/components/file-upload";
import { EmptyState, Section, StatusBadge } from "@/components/ui";
import { apiJson, requireUser } from "@/lib/server-api";

type FileItem={id:string;name:string;mime_type:string;size_bytes:number;status:string;created_at:string};

export default async function FilesPage(){
  const user=await requireUser<{permissions?:string[]}>();
  const rows=await apiJson<FileItem[]>("/api/v1/files");
  const canManage=user.permissions?.includes("files.manage")??false;
  if (rows === null) return <DashboardShell title="Files" eyebrow="Secure learning content"><section className="data-panel" role="alert"><h2>File repository unavailable</h2><p>Secure file records could not be loaded. Refresh and try again later.</p></section></DashboardShell>;
  return <DashboardShell title="Files" eyebrow="Secure learning content">
    {canManage?<Section eyebrow="Upload" title="Add governed content"><FileUpload/></Section>:null}
    <Section eyebrow="Repository" title="Tenant files">
      {rows?.length?<div className="table-wrap"><table className="data-table">
        <thead><tr><th scope="col">File</th><th scope="col">Type</th><th scope="col">Size</th><th scope="col">Status</th><th scope="col">Added</th></tr></thead>
        <tbody>{rows.map(x=><tr key={x.id}><td><strong>{x.status==="available"?<a className="text-link" href={"/api/lms/files/"+x.id+"/download"}>{x.name}</a>:x.name}</strong></td><td>{x.mime_type}</td><td>{Math.max(1,Math.round(x.size_bytes/1024))} KB</td><td><StatusBadge status={x.status}/></td><td>{new Date(x.created_at).toLocaleDateString()}</td></tr>)}</tbody>
      </table></div>:<EmptyState title="No files" description="Upload approved learning content to the governed repository."/>}
    </Section>
  </DashboardShell>;
}
