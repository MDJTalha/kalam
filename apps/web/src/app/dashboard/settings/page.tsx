import { DashboardShell } from "@/components/dashboard-shell";
import { SettingsCenter } from "@/components/settings-center";
import { apiJson, apiJsonResult, requireUser } from "@/lib/server-api";

type Preferences={preferred_name?:string|null;density?:"comfortable"|"compact";reduce_motion?:boolean;timezone?:string};
type User={id:string;tenant_id:string;tenant_name?:string|null;tenant_slug?:string|null;email:string;first_name:string;last_name:string;employee_number?:string|null;job_title?:string|null;org_unit_name?:string|null;manager_name?:string|null;last_login_at?:string|null;roles?:Array<{name:string}>;permissions?:string[];preferences?:Preferences};
type Notice={id:string;read_at?:string|null};
type Discovery={sso_providers?:Array<{provider:string;label:string}>;password_available?:boolean};
type NotificationPreferences={email_enabled:boolean;learning:boolean;compliance:boolean;assessment:boolean;credentials:boolean;support:boolean;approvals:boolean;system:boolean;security:boolean};

export default async function SettingsPage(){
  const user=await requireUser<User>();
  const [notices,discovery,notificationPreferencesResult]=await Promise.all([
    apiJson<Notice[]>("/api/v1/notifications"),
    user.tenant_slug?apiJson<Discovery>("/api/v1/auth/discovery/"+encodeURIComponent(user.tenant_slug)):Promise.resolve(null),
    apiJsonResult<NotificationPreferences>("/api/v1/notifications/preferences"),
  ]);
  const unreadCount=(notices||[]).filter(item=>!item.read_at).length;
  return <DashboardShell title="Settings" eyebrow="Account & workspace preferences"><SettingsCenter user={user} unreadCount={unreadCount} ssoProviders={discovery?.sso_providers||[]} passwordAvailable={discovery?.password_available!==false} initialNotificationPreferences={notificationPreferencesResult.data} notificationPreferencesError={notificationPreferencesResult.error}/></DashboardShell>;
}