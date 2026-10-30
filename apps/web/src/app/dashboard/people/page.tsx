import { DashboardShell } from "@/components/dashboard-shell";
import { redirect } from "next/navigation";
import { PeopleDirectory, type PeoplePageResult } from "@/components/people-directory";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type Unit = { id: string; name: string };
type Params = { q?: string; status?: string; unit?: string; page?: string };
export default async function PeoplePage({ searchParams }: { searchParams: Promise<Params> }) {
  const user = await requireUser<{ permissions?: string[] }>();
  const permissions = user.permissions ?? [];
  if (!permissions.includes("users.read")) return <DashboardShell title="People" eyebrow="Workforce administration"><section className="data-panel"><h2>Access restricted</h2><p>You need permission to view the people directory.</p></section></DashboardShell>;
  const params = await searchParams;
  const q = (params.q ?? "").trim().slice(0, 160);
  const status = ["all", "active", "inactive"].includes(params.status ?? "") ? params.status! : "all";
  const unit = params.unit === "unassigned" || /^[0-9a-fA-F-]{36}$/.test(params.unit ?? "") ? params.unit! : "all";
  const requested = Number(params.page);
  const page = Number.isSafeInteger(requested) && requested > 0 ? Math.min(requested, 100000) : 1;
  const query = new URLSearchParams({ page: String(page), page_size: "20", status, q });
  if (unit === "unassigned") query.set("unassigned", "true");
  else if (unit !== "all") query.set("unit_id", unit);
  const [peopleResult, unitsResult] = await Promise.all([
    apiJsonResult<PeoplePageResult>("/api/v1/people/page?" + query.toString()),
    apiJsonResult<Unit[]>("/api/v1/organization/units"),
  ]);
  const result = peopleResult.data;
  const units = unitsResult.data;
  if (result && result.total > 0 && page > Math.ceil(result.total / result.page_size)) {
    const destination = new URLSearchParams({ page: String(Math.ceil(result.total / result.page_size)) });
    if (q) destination.set("q", q);
    if (status !== "all") destination.set("status", status);
    if (unit !== "all") destination.set("unit", unit);
    redirect("/dashboard/people?" + destination.toString());
  }
  return <DashboardShell title="People" eyebrow="Workforce administration" breadcrumbs={[{ label: "Overview", href: "/dashboard" }, { label: "People" }]}>
    {peopleResult.ok && result && unitsResult.ok && units ? <PeopleDirectory result={result} units={units} filters={{ q, status, unit }} canManage={permissions.includes("users.manage")} /> : <section className="data-panel" role="alert"><h2>{peopleResult.status === 403 || unitsResult.status === 403 ? "People access restricted" : peopleResult.status === 0 || peopleResult.status >= 500 || unitsResult.status === 0 || unitsResult.status >= 500 ? "People service unavailable" : "People directory could not be loaded"}</h2><p>{peopleResult.status === 403 || unitsResult.status === 403 ? "Your account does not have permission to view the directory or organization units." : peopleResult.status === 0 || unitsResult.status === 0 ? "The API service could not be reached. Check that it is running and try again." : `People request: HTTP ${peopleResult.status}; organization units: HTTP ${unitsResult.status}. ${peopleResult.error || unitsResult.error || "Refresh and try again."}`}</p></section> }
  </DashboardShell>;
}
