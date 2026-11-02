"use client";

import { RefreshCw } from "lucide-react";
import Link from "next/link";
import { KalamBrand } from "@/components/kalam-brand";

export default function RootError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="auth-shell">
      <section className="auth-brand">
        <KalamBrand dark compact className="brand-lockup" />
        <div className="auth-brand-copy">
          <span className="eyebrow">Request interrupted</span>
          <h1>Kalam could not complete this request.</h1>
          <p>Your existing records have not been intentionally changed by this error. You can retry or return to the home page.</p>
        </div>
      </section>
      <section className="auth-panel">
        <div className="auth-card">
          <div className="auth-card-heading">
            <span className="eyebrow">Recovery</span>
            <h2>Choose your next step</h2>
            <p>Retry the current page. If the problem continues, contact your organization administrator.</p>
          </div>
          <button className="button button-primary button-large submit-button" onClick={() => reset()}>
            <RefreshCw size={16} aria-hidden="true" /> Try again
          </button>
          <Link className="button button-secondary button-large submit-button" href="/">Return to Kalam home</Link>
        </div>
      </section>
    </main>
  );
}
