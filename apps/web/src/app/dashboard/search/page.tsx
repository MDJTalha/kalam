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

      {results ? (
        <div className="module-grid">
          <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Courses</span><h2>{results.courses.length}</h2></div><BookOpenCheck size={20}/></div>{results.courses.map(item => <Link key={item.id} href={"/dashboard/catalog/" + item.id} className="compact-row"><div><strong>{item.title}</strong></div><span>→</span></Link>)}</section>
          <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">People</span><h2>{results.people.length}</h2></div><UsersRound size={20}/></div>{results.people.map(item => <div key={item.id} className="compact-row"><div><strong>{item.name}</strong><small>{item.email}</small></div></div>)}</section>
          <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Skills</span><h2>{results.skills.length}</h2></div><Layers3 size={20}/></div>{results.skills.map(item => <div key={item.id} className="compact-row"><div><strong>{item.name}</strong></div></div>)}</section>
          <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Programs</span><h2>{results.programs.length}</h2></div><Route size={20}/></div>{results.programs.map(item => <div key={item.id} className="compact-row"><div><strong>{item.title}</strong></div></div>)}</section>
        </div>
      ) : null}
    </DashboardShell>
  );
}
