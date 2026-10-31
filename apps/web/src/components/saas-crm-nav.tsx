import { requireUser } from "@/lib/server-api";
import { SaaSCrmNavClient } from "@/components/saas-crm-nav-client";

export async function SaaSCrmNav() {
  const user = await requireUser<{ permissions?: string[] }>();
  return <SaaSCrmNavClient permissions={user.permissions ?? []} />;
}
