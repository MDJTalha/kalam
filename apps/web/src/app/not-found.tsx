import Link from "next/link";
import { KalamBrand } from "@/components/kalam-brand";

export default function NotFound() {
  return (
    <main className="auth-shell">
      <section className="auth-brand">
        <KalamBrand dark compact className="brand-lockup" />
        <div className="auth-brand-copy">
          <span className="eyebrow">404 · Page not found</span>
          <h1>This page is not available.</h1>
          <p>The address may have changed, or you may not have a link to this page. Check the address or return to Kalam home.</p>
        </div>
      </section>
      <section className="auth-panel">
        <div className="auth-card">
          <div className="auth-card-heading">
            <span className="eyebrow">Continue</span>
            <h2>Find your way back</h2>
            <p>Use the home page to continue to the public experience or sign in to your organization.</p>
          </div>
          <Link className="button button-primary button-large submit-button" href="/">Return to Kalam home</Link>
        </div>
      </section>
    </main>
  );
}
