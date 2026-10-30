"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  ["/dashboard/saas", "Overview"],
  ["/dashboard/saas/inquiries", "Leads & Inquiries"],
  ["/dashboard/saas/clients", "Clients"],
  ["/dashboard/saas/tenants", "Tenants"],
  ["/dashboard/saas/pricing", "Pricing & Offers"],
  ["/dashboard/saas/trials", "Trials"],
  ["/dashboard/saas/tasks", "Tasks"],
  ["/dashboard/saas/forecast", "Forecast"],
  ["/dashboard/saas/subscriptions", "Subscriptions"],
  ["/dashboard/saas/contracts", "Contracts"],
  ["/dashboard/saas/billing", "Billing"],
  ["/dashboard/saas/onboarding", "Onboarding"],
  ["/dashboard/saas/renewals", "Renewals"],
  ["/dashboard/saas/team", "Sales Team"],
  ["/dashboard/saas/pipeline", "Pipeline"],
  ["/dashboard/saas/certifications", "Certifications"],
] as const;

export function SaaSCrmNav({ readOnly = false }: { readOnly?: boolean }) {
  const pathname = usePathname();
  const visibleItems = readOnly
    ? items.filter(([href]) => ["/dashboard/saas", "/dashboard/saas/tenants"].includes(href))
    : items;
  return <nav className="view-tabs" aria-label="SaaS CRM sections">
    {visibleItems.map(([href,label]) => {
      const active = href === "/dashboard/saas" ? pathname === href : pathname === href || pathname.startsWith(href + "/");
      return <Link className={active ? "active" : ""} href={href} key={href} aria-current={active ? "page" : undefined}>{label}</Link>;
    })}
  </nav>;
}
