"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Bell, Building2, CheckCircle2, ChevronRight, CircleHelp, Clock3, KeyRound, MonitorCog, Palette, Save, Settings2, ShieldCheck, UserRound, UsersRound } from "lucide-react";

type Preferences={preferred_name?:string|null;density?:"comfortable"|"compact";reduce_motion?:boolean;timezone?:string};
type UserContext={first_name:string;last_name:string;email:string;employee_number?:string|null;job_title?:string|null;tenant_name?:string|null;tenant_slug?:string|null;org_unit_name?:string|null;manager_name?:string|null;last_login_at?:string|null;roles?:Array<{name:string}>;permissions?:string[];preferences?:Preferences};
type SsoProvider={provider:string;label:string};
type NotificationPreferences={email_enabled:boolean;learning:boolean;compliance:boolean;assessment:boolean;credentials:boolean;support:boolean;approvals:boolean;system:boolean;security:boolean};

const isNotificationPreferences=(value:unknown):value is NotificationPreferences=>
  typeof value==="object"&&value!==null&&
  ["email_enabled","learning","compliance","assessment","credentials","support","approvals","system","security"]
    .every(key=>typeof (value as Record<string,unknown>)[key]==="boolean");

export function SettingsCenter({user,unreadCount,ssoProviders,passwordAvailable=true,initialNotificationPreferences,notificationPreferencesError}:{user:UserContext;unreadCount:number;ssoProviders:SsoProvider[];passwordAvailable?:boolean;initialNotificationPreferences:NotificationPreferences|null;notificationPreferencesError:string|null}) {
  const [preferredName,setPreferredName]=useState(user.preferences?.preferred_name||"");
  const [density,setDensity]=useState<"comfortable"|"compact">(user.preferences?.density==="compact"?"compact":"comfortable");
  const [reduceMotion,setReduceMotion]=useState(Boolean(user.preferences?.reduce_motion));
  const [timezone,setTimezone]=useState(user.preferences?.timezone||"UTC");
  const [busy,setBusy]=useState(false); const [message,setMessage]=useState(""); const [error,setError]=useState("");
  const [currentPassword,setCurrentPassword]=useState(""); const [newPassword,setNewPassword]=useState(""); const [confirmPassword,setConfirmPassword]=useState(""); const [passwordMessage,setPasswordMessage]=useState(""); const [passwordError,setPasswordError]=useState(""); const [passwordBusy,setPasswordBusy]=useState(false);
  const [notificationPreferences,setNotificationPreferences]=useState<NotificationPreferences|null>(initialNotificationPreferences);
  const [notificationLoadError,setNotificationLoadError]=useState(initialNotificationPreferences?null:notificationPreferencesError||"Notification preferences could not be loaded.");
  const [notificationLoading,setNotificationLoading]=useState(false);
  const [notificationBusy,setNotificationBusy]=useState(false); const [notificationMessage,setNotificationMessage]=useState(""); const [notificationError,setNotificationError]=useState("");
  const timezones=useMemo(()=>{try{const values=Intl.supportedValuesOf("timeZone");return values.includes("UTC")?values:["UTC",...values]}catch{return["UTC","Asia/Karachi","Asia/Dubai","Europe/London","America/New_York","America/Los_Angeles"]}},[]);
  const canTenantManage=user.permissions?.includes("tenant.manage")??false;
  const canIntegrations=user.permissions?.includes("integrations.manage")??false;
  const canAudit=user.permissions?.includes("audit.read")??false;
  const displayName=preferredName.trim()||user.first_name;
  const initials=((displayName[0]||"K")+(user.last_name?.[0]||"")).toUpperCase();

  async function loadNotificationPreferences(){
    setNotificationLoading(true);setNotificationLoadError(null);setNotificationError("");setNotificationMessage("");
    try{
      const response=await fetch("/api/lms/notifications/preferences",{cache:"no-store"});
      const data:unknown=await response.json().catch(()=>null);
      if(!response.ok)throw new Error(data&&typeof data==="object"&&"detail" in data&&typeof data.detail==="string"?data.detail:"Notification preferences could not be loaded.");
      if(!isNotificationPreferences(data))throw new Error("The notification preferences response was incomplete. Refresh and try again.");
      setNotificationPreferences(data);
    }catch(cause){
      setNotificationLoadError(cause instanceof Error?cause.message:"Notification preferences could not be loaded.");
    }finally{setNotificationLoading(false)}
  }

  async function saveNotificationPreferences(){
    if(!notificationPreferences)return;
    setNotificationBusy(true);setNotificationMessage("");setNotificationError("");
    try{
      const {security: _security,...payload}=notificationPreferences;
      void _security;
      const response=await fetch("/api/lms/notifications/preferences",{method:"PATCH",headers:{"content-type":"application/json"},body:JSON.stringify(payload)});
      const data=await response.json().catch(()=>({}));
      if(!response.ok)throw new Error(typeof data.detail==="string"?data.detail:"Notification preferences could not be saved.");
      if(!isNotificationPreferences(data))throw new Error("The saved notification preferences response was incomplete. Reload the page to verify your settings.");
      setNotificationPreferences(data);
      setNotificationMessage("Notification preferences saved.");
    }catch(cause){setNotificationError(cause instanceof Error?cause.message:"Notification preferences could not be saved.")}finally{setNotificationBusy(false)}
  }

  async function changePassword(){
    setPasswordError("");setPasswordMessage("");
    if(newPassword.length<12){setPasswordError("Use at least 12 characters for the new password.");return}
    if(newPassword!==confirmPassword){setPasswordError("New password and confirmation do not match.");return}
    setPasswordBusy(true);
    try{
      const response=await fetch("/api/lms/auth/change-password",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({current_password:currentPassword,new_password:newPassword})});
      const data=await response.json().catch(()=>({}));
      if(!response.ok)throw new Error(typeof data.detail==="string"?data.detail:"Password could not be changed.");
      setCurrentPassword("");setNewPassword("");setConfirmPassword("");
      setPasswordMessage("Password updated. Other active sessions were signed out.");
    }catch(cause){setPasswordError(cause instanceof Error?cause.message:"Password could not be changed.")}finally{setPasswordBusy(false)}
  }

  async function savePreferences(){
    setBusy(true);setMessage("");setError("");
    try{
      const response=await fetch("/api/lms/auth/preferences",{method:"PATCH",headers:{"content-type":"application/json"},body:JSON.stringify({preferred_name:preferredName.trim()||null,density,reduce_motion:reduceMotion,timezone})});
      const data=await response.json().catch(()=>({}));
      if(!response.ok)throw new Error(typeof data.detail==="string"?data.detail:"Preferences could not be saved.");
      setMessage("Preferences saved. Refresh to apply density and motion changes across the workspace.");
    }catch(cause){setError(cause instanceof Error?cause.message:"Preferences could not be saved.")}finally{setBusy(false)}
  }

  return <div className="settings-center">
    <aside className="settings-nav" aria-label="Settings sections">
      <div className="settings-nav-title"><Settings2 size={17}/><span>Settings</span></div>
      <a href="#profile"><UserRound size={15}/>Profile</a><a href="#preferences"><Palette size={15}/>Preferences</a><a href="#notifications"><Bell size={15}/>Notifications</a><a href="#security"><ShieldCheck size={15}/>Security</a>
      {(canTenantManage||canIntegrations||canAudit)&&<a href="#organization"><Building2 size={15}/>Organization</a>}
      <a href="#support"><CircleHelp size={15}/>Help & support</a>
    </aside>
    <div className="settings-content">
      <section className="settings-hero"><div className="settings-avatar">{initials}</div><div><span className="eyebrow">Account settings</span><h2>{displayName} {user.last_name}</h2><p>{user.job_title||"Kalam user"}{user.tenant_name?" · "+user.tenant_name:""}</p></div><span className="status-badge success"><CheckCircle2 size={13}/>Active account</span></section>

      <section className="settings-section" id="profile"><div className="settings-section-heading"><div><span className="eyebrow">Profile</span><h2>Your identity</h2><p>Identity and employment attributes supplied by your organization are shown as managed fields.</p></div><UserRound size={20}/></div>
        <div className="settings-detail-grid">
          <div><span>Full name</span><strong>{user.first_name} {user.last_name}</strong><small>Managed by your organization</small></div><div><span>Work email</span><strong>{user.email}</strong><small>Managed by your organization</small></div>
          <div><span>Employee number</span><strong>{user.employee_number||"Not provided"}</strong><small>Managed by your organization</small></div><div><span>Job title</span><strong>{user.job_title||"Not provided"}</strong><small>Managed by your organization</small></div>
          <div><span>Organization unit</span><strong>{user.org_unit_name||"Not assigned"}</strong><small>Organization structure</small></div><div><span>Manager</span><strong>{user.manager_name||"Not assigned"}</strong><small>Organization structure</small></div>
        </div>
      </section>

      <section className="settings-section" id="preferences"><div className="settings-section-heading"><div><span className="eyebrow">Personal preferences</span><h2>Workspace experience</h2><p>These preferences belong to your account and do not change organization-managed identity data.</p></div><MonitorCog size={20}/></div>
        <div className="settings-form-grid"><label><span>Preferred display name</span><input value={preferredName} onChange={e=>setPreferredName(e.target.value)} maxLength={80} placeholder={user.first_name}/><small>Used in supported Kalam workspace surfaces.</small></label>
          <label><span>Time zone</span><select value={timezone} onChange={e=>setTimezone(e.target.value)}>{timezones.map(item=><option value={item} key={item}>{item}</option>)}</select><small>Used by settings-aware date and session views.</small></label></div>
        <fieldset className="settings-choice-group"><legend>Display density</legend><label className={density==="comfortable"?"selected":""}><input type="radio" name="density" checked={density==="comfortable"} onChange={()=>setDensity("comfortable")}/><span><strong>Comfortable</strong><small>More spacing for everyday use.</small></span></label><label className={density==="compact"?"selected":""}><input type="radio" name="density" checked={density==="compact"} onChange={()=>setDensity("compact")}/><span><strong>Compact</strong><small>More information visible at once.</small></span></label></fieldset>
        <label className="settings-switch"><input type="checkbox" checked={reduceMotion} onChange={e=>setReduceMotion(e.target.checked)}/><span><strong>Reduce interface motion</strong><small>Minimizes transitions and animated movement across the workspace.</small></span></label>
        <div className="settings-actions"><button className="button button-primary" type="button" onClick={()=>void savePreferences()} disabled={busy}><Save size={15}/>{busy?"Saving…":"Save preferences"}</button>{message&&<span className="form-success" role="status">{message}</span>}{error&&<span className="form-error" role="alert">{error}</span>}</div>
      </section>

      <section className="settings-section" id="notifications"><div className="settings-section-heading"><div><span className="eyebrow">Notifications</span><h2>Notification preferences</h2><p>Choose which categories may use optional notification delivery. Security notifications remain enabled because they may be required to protect your account.</p></div><Bell size={20}/></div>
        {!notificationPreferences?<div className="ds-state ds-state-danger" role="alert"><div><strong className="ds-state-title">Notification preferences unavailable</strong><span className="ds-state-copy">{notificationLoadError||"Your saved choices could not be confirmed, so editing is disabled to avoid overwriting them."}</span><button className="button button-secondary" type="button" onClick={()=>void loadNotificationPreferences()} disabled={notificationLoading}>{notificationLoading?"Loading…":"Try again"}</button></div></div>:<>
        <div className="notification-preference-grid">
          <label className="settings-switch"><input type="checkbox" checked={notificationPreferences.email_enabled} onChange={e=>setNotificationPreferences({...notificationPreferences,email_enabled:e.target.checked})}/><span><strong>Email delivery</strong><small>Allow eligible notification categories to also use email when email delivery is configured.</small></span></label>
          <label className="settings-switch locked"><input type="checkbox" checked readOnly/><span><strong>Security</strong><small>Mandatory account and sign-in security notifications cannot be disabled.</small></span></label>
          {(["learning","compliance","assessment","credentials","support","approvals","system"] as const).map(key=><label className="settings-switch" key={key}><input type="checkbox" checked={notificationPreferences[key]} onChange={e=>setNotificationPreferences({...notificationPreferences,[key]:e.target.checked})}/><span><strong>{key.charAt(0).toUpperCase()+key.slice(1)}</strong><small>{key==="learning"?"Assignments, enrollment and learning activity.":key==="compliance"?"Readiness, obligation and compliance reminders.":key==="assessment"?"Assessment availability and completion updates.":key==="credentials"?"Certificates, credentials and expiry-related updates.":key==="support"?"Support-case replies and status changes.":key==="approvals"?"Approval and workflow decisions that need attention.":"General platform and operational notices."}</small></span></label>)}
        </div>
        <div className="settings-actions"><button className="button button-primary" type="button" onClick={()=>void saveNotificationPreferences()} disabled={notificationBusy||!notificationPreferences}><Save size={15}/>{notificationBusy?"Saving…":"Save notification preferences"}</button>{notificationMessage&&<span className="form-success" role="status">{notificationMessage}</span>}{notificationError&&<span className="form-error" role="alert">{notificationError}</span>}</div>
        </>}
        <div className="settings-action-row"><div><strong>{unreadCount} unread notification{unreadCount===1?"":"s"}</strong><span>Review your current inbox, filter by category and open the source workflow directly.</span></div><Link className="button button-secondary" href="/dashboard/notifications">Open Notification Center <ChevronRight size={15}/></Link></div>
      </section>

      <section className="settings-section" id="security"><div className="settings-section-heading"><div><span className="eyebrow">Security</span><h2>Sign-in & session security</h2><p>Review how your organization authenticates access and manage active Kalam sessions.</p></div><ShieldCheck size={20}/></div>
        <div className="settings-security-grid"><article><KeyRound size={18}/><span><strong>{ssoProviders.length?"Enterprise SSO available":"Password sign-in"}</strong><small>{ssoProviders.length?ssoProviders.map(item=>item.label).join(" · "):"No connected enterprise SSO method is currently exposed for this organization."}</small></span></article><article><Clock3 size={18}/><span><strong>Last sign-in</strong><small>{user.last_login_at?new Date(user.last_login_at).toLocaleString(undefined,{timeZone:timezone}):"No sign-in timestamp available"}</small></span></article></div>
        {passwordAvailable&&<div className="settings-password-panel"><div><strong>Change password</strong><span>Changing your password signs out other active sessions while keeping this browser signed in.</span></div><div className="settings-password-grid"><label><span>Current password</span><input type="password" autoComplete="current-password" value={currentPassword} onChange={e=>setCurrentPassword(e.target.value)}/></label><label><span>New password</span><input type="password" autoComplete="new-password" minLength={12} value={newPassword} onChange={e=>setNewPassword(e.target.value)}/></label><label><span>Confirm new password</span><input type="password" autoComplete="new-password" minLength={12} value={confirmPassword} onChange={e=>setConfirmPassword(e.target.value)}/></label></div><div className="settings-actions"><button className="button button-secondary" type="button" onClick={()=>void changePassword()} disabled={passwordBusy||!currentPassword||!newPassword||!confirmPassword}>{passwordBusy?"Updating…":"Update password"}</button>{passwordMessage&&<span className="form-success" role="status">{passwordMessage}</span>}{passwordError&&<span className="form-error" role="alert">{passwordError}</span>}</div></div>}
        <div className="settings-action-row"><div><strong>Active sessions</strong><span>Review current and other signed-in sessions and revoke access you no longer recognize.</span></div><Link className="button button-secondary" href="/dashboard/settings/sessions">Manage active sessions <ChevronRight size={15}/></Link></div>
      </section>

      {(canTenantManage||canIntegrations||canAudit)&&<section className="settings-section" id="organization"><div className="settings-section-heading"><div><span className="eyebrow">Administration</span><h2>Organization controls</h2><p>Administrative controls are shown only when your assigned permissions allow access.</p></div><Building2 size={20}/></div><div className="settings-link-grid">
        {canTenantManage&&<Link href="/dashboard/admin"><UsersRound size={18}/><span><strong>Roles & permissions</strong><small>Manage roles, permissions and identity administration.</small></span><ChevronRight size={16}/></Link>}
        {canIntegrations&&<Link href="/dashboard/integrations"><KeyRound size={18}/><span><strong>Identity & integrations</strong><small>Configure enterprise integrations and connected identity services.</small></span><ChevronRight size={16}/></Link>}
        {canAudit&&<Link href="/dashboard/audit"><ShieldCheck size={18}/><span><strong>Audit log</strong><small>Review governed administrative and security events.</small></span><ChevronRight size={16}/></Link>}
      </div></section>}

      <section className="settings-section" id="support"><div className="settings-section-heading"><div><span className="eyebrow">Support</span><h2>Help & support</h2><p>Use Kalam support resources for product guidance, access questions and operational assistance.</p></div><CircleHelp size={20}/></div><div className="settings-action-row"><div><strong>Need help?</strong><span>Open the support center without leaving your secured workspace.</span></div><Link className="button button-secondary" href="/dashboard/help">Open Help & Support <ChevronRight size={15}/></Link></div></section>
    </div>
  </div>;
}
