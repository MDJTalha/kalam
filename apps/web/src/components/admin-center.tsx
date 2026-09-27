"use client";
import { FormEvent, useState } from "react";
import { Building2, MailPlus, Save } from "lucide-react";
import { Notice, SectionCard, StatusBadge } from "./ui";

type Role={id:string;name:string;description?:string|null};
type OrgUnit={id:string;name:string;unit_type:string;code?:string|null;parent_id?:string|null};
type Person={id:string;first_name:string;last_name:string;email:string;job_title?:string|null;is_active:boolean};
type Tenant={id:string;name:string;slug:string;status:string;settings:Record<string,unknown>};type Permission={key:string;description?:string|null};

export function AdminCenter({tenant,roles,units,people,accessPermissions}:{tenant:Tenant;roles:Role[];units:OrgUnit[];people:Person[];accessPermissions:string[]}){
  const can = (permission: string) => accessPermissions.includes(permission);
  const [settings,setSettings]=useState(JSON.stringify(tenant.settings||{},null,2));const [unitName,setUnitName]=useState("");const [unitType,setUnitType]=useState("department");
  const [inviteEmail,setInviteEmail]=useState("");const [roleId,setRoleId]=useState(roles[0]?.id||"");const [selectedRoleId,setSelectedRoleId]=useState(roles[0]?.id||"");const [permissionCatalog,setPermissionCatalog]=useState<Permission[]>([]);const [rolePermissionKeys,setRolePermissionKeys]=useState<string[]>([]);const [message,setMessage]=useState<string|null>(null);const [busy,setBusy]=useState(false);
  async function loadRolePermissions(id:string){
    setSelectedRoleId(id);
    const [all,current]=await Promise.all([
      fetch("/api/lms/admin/permissions").then(r=>r.json()),
      fetch("/api/lms/admin/roles/"+id+"/permissions").then(r=>r.json())
    ]);
    setPermissionCatalog(Array.isArray(all)?all:[]);
    setRolePermissionKeys(Array.isArray(current.permission_keys)?current.permission_keys:[]);
  }
  async function saveRolePermissions(){
    setBusy(true);setMessage(null);
    try{
      const r=await fetch("/api/lms/admin/roles/"+selectedRoleId+"/permissions",{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({permission_keys:rolePermissionKeys})});
      const d=await r.json();if(!r.ok)throw new Error(typeof d.detail==="string"?d.detail:"Unable to update permissions");
      setMessage("Role permission matrix updated.");
    }catch(err){setMessage(err instanceof Error?err.message:"Unable to update permissions")}finally{setBusy(false)}
  }
  async function saveSettings(e:FormEvent){e.preventDefault();setBusy(true);setMessage(null);try{let parsed={};try{parsed=JSON.parse(settings)}catch{throw new Error("Settings must be valid JSON")};const r=await fetch("/api/lms/admin/tenant-settings",{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({settings:parsed})});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Unable to save settings");setMessage("Tenant settings updated.");}catch(err){setMessage(err instanceof Error?err.message:"Unable to update settings")}finally{setBusy(false)}}
  async function createUnit(e:FormEvent){e.preventDefault();setBusy(true);setMessage(null);try{const r=await fetch("/api/lms/admin/org-units",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:unitName,unit_type:unitType})});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Unable to create organization unit");setMessage("Organization unit created.");setUnitName("");}catch(err){setMessage(err instanceof Error?err.message:"Unable to create organization unit")}finally{setBusy(false)}}
  async function invite(e:FormEvent){e.preventDefault();setBusy(true);setMessage(null);try{const r=await fetch("/api/lms/admin/invitations",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:inviteEmail,role_id:roleId,expiry_days:7})});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Unable to create invitation");setMessage("Invitation created and queued for delivery.");setInviteEmail("");}catch(err){setMessage(err instanceof Error?err.message:"Unable to create invitation")}finally{setBusy(false)}}
  return <><div className="stat-grid"><div className="stat-card"><span>Tenant</span><strong>{tenant.name}</strong><small>{tenant.slug}</small></div><div className="stat-card"><span>Roles</span><strong>{roles.length}</strong><small>Permission roles</small></div><div className="stat-card"><span>Org units</span><strong>{units.length}</strong><small>Departments / business units</small></div><div className="stat-card"><span>People</span><strong>{people.length}</strong><small>Tenant workforce</small></div></div>
    {message&&<Notice kind="success">{message}</Notice>}
    {!can("tenant.manage")&&<Notice kind="info">Your current permissions allow viewing only. Tenant administration actions are disabled.</Notice>}
    <div className="console-grid">
      <SectionCard eyebrow="Tenant control" title="Tenant settings"><form className="studio-form" onSubmit={saveSettings}><label>Settings JSON<textarea rows={9} value={settings} onChange={e=>setSettings(e.target.value)} readOnly={!can("tenant.manage")}/></label>{can("tenant.manage")&&<button className="button button-primary" disabled={busy}><Save size={15}/> Save settings</button>}</form></SectionCard>
      <SectionCard eyebrow="Organization" title="Add organization unit"><form className="studio-form" onSubmit={createUnit}><div className="form-grid"><label>Name<input value={unitName} onChange={e=>setUnitName(e.target.value)} required disabled={!can("tenant.manage")}/></label><label>Type<select value={unitType} onChange={e=>setUnitType(e.target.value)} disabled={!can("tenant.manage")}><option>department</option><option>business_unit</option><option>location</option><option>team</option></select></label></div>{can("tenant.manage")&&<button className="button button-secondary" disabled={busy}><Building2 size={15}/> Create unit</button>}</form><div className="compact-list">{units.slice(0,8).map(u=><div className="compact-row" key={u.id}><div><strong>{u.name}</strong><small>{u.unit_type}{u.code?" · "+u.code:""}</small></div></div>)}</div></SectionCard>
      <SectionCard eyebrow="Identity lifecycle" title="Invite a user"><form className="studio-form" onSubmit={invite}><label>Work email<input type="email" value={inviteEmail} onChange={e=>setInviteEmail(e.target.value)} required disabled={!can("users.manage")}/></label><label>Role<select value={roleId} onChange={e=>setRoleId(e.target.value)} disabled={!can("users.manage")}>{roles.map(r=><option value={r.id} key={r.id}>{r.name}</option>)}</select></label>{can("users.manage")&&<button className="button button-primary" disabled={busy}><MailPlus size={15}/> Send invitation</button>}</form></SectionCard>
      <SectionCard eyebrow="Role model" title="Tenant roles"><div className="compact-list">{roles.map(role=><div className="compact-row" key={role.id}><div><strong>{role.name}</strong><small>{role.description||"Configured tenant role"}</small></div><StatusBadge status="configured"/></div>)}</div></SectionCard>
      <SectionCard eyebrow="Authorization" title="Role permission matrix">
        <div className="studio-form">
          <label>Role<select value={selectedRoleId} onChange={e=>void loadRolePermissions(e.target.value)} disabled={!can("tenant.manage")}>{roles.map(r=><option value={r.id} key={r.id}>{r.name}</option>)}</select></label>
          <div className="compact-list">
            {permissionCatalog.length ? permissionCatalog.map(permission=><label className="compact-row" key={permission.key}>
              <span><strong>{permission.key}</strong><small>{permission.description||"Permission"}</small></span>
              <input type="checkbox" checked={rolePermissionKeys.includes(permission.key)} onChange={e=>setRolePermissionKeys(keys=>e.target.checked?[...new Set([...keys,permission.key])]:keys.filter(key=>key!==permission.key))}/>
            </label>) : <div className="empty-state"><p>Select a role to load its permission matrix.</p></div>}
          </div>
          {can("tenant.manage")&&<button type="button" className="button button-primary" disabled={busy||!permissionCatalog.length} onClick={()=>void saveRolePermissions()}><Save size={15}/> Save permission matrix</button>}
        </div>
      </SectionCard>
    </div>
    <SectionCard eyebrow="Workforce" title="People register"><div className="table-wrap"><table className="data-table"><thead><tr><th>Person</th><th>Job title</th><th>Status</th></tr></thead><tbody>{people.slice(0,50).map(p=><tr key={p.id}><td><strong>{p.first_name} {p.last_name}</strong><small>{p.email}</small></td><td>{p.job_title||"—"}</td><td><StatusBadge status={p.is_active?"active":"inactive"}/></td></tr>)}</tbody></table></div></SectionCard>
  </>;
}