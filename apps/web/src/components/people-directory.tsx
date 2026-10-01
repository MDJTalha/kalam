import Link from "next/link";
import { Filter, RotateCcw, Search, UsersRound } from "lucide-react";

type Unit = { id: string; name: string };
type Person = { id: string; email: string; first_name: string; last_name: string; employee_number?: string | null; job_title?: string | null; org_unit_id?: string | null; is_active: boolean };
export type PeoplePageResult = { items: Person[]; total: number; tenant_total: number; page: number; page_size: number };
type Filters = { q: string; status: string; unit: string };

export function PeopleDirectory({ result, units, filters, canManage }: { result: PeoplePageResult; units: Unit[]; filters: Filters; canManage: boolean }) {
  const unitNames = new Map(units.map(item => [item.id, item.name]));
  const pages = Math.max(1, Math.ceil(result.total / result.page_size));
  const pageHref = (page: number) => {
    const query = new URLSearchParams({ page: String(page) });
    if (filters.q) query.set("q", filters.q);
    if (filters.status !== "all") query.set("status", filters.status);
    if (filters.unit !== "all") query.set("unit", filters.unit);
    return "/dashboard/people?" + query.toString();
  };
  return <section className="data-panel">
    <div className="section-heading compact people-directory-heading"><div><span className="eyebrow">Tenant workforce</span><h2>People directory</h2></div>{canManage && <Link className="button button-primary people-manage-button" href="/dashboard/people/admin" aria-label="Manage people and workforce access"><UsersRound size={16} aria-hidden="true" /><span>Manage people</span></Link>}</div>
    {(() => {
      const hasFilters = Boolean(filters.q || filters.status !== "all" || filters.unit !== "all");
      const unitLabel = filters.unit === "unassigned" ? "Unassigned" : unitNames.get(filters.unit) ?? "";
      return (
        <>
          <div className="people-filter-heading">
            <div>
              <span className="eyebrow"><Filter size={13} aria-hidden="true" /> Workforce filters</span>
              <strong>Find the people you need</strong>
              <small>Search by identity, status or organization unit.</small>
            </div>
            <span className={hasFilters ? "people-filter-state active" : "people-filter-state"}>
              {hasFilters ? "Filters applied" : "All people"}
            </span>
          </div>
          <form method="get" className="people-filter-bar" role="search" aria-label="Filter people">
            <label className="people-filter-field people-filter-search">
              <span>Search people</span>
              <div className="people-filter-control">
                <Search size={16} aria-hidden="true" />
                <input type="search" name="q" defaultValue={filters.q} maxLength={160} placeholder="Name, email, employee number or title" />
              </div>
            </label>
            <label className="people-filter-field">
              <span>Status</span>
              <select name="status" defaultValue={filters.status}>
                <option value="all">All statuses</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </label>
            <label className="people-filter-field people-filter-unit">
              <span>Organization unit</span>
              <select name="unit" defaultValue={filters.unit}>
                <option value="all">All units</option>
                <option value="unassigned">Unassigned</option>
                {units.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
              </select>
            </label>
            <div className="people-filter-actions">
              <button type="submit" className="button people-apply-button">
                <Filter size={14} aria-hidden="true" />
                Apply filters
              </button>
              {hasFilters ? (
                <Link href="/dashboard/people" className="button people-clear-button">
                  <RotateCcw size={13} aria-hidden="true" />
                  Clear
                </Link>
              ) : (
                <button type="button" className="button people-clear-button disabled" disabled>
                  <RotateCcw size={13} aria-hidden="true" />
                  Clear
                </button>
              )}
            </div>
          </form>
          {hasFilters && <div className="people-active-filters" aria-label="Active filters">
            <span>Showing {result.total.toLocaleString()} matches</span>
            {filters.q && <b>Search: {filters.q}</b>}
            {filters.status !== "all" && <b>Status: {filters.status === "active" ? "Active" : "Inactive"}</b>}
            {unitLabel && filters.unit !== "all" && <b>Unit: {unitLabel}</b>}
          </div>}
          <div className="people-filter-result" role="status">
            <strong>{result.total.toLocaleString()}</strong>
            <span>matching of {result.tenant_total.toLocaleString()} people</span>
          </div>
        </>
      );
    })()}
    {result.items.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th scope="col">Person</th><th scope="col">Employee #</th><th scope="col">Job title</th><th scope="col">Organization unit</th><th scope="col">Status</th></tr></thead><tbody>{result.items.map(person =>
      <tr key={person.id}><td><Link className="text-link" href={`/dashboard/people/${person.id}`}>{person.first_name} {person.last_name}</Link><small>{person.email}</small></td><td>{person.employee_number || "—"}</td><td>{person.job_title || "—"}</td><td>{unitNames.get(person.org_unit_id ?? "") || "Unassigned"}</td><td><span className={`status-badge ${person.is_active ? "success" : "muted"}`}>{person.is_active ? "Active" : "Inactive"}</span></td></tr>
    )}</tbody></table></div> : <div className="empty-state"><UsersRound size={24} aria-hidden="true"/><p>{result.tenant_total ? result.total ? "This page has no results. Return to the first page." : "No people match these filters." : "No people have been added yet."}{result.total > 0 && <Link className="text-link" href={pageHref(1)}>First page</Link>}</p></div>}
    {result.total > 0 && <nav className="form-actions" aria-label="People pages">
      {result.page > 1 ? <Link className="button button-secondary" href={pageHref(result.page - 1)}>Previous</Link> : null}
      <span>Page {result.page} of {pages} · {result.total} matching</span>
      {result.page < pages ? <Link className="button button-secondary" href={pageHref(result.page + 1)}>Next</Link> : null}
    </nav>}
  </section>;
}
