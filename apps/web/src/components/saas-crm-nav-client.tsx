"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type Props = { permissions: string[] };

const items = [
  ["/dashboard/saas", "Business Overview", "saas.crm.read"],
  ["/dashboard/saas/inquiries", "Leads & Inquiries", "saas.sales.read"],
  ["/dashboard/saas/clients", "Clients", "saas.sales.read"],
  ["/dashboard/saas/pipeline", "Pipeline", "saas.sales.read"],
  ["/dashboard/saas/tasks", "Sales Tasks", "saas.sales.read"],
  ["/dashboard/saas/pricing", "Pricing & Offers", "saas.pricing.read"],
  ["/dashboard/saas/trials", "Trials", "saas.customer_success.read"],
  ["/dashboard/saas/tenants", "Tenants", "saas.customer_success.read"],
  ["/dashboard/saas/onboarding", "Onboarding", "saas.customer_success.read"],
  ["/dashboard/saas/subscriptions", "Subscriptions", "saas.finance.read"],
  ["/dashboard/saas/contracts", "Contracts", "saas.finance.read"],
  ["/dashboard/saas/billing", "Billing", "saas.finance.read"],
  ["/dashboard/saas/forecast", "Financial Forecast", "saas.finance.read"],
  ["/dashboard/saas/renewals", "Renewals", "saas.finance.read"],
  ["/dashboard/saas/team", "SaaS Team", "saas.team.read"],
  ["/dashboard/saas/roles", "Tenant Role Governance", "saas.roles.manage"],
  ["/dashboard/saas/certifications", "Platform Certifications", "saas.platform.read"],
] as const;

export function SaaSCrmNavClient({ permissions }: Props) {
  const pathname = usePathname();
  const visible = items.filter(([, , permission]) => permissions.includes(permission));
  return <nav className="view-tabs" aria-label="SaaS operations sections">
    {visible.map(([href, label]) => {
      const active = href === "/dashboard/saas"
        ? pathname === href
        : pathname === href || pathname.startsWith(href + "/");
      return <Link className={active ? "active" : ""} href={href} key={href} aria-current={active ? "page" : undefined}>{label}</Link>;
    })}
  </nav>;
}
