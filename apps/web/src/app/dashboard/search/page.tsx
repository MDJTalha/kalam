import Link from "next/link";
import { Search, BookOpenCheck, UsersRound, Layers3, Route } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiJson, requireUser } from "@/lib/server-api";

type SearchResult = {
  query: string;
  courses: { id: string; title: string }[];
  people: { id: string; name: string; email: string }[];
  skills: { id: string; name: string }[];
  programs: { id: string; title: string }[];
};

export default async function SearchPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  await requireUser();
  const params = await searchParams;
  const query = params.q?.trim() || "";
  const results = query.length >= 2 ? await apiJson<SearchResult>("/api/v1/search?q=" + encodeURIComponent(query)) : null;

  return (
    <DashboardShell title="Global search" eyebrow="Cross-domain discovery">
      <div className="data-panel">
        <form className="search-form" method="get">
          <label htmlFor="q">Search courses, people, skills and programs</label>
          <div className="search-row"><input id="q" name="q" defaultValue={query} placeholder="e.g. ethics, manager, leadership" minLength={2} /><button className="button button-primary" type="submit"><Search size={16}/> Search</button></div>
        </form>
      </div>

      {!query ? <div className="data-panel"><div className="empty-state"><Search size={28}/><h2>Search the learning workspace</h2><p>Results respect the signed-in user&apos;s tenant and authorization boundary.</p></div></div> : null}

      {query && query.length < 2 && <div className="data-panel" role="status"><p>Enter at least two characters to search.</p></div>}
      {query.length >= 2 && results === null && <div className="data-panel" role="alert"><h2>Search unavailable</h2><p>Results could not be loaded. Try again later.</p></div>}
      {results && ![results.courses,results.people,results.skills,results.programs].some(items => items.length) && <div className="data-panel" role="status"><h2>No matching records</h2><p>Try another course, person, skill or program name.</p></div>}
      {results ? (
        <div className="module-grid">
          <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Courses</span><h2>{results.courses.length}</h2></div><BookOpenCheck size={20}/></div>{results.courses.map(item => <Link key={item.id} href={"/dashboard/catalog/" + item.id} className="compact-row"><div><strong>{item.title}</strong></div><span>→</span></Link>)}</section>
          <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">People</span><h2>{results.people.length}</h2></div><UsersRound size={20}/></div>{results.people.map(item => <Link key={item.id} href={"/dashboard/people/" + item.id} className="compact-row"><div><strong>{item.name}</strong><small>{item.email}</small></div><span>→</span></Link>)}</section>
          <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Skills</span><h2>{results.skills.length}</h2></div><Layers3 size={20}/></div>{results.skills.map(item => <Link key={item.id} href="/dashboard/skills" className="compact-row"><div><strong>{item.name}</strong></div><span>→</span></Link>)}</section>
          <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Programs</span><h2>{results.programs.length}</h2></div><Route size={20}/></div>{results.programs.map(item => <Link key={item.id} href={"/dashboard/programs/" + item.id} className="compact-row"><div><strong>{item.title}</strong></div><span>→</span></Link>)}</section>
        </div>
      ) : null}
    </DashboardShell>
  );
}
