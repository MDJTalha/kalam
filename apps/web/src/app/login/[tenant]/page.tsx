import { redirect } from "next/navigation";

export default async function TenantLoginPage({ params }: { params: Promise<{ tenant: string }> }) {
  const { tenant } = await params;
  redirect("/login?org=" + encodeURIComponent(tenant.trim().toLowerCase()));
}
