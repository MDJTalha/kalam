"use client";
import { RotateCcw } from "lucide-react";
import { KalamBrand } from "@/components/kalam-brand";

export default function DashboardError({reset}:{reset:()=>void}) {
  return <main className="auth-shell"><section className="auth-brand"><KalamBrand dark compact className="brand-lockup" /><div className="auth-brand-copy"><span className="eyebrow">Workspace error</span><h1>The learning workspace needs a refresh.</h1><p>The service returned an unexpected state. Your learning records are preserved; retry the workspace before taking further action.</p></div></section><section className="auth-panel"><div className="auth-card"><div className="auth-card-heading"><span className="eyebrow">Recovery</span><h2>Try again</h2><p>Retry the current screen and continue from the same tenant session.</p></div><button className="button button-primary button-large submit-button" onClick={()=>reset()}><RotateCcw size={16}/> Reload workspace</button></div></section></main>;
}
